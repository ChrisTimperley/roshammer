# -*- coding: utf-8 -*-
"""
Provides a generic fuzzing framework for ROS applications.
"""
__all__ = ('Fuzzer',)

from typing import (Tuple, Set, FrozenSet, Optional, Iterator, Union, TypeVar,
                    Generic)
import os
import contextlib
import logging

import attr

from .core import FuzzTarget, Sanitiser, InputGenerator, AppLauncher

T = TypeVar('T')

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@attr.s(frozen=True)
class Fuzzer(Generic[T]):
    """Fuzzes a specified ROS application using a given strategy.

    Attributes
    ----------
        target: FuzzTarget
            A description of the ROS application that is to be fuzzed.
        seeds: FrozenSet[T]
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
    launcher: AppLauncher = attr.ib()
    inputs: InputGenerator[T] = attr.ib()
    sanitisers: FrozenSet[Sanitiser] = attr.ib(converter=frozenset,
                                               default=frozenset())
    num_workers: int = attr.ib(default=1)
    random_seed: int = attr.ib(default=0)

    @num_workers.validator
    def has_at_least_one_worker(self, attribute, num_workers) -> None:
        if num_workers < 1:
            raise ValueError('at least one worker must be used.')

    def fuzz(self) -> None:
        logger.info("started fuzz campaign")
        for inp in self.inputs:
            with self.launcher() as ros:
                # TODO inject input
                pass

    run = fuzz
