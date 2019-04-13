# -*- coding: utf-8 -*-
"""
The core module defines all of ROSHammer's basic data structures and
interfaces.
"""
__all__ = ('App', 'AppInstance', 'FuzzSeed', 'Input', 'FuzzTarget',
           'Sanitiser')

from typing import (Union, Tuple, Sequence, Iterator, Any, Generic, TypeVar)
from enum import Enum
import os

import attr
from roswire import System as App
from roswire import SystemDescription as AppInstance
from roswire.proxy import ROSProxy

T = TypeVar('T')


class Mutation(Generic[T]):
    """Represents a mutation to an input."""
    def __call__(self, inp: T) -> T:
        raise NotImplementedError


# NOTE cannot use slots=True (https://github.com/python-attrs/attrs/issues/313)
@attr.s(frozen=True)
class Input(Generic[T]):
    """Represents a (generated) fuzzing input."""
    seed: T = attr.ib()
    mutations: Tuple[Mutation[T], ...] = attr.ib(default=tuple())


class Mutator(Generic[T]):
    """Used to mutate given inputs according to a given strategy."""
    def __call__(self, inp: Input[T]) -> Input[T]:
        raise NotImplementedError


class InputExecutor(Generic[T]):
    """Executes a given input on a provided ROS Master."""
    def __call__(self, ros: ROSProxy, inp: T) -> bool:
        raise NotImplementedError


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
