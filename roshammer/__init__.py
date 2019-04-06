# -*- coding: utf-8 -*-
"""
roshammer is a fuzzing and random input generation tool for ROS applications.
"""
__all__ = ('Fuzzer', 'FuzzSeed', 'FuzzInput', 'FuzzTarget', 'Sanitiser')

from typing import Tuple, Set, FrozenSet, Optional, Iterator, Union
from enum import Enum
import os
import contextlib
import logging

import attr

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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


@attr.s(frozen=True)
class Fuzzer:
    """Fuzzes a specified ROS application using a given strategy.

    Attributes
    ----------
        target: FuzzTarget
            A description of the ROS application that is to be fuzzed.
        seeds: FrozenSet[FuzzSeed]
            The set of seeds that should be used when fuzzing.
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
    seeds: FrozenSet[FuzzSeed] = attr.ib(converter=frozenset)
    sanitisers: FrozenSet[Sanitiser] = attr.ib(converter=frozenset,
                                               default=frozenset())
    num_workers: int = attr.ib(default=1)
    random_seed: int = attr.ib(default=0)

    @num_workers.validator
    def has_at_least_one_worker(self, attribute, num_workers) -> None:
        if num_workers < 1:
            raise ValueError('at least one worker must be used.')

    @num_workers.validator
    def has_at_least_one_seed(self, attribute, seeds) -> None:
        if not seeds:
            raise ValueError('at least one fuzzing seed must be provided.')

    @contextlib.contextmanager
    def instrument(self) -> Iterator[str]:
        """Instruments the Docker image for the application under test.

        Upon exiting the context, the instrumented Docker image will be
        destroyed.

        Yields
        ------
        str
            The name of the instrumented Docker image.
        """
        image_original = self.target.image
        logger.info("instrumenting Docker image [%s]", image_original)

        raise NotImplementedError

        image_instrumented = "TODO"
        logger.info("instrumented Docker image [%s]: saved to %s",
                    image_original,
                    image_instrumented)

    def _prepare_seeds(self) -> Set[FuzzSeed]:
        """Prepares the input seeds for fuzzing.

        Note
        ----
            For now, this method maintains the original input seeds.
        """
        logger.info("preparing seeds")
        seeds = set(self.seeds)

        # - filtering: remove all messages on non-target topics
        # - selection

        logger.info("prepared seeds")
        return seeds

    def fuzz(self) -> None:
        logger.info("started fuzz campaign")
        seeds = self._prepare_seeds()
        with self.instrument() as image:
            raise NotImplementedError
        logger.info("finished fuzz campaign")

    run = fuzz
