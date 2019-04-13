# -*- coding: utf-8 -*-
"""
This module provides functionality for fuzzing ROS bags.
"""
__all__ = ('Bag',)

from typing import Sequence, Iterator, Any

from roswire.definitions import TypeDatabase
from roswire.bag.core import BagMessage
from roswire.bag import BagWriter, BagReader

from .core import Input, Mutation, Mutator


class Bag(Sequence[BagMessage]):
    """Stores the contents of a ROS bag."""
    __slots__ = ('__contents', '__length')

    def __init__(self, contents: Sequence[BagMessage]) -> None:
        self.__contents = tuple(contents)
        self.__length = len(self.__contents)

    @classmethod
    def load(cls, db_type: TypeDatabase, fn: str) -> 'Bag':
        """Loads a bag from a given file."""
        reader = BagReader(fn, db_type)
        return Bag(reader)

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


class BagInput(Input[Bag]):
    """Represents a ROS bag fuzzing input."""


class BagMutation(Mutation[Bag]):
    """Represents a mutation to a bag file."""


class BagMutator(Mutator[Bag]):
    """Base class used by all bag mutators."""
