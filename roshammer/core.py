# -*- coding: utf-8 -*-
"""
The core module provides all of ROSHammer's basic data structures.
"""
__all__ = ('FuzzSeed', 'FuzzInput', 'FuzzTarget', 'Sanitiser')

from typing import Union, Tuple
from enum import Enum
import os

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
class FuzzSeed:
    """Describes a fuzzing seed (i.e., a bag file)."""
    bag_file: str = attr.ib()

    @bag_file.validator
    def bag_file_must_exist(self, attribute, filename) -> None:
        if not os.path.isfile(filename):
            raise ValueError('non-existent bag file provided.')


FuzzInput = Union[FuzzSeed]


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
