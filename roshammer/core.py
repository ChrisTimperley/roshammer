# -*- coding: utf-8 -*-
"""
The core module defines all of ROSHammer's basic data structures and
interfaces.
"""
__all__ = ('App',
           'AppInstance',
           'FuzzSeed',
           'Input',
           'Fuzzer',
           'Failure',
           'FailureDetector',
           'InputInjector',
           'Sanitiser',
           'InputGenerator')

from typing import (Union, Tuple, Sequence, Iterator, Any, Generic, TypeVar,
                    Generator, Collection, FrozenSet, ContextManager,
                    Callable, List, Optional)
from abc import ABC, abstractmethod
from enum import Enum
from functools import reduce
import threading
import contextlib
import logging
import time
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

    @property
    def value(self) -> T:
        """Obtains the concrete value for this input."""
        return reduce(lambda s, m: m(s), self.mutations, self.seed)

    def mutate(self, mutation: Mutation[T]) -> 'Input[T]':
        """Applies a given mutation to this input to produce a new input."""
        return attr.evolve(self, mutations=self.mutations + (mutation,))


class Mutator(Generic[T]):
    """Used to mutate given inputs according to a given strategy."""
    def __call__(self, inp: Input[T]) -> Input[T]:
        raise NotImplementedError


class InputInjector(Generic[T]):
    """Injects a given input into the application under test."""
    def __call__(self, ros: ROSProxy, inp: Input[T]) -> None:
        raise NotImplementedError


class InputGenerator(Iterator[Input[T]]):
    """Produces fuzzing inputs according to a given strategy."""


FailureDetectorFactory = Callable[[AppInstance, ROSProxy, threading.Event],
                                  'FailureDetector']


class Failure:
    """Base class used to describe a failure of the application."""


class FailureDetector(contextlib.AbstractContextManager):
    """Abstract base class used by all failure detectors."""
    def __init__(self,
                 app: AppInstance,
                 ros: ROSProxy,
                 has_failed: threading.Event
                 ) -> None:
        self._app = app
        self._ros = ros
        self._has_failed = has_failed
        self.__failure: Optional[Failure] = None
        self.__running = False
        self.__listener = threading.Thread(target=self.listen)

    @property
    def failure(self) -> Optional[Failure]:
        """A description of the failure, if any, caught by this detector."""
        return self.__failure

    @property
    def running(self) -> bool:
        """Returns true if this failure detector is running."""
        return self.__running

    @abstractmethod
    def listen(self) -> None:
        """Blocks and listens for failure."""
        raise NotImplementedError

    def start(self) -> None:
        """Starts listening for failures."""
        logger.debug("starting failure detector: %s", self)
        self.__running = True
        self.__listener.start()

    def stop(self) -> None:
        """Stops listening for failures."""
        logger.debug("stopping failure detector: %s", self)
        self.__running = False
        self.__listener.join()

    def _report_failure(self, failure: Failure) -> None:
        """Used to record a failure that was caught by this detector."""
        logger.debug("ERROR REPORTED")
        self.__failure = failure
        self._has_failed.set()

    def __enter__(self) -> 'FailureDetector':
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


@attr.s(frozen=True, slots=True)
class AppLauncher:
    """Responsible for launching instances of the app under test."""
    image: str = attr.ib()
    description: App = attr.ib()
    launch_filename: str = attr.ib()
    _roswire: ROSWire = attr.ib()

    @contextlib.contextmanager
    def launch(self) -> Iterator[Tuple[AppInstance, ROSProxy]]:
        with self._roswire.launch(self.image, self.description) as sut:
            with sut.roscore() as ros:
                ros.launch(self.launch_filename)
                time.sleep(5)  # FIXME wait until nodes are launched
                yield sut, ros

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


@attr.s
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
    detectors: List[FailureDetectorFactory] = attr.ib(converter=list)
    num_workers: int = attr.ib(default=1)

    @num_workers.validator
    def has_at_least_one_worker(self, attribute, num_workers) -> None:
        if num_workers < 1:
            raise ValueError('at least one worker must be used.')

    @detectors.validator
    def has_at_least_one_detector(self, attribute, detectors) -> None:
        if not detectors:
            raise ValueError('at least one failure detector must be used.')

    def fuzz_with_input(self, inp: Input[T]) -> None:
        """Spawns an instance of the app and fuzzes it with a given input."""
        logger.info("fuzzing with input: %s", inp)
        with self.launcher() as (app, ros):
            with contextlib.ExitStack() as stack:
                has_failed = threading.Event()
                detectors = []
                for factory in self.detectors:
                    detector = factory(app, ros, has_failed)
                    logger.debug("enabling detector: %s", detector)
                    stack.enter_context(detector)
                    detectors.append(detector)

                # inject the input, block, wait for effects, and listen
                # for failure.
                self.inject(ros, inp)
                time.sleep(15)  # TODO customise

                if has_failed:
                    logger.info("CRASHING INPUT FOUND")
                    failures = [d.failure for d in detectors if d.failure]
                    logger.info("FAILURES: %s", failures)

    def fuzz(self) -> None:
        """Launches a fuzzing campaign using this fuzzing configuration."""
        logger.info("started fuzzing campaign")
        inp = next(self.inputs)
        self.fuzz_with_input(inp)
        logger.info("finished fuzzing campaign")
