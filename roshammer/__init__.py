# -*- coding: utf-8 -*-
"""
roshammer is a fuzzing and random input generation tool for ROS applications.
"""
__all__ = ('Fuzzer', 'FuzzTarget', 'Sanitiser')

from typing import Tuple, FrozenSet, Optional
from enum import Enum

import attr


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


@attr.s(frozen=True)
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


@attr.s(frozen=True)
class Fuzzer:
    """Fuzzes a specified ROS application using a given strategy.

    Attributes
    ----------
        target: FuzzTarget
            A description of the ROS application that is to be fuzzed.
        sanitisers: FrozenSet[Sanitiser]
            The set of sanitisers that should be used when fuzzing.
        num_workers: int
            The number of parallel worker processes that should be used when
            fuzzing.
        random_seed: int
            The seed that should be supplied to the random number generator.

    Raises
    ------
        ValueError: if number of workers is less than one.
    """
    target: FuzzTarget = attr.ib()
    sanitisers: FrozenSet[Sanitiser] = attr.ib(converter=frozenset,
                                               default=frozenset())
    num_workers: int = attr.ib(default=1)
    random_seed: int = attr.ib(default=0)

    @num_workers.validator
    def has_at_least_one_worker(self, attribute, num_workers) -> None:
        if num_workers < 1:
            raise ValueError('at least one worker must be used.')

    def fuzz(self) -> None:
        raise NotImplementedError

    run = fuzz
