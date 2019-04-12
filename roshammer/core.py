# -*- coding: utf-8 -*-
"""
The core module provides all of ROSHammer's basic data structures.
"""
__all__ = ('App', 'AppInstance', 'FuzzSeed', 'FuzzInput', 'FuzzTarget',
           'Sanitiser', 'Bag')

from typing import Union, Tuple, Sequence, Iterator, Any
from enum import Enum
import os

import attr
from roswire import System as App
from roswire import SystemDescription as AppInstance
from roswire.definitions import TypeDatabase
from roswire.bag.core import BagMessage
from roswire.bag import BagWriter, BagReader


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


class Sanitiser(Enum):
    """Detect undesirable program behaviours via program transformations.

    Sanitisers are used to detect undesirable program behaviours (e.g., buffer
    overflows and memory leaks) by applying program transformations to the
    system under test at compile-time.
    """
    ASan = 'asan'
    MSan = 'msan'
    TSan = 'tsan'
    UBSan = 'ubsan'


@attr.s(frozen=True, slots=True)
class FuzzTarget:
    """Provides a description of the ROS application under test.

    Attributes
    ----------
        image: str
            The name of the Docker image for the ROS application.
        launch_filepath: str
            The filepath within the container to the launch file that should
            be used to launch the application under test.
        nodes: Tuple[str, ...]
            The names of the nodes that should be fuzzed.
        topics: Tuple[str, ...]
            The names of the topics that should be fuzzed.

    Raises
    ------
        ValueError: if no nodes are specified.
        ValueError: if no topics are specified.
    """
    image: str = attr.ib()
    launch_filepath: str = attr.ib()
    nodes: Tuple[str, ...] = attr.ib(converter=tuple)
    topics: Tuple[str, ...] = attr.ib(converter=tuple)

    @nodes.validator
    def has_at_least_one_node(self, attribute, nodes) -> None:
        if not nodes:
            raise ValueError('at least one node must be specified.')

    @topics.validator
    def has_at_least_one_topic(self, attribute, topics) -> None:
        if not topics:
            raise ValueError('at least one topic must be specified.')
