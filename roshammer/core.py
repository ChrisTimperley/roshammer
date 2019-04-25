# -*- coding: utf-8 -*-
"""
The core module defines all of ROSHammer's basic data structures and
interfaces.
"""
__all__ = ('App', 'AppInstance', 'FuzzSeed', 'Input', 'Fuzzer',
           'InputInjector', 'Sanitiser', 'InputGenerator')

from typing import (Union, Tuple, Sequence, Iterator, Any, Generic, TypeVar,
                    Generator)
from enum import Enum
import contextlib
import logging
import os

import attr
from roswire import ROSWire
from roswire import System as AppInstance
from roswire import SystemDescription as App
from roswire.proxy import ROSProxy

T = TypeVar('T')

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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


class InputInjector(Generic[T]):
    """Injects a given input into the application under test."""
    def __call__(self, ros: ROSProxy, inp: Input[T]) -> None:
        raise NotImplementedError


class InputGenerator(Generator[Input[T], None, None]):
    """Produces fuzzing inputs according to a given strategy."""


@attr.s(frozen=True, slots=True)
class AppLauncher:
    """Responsible for launching instances of the app under test."""
    image: str = attr.ib()
    description: App = attr.ib()
    _roswire: ROSWire = attr.ib()

    @contextlib.contextmanager
    def launch(self) -> Iterator[ROSProxy]:
        with self._roswire.launch(self.image, self.description) as sut:
            with sut.ros() as ros:
                yield ros

    __call__ = launch


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
class Fuzzer(Generic[T]):
    """Fuzzes a specified ROS application using a given strategy.

    Attributes
    ----------
    launcher: AppLauncher
        Launches instances of the application under test.
    inject: InputInjector[T]
        Used to inject fuzzing inputs into the application under test.
    inputs: InputGenerator[T]
        Produces a stream of fuzzing inputs.
    num_workers: int
        The number of parallel worker processes that should be used when
        fuzzing.

    Raises
    ------
        ValueError: if number of workers is less than one.
    """
    launcher: AppLauncher = attr.ib()
    inject: InputInjector[T] = attr.ib()
    inputs: InputGenerator[T] = attr.ib()
    num_workers: int = attr.ib(default=1)

    @num_workers.validator
    def has_at_least_one_worker(self, attribute, num_workers) -> None:
        if num_workers < 1:
            raise ValueError('at least one worker must be used.')

    def fuzz(self) -> None:
        logger.info("started fuzz campaign")
        for inp in self.inputs:
            with self.launcher() as ros:
                # TODO should we block?
                self.inject(ros, inp)
