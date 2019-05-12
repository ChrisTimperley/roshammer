# -*- coding: utf-8 -*-
"""
This module provides functionality for fuzzing ROS bags.
"""
__all__ = ('Bag', 'BagInjector')

from typing import Sequence, Iterator, Any, Optional, List, Iterable, Tuple
import os
import time
import bisect
import random
import tempfile
import logging
import threading

import attr
from roswire.definitions import TypeDatabase, Message
from roswire.bag.core import BagMessage
from roswire.bag import BagWriter, BagReader

from .core import Input, InputInjector, Mutation, Mutator, AppInstance

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@attr.s(frozen=True, slots=True)
class Bag(Sequence[BagMessage]):
    """
    Stores the contents of a ROS bag as a sequence of messages, ordered by
    their timestamps.

    Note that all bag operations (e.g., message deletion, replacement,
    insertion, swapping) maintain the message ordering invariant: the messages
    within the bag are chronologically by their timestamps, from earliest to
    latest.
    """
    _contents: Tuple[BagMessage, ...] = attr.ib(converter=tuple)

    @classmethod
    def load(cls,
             db_type: TypeDatabase,
             fn: str,
             topics: Optional[List[str]] = None
             ) -> 'Bag':
        """Loads a bag from a given file.

        Arguments
        ---------
        db_type: TypeDatabase
            The type database for the system under test.
        fn: str
            The path to the bag file.
        topics: Optional[List[str]]
            An optional list of topics to which the bag should be restricted.
        """
        reader = BagReader(fn, db_type)
        return Bag(reader.read_messages(topics))

    def save(self, fn: str) -> None:
        """Saves the contents of the bag to a given file on disk."""
        writer = BagWriter(fn)
        writer.write(self)
        writer.close()

    def __len__(self) -> int:
        """Returns the number of messages in the bag."""
        return len(self._contents)

    def __getitem__(self, index: Any) -> BagMessage:
        """Retrieves the bag message located at a given index."""
        assert type(index) in [slice, int]
        return self._contents[index]

    def __iter__(self) -> Iterator[BagMessage]:
        """Returns an iterator over the contents of the bag."""
        yield from self._contents

    def delete(self, index: int) -> 'Bag':
        """
        Returns a variant of this bag that does not contain a given message,
        specified by its index.

        Raises
        ------
        IndexError
            if the bag does not contain an entry at the given index.
        """
        if index >= len(self):
            raise IndexError
        return Bag(self[:index] + self[index+1:])

    def insert(self, message: BagMessage) -> 'Bag':
        """Returns a variant of this bag that contains a given message."""
        i = bisect.bisect(self._contents, message)
        return Bag(self[:i] + (message,) + self[i:])

    def replace(self, index: int, replacement: BagMessage) -> 'Bag':
        """
        Returns a variant of this bag where a given message is replaced by
        another.
        """
        return self.delete(index).insert(replacement)

    def swap(self, i: int, j: int) -> 'Bag':
        """
        Returns a variant of this bag where the position and timestamps of two
        messages, given by their indices, are switched.
        """
        i, j = sorted((i, j))
        mi = self[i]
        mj = self[j]
        mi, mj = (attr.evolve(mi, time=mj.time), attr.evolve(mj, time=mi.time))
        return Bag(self[:i] + (mj,) + self[i + 1:j] + (mi,) + self[j + 1:])

    def restrict_to_topic(self, topic: str) -> 'Bag':
        """Returns a variant of this bag that only represents a given topic."""
        return Bag(m for m in self if m.topic == topic)


class BagMutation(Mutation[Bag]):
    """Represents a mutation to a bag file."""


@attr.s(frozen=True, slots=True)
class DropMessage(BagMutation):
    """Drops a given message from the bag."""
    index: int = attr.ib()

    def __call__(self, bag: Bag) -> Bag:
        return bag.delete(self.index)


class DropMessageMutator(Mutator[Bag]):
    """Applies drop message mutations to its inputs."""
    def __call__(self, inp: Input[Bag]) -> Input[Bag]:
        bag = inp.value
        index = random.randint(0, len(bag) - 1)
        return inp.mutate(DropMessage(index))


@attr.s(frozen=True, slots=True)
class DelayMessage(BagMutation):
    """Delays a given message by a fixed period of time."""
    index: int = attr.ib()
    secs: int = attr.ib()

    def __call__(self, bag: Bag) -> Bag:
        msg = attr.evolve(bag[self.index], time=msg.time + self.secs)
        return bag.replace(self.index, msg)


@attr.s(frozen=True, slots=True)
class SwapMessage(BagMutation):
    """Swaps the position of two messages in the bag."""
    index_a: int = attr.ib()
    index_b: int = attr.ib()

    def __call__(self, bag: Bag) -> Bag:
        return bag.swap(self.index_a, self.index_b)


@attr.s(frozen=True, slots=True)
class ReplaceMessage(BagMutation):
    """Replaces a given message in the bag with another."""
    index: int = attr.ib()
    replacement: BagMessage = attr.ib()

    def __call__(self, bag: Bag) -> Bag:
        return bag.replace(self.index, self.replacement)


@attr.s(frozen=True, slots=True)
class InsertMessage(BagMutation):
    """Inserts a given message into the bag."""
    message: BagMessage = attr.ib()

    def __call__(self, bag: Bag) -> Bag:
        return bag.insert(self.message)


@attr.s(frozen=True, slots=True)
class ReplaceMessageData(BagMutation):
    """Replaces message data but retains topic and timestamp information."""
    index: int = attr.ib()
    replacement: Message = attr.ib()

    def __call__(self, bag: Bag) -> Bag:
        msg = attr.evolve(bag[self.index], message=self.replacement)
        return bag.replace(self.index, msg)


class BagInjector(InputInjector[Bag]):
    """Used to inject messages from a ROSBag onto a given ROS session."""
    def __call__(self,
                 app_instance: AppInstance,
                 has_failed: threading.Event,
                 inp: Input[Bag]
                 ) -> None:
        ros = app_instance.ros
        bag = inp.value
        _, fn_bag = tempfile.mkstemp()
        logger.debug("created temporary file for bag: %s", fn_bag)
        try:
            bag.save(fn_bag)
            with ros.playback(fn_bag) as player:
                while not has_failed.is_set() and not player.finished():
                    time.sleep(0.1)
        finally:
            os.remove(fn_bag)
