# -*- coding: utf-8 -*-
"""
This module provides functionality for fuzzing ROS bags.
"""
__all__ = ('Bag',)

from typing import Sequence, Iterator, Any, Optional, List, Iterable

from roswire.definitions import TypeDatabase
from roswire.bag.core import BagMessage
from roswire.bag import BagWriter, BagReader

from .core import Input, Mutation, Mutator


class Bag(Sequence[BagMessage]):
    """Stores the contents of a ROS bag."""
    __slots__ = ('__contents', '__length')

    def __init__(self, contents: Iterable[BagMessage]) -> None:
        self.__contents = tuple(contents)
        self.__length = len(self.__contents)

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
        writer.write(self.__contents)
        writer.close()

    def __len__(self) -> int:
        """Returns the number of messages in the bag."""
        return self.__length

    def __getitem__(self, index: Any) -> BagMessage:
        """Retrieves the bag message located at a given index."""
        assert isinstance(index, int)
        return self.__contents[index]

    def __iter__(self) -> Iterator[BagMessage]:
        """Returns an iterator over the contents of the bag."""
        yield from self.__contents

    def restrict_to_topic(self, topic: str) -> Bag:
        """Returns a variant of this bag that only represents a given topic."""
        return Bag(m for m in self.__contents if m.topic == topic)


class BagInput(Input[Bag]):
    """Represents a ROS bag fuzzing input."""


class BagMutation(Mutation[Bag]):
    """Represents a mutation to a bag file."""


class BagMutator(Mutator[Bag]):
    """Base class used by all bag mutators."""
