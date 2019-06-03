# -*- coding: utf-8 -*-
"""
The core module defines all of ROSHammer's basic data structures and
interfaces.
"""
__all__ = ('App',
           'AppContainer',
           'CoverageLevel',
           'Execution',
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
import collections.abc
import logging
import time
import os

import attr
from roswire import ROSWire
from roswire import System as ROSWireSystem
from roswire import SystemDescription as AppDescription
from roswire.proxy import ROSProxy as ROSWireROSProxy
from roswire.proxy import ShellProxy as ROSWireShellProxy
from roswire.proxy import FileProxy as ROSWireFileProxy
from roswire.util import Stopwatch

T = TypeVar('T')

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def validate_is_abs(obj, attr, value) -> None:
    """Raises an exception if a given value is not an absolute path."""
    if not os.path.isabs(value):
        raise ValueError('path is not absolute.')


class CoverageLevel(Enum):
    """Specifies a level of coverage."""
    DISABLED = 'disabled'
    EDGE = 'edge'
    LINE = 'line'
    BLOCK = 'block'
    FUNCTION = 'function'


class Coverage(FrozenSet[int], collections.abc.Set, ABC):
    """Provdes a concise coverage report for an execution."""


@attr.s(frozen=True, slots=True)
class App:
    """Provides a description of a ROS application under test.

    Attributes
    ----------
    image: str
        The original Docker image for the application.
    workspace: str
        The absolute path to the catkin workspace for the application.
    launch_filename: str
        The absolute path of the launch file, inside the container, that
        should be used to launch the application.
    launch_prefix: str, optional
        The prefix that should be used when launching the application, if any.
    description: AppDescription
        A description of the application, produced by ROSWire.

    Raises
    ------
    ValueError:
        if `launch_filename` is not an absolute path.
    ValueError:
        if `workspace` is not an absolute path.
    """
    image: str = attr.ib()
    workspace: str = attr.ib(validator=validate_is_abs)
    launch_filename: str = attr.ib(validator=validate_is_abs)
    launch_prefix: Optional[str] = attr.ib()
    description: AppDescription = attr.ib()

    @contextlib.contextmanager
    def provision(self, rsw: ROSWire) -> Iterator['AppContainer']:
        """Provisions a container for this application."""
        with rsw.launch(self.image, self.description) as sut:
            yield AppContainer(self, sut)


@attr.s(frozen=True, slots=True)
class AppContainer:
    """Provides access to a Docker container that hosts a ROS application."""
    app: App = attr.ib()
    _system: ROSWireSystem = attr.ib()

    @contextlib.contextmanager
    def launch(self) -> Iterator['AppInstance']:
        """Launches the application provided by this container.

        Yields
        ------
        AppInstance
            An instance of the application under test.
        """
        filename = self.app.launch_filename
        prefix = self.app.launch_prefix
        with self._system.roscore() as ros:
            ros.launch(filename, prefix=prefix)
            time.sleep(5)  # FIXME wait until nodes are launched
            yield AppInstance(self, ros)

    @property
    def files(self) -> ROSWireFileProxy:
        """Provides access to the file system for this container."""
        return self._system.files

    @property
    def shell(self) -> ROSWireShellProxy:
        """Provides access to a shell for this container."""
        return self._system.shell


@attr.s(frozen=True, slots=True)
class AppInstance:
    container: AppContainer = attr.ib()
    ros: ROSWireROSProxy = attr.ib()

    @property
    def app(self) -> App:
        return self.container.app

    @property
    def files(self) -> ROSWireFileProxy:
        """Provides access to the file system for this app instance."""
        return self.container.files

    @property
    def shell(self) -> ROSWireShellProxy:
        """Provides access to a shell for this app instance."""
        return self.container.shell


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
    def __call__(self,
                 app_instance: AppInstance,
                 has_failed: threading.Event,
                 inp: Input[T]
                 ) -> None:
        raise NotImplementedError


class InputGenerator(Iterator[Input[T]]):
    """Produces fuzzing inputs according to a given strategy."""


FailureDetectorFactory = Callable[[AppInstance, threading.Event],
                                  'FailureDetector']


class Failure:
    """Base class used to describe a failure of the application."""


class FailureDetector(contextlib.AbstractContextManager):
    """Abstract base class used by all failure detectors."""
    def __init__(self,
                 app_instance: AppInstance,
                 has_failed: threading.Event
                 ) -> None:
        self._app_instance = app_instance
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
class Execution:
    """Describes the outcome of a single fuzzing execution.

    Attributes
    ----------
    duration_secs: float
        The number of seconds taken to complete the execution.
    failures: frozenset of Failure
        The failures that were detected during the execution.
    coverage: Optional[Coverage]
        An optional coverage report for the execution.
    """
    duration_secs: float = attr.ib()
    failures: FrozenSet[Failure] = attr.ib(converter=frozenset)
    coverage: Optional[Coverage] = attr.ib()

    @property
    def failed(self) -> bool:
        """Returns true if a failure occurred during this execution."""
        return self.failures is not None


class Sanitiser(Enum):
    """Detect undesirable program behaviours via program transformations.

    Sanitisers are used to detect undesirable program behaviours (e.g., buffer
    overflows and memory leaks) by applying program transformations to the
    system under test at compile-time.
    """
    ASAN = 'asan'
    MSAN = 'msan'
    TSAN = 'tsan'
    UBSAN = 'ubsan'


@attr.s(frozen=True)
class ResourceLimits:
    """Describes the resource limits that should be placed on the search.

    Attributes
    ----------
    wall_clock_mins: float, optional
        The maximum length of wall-clock time that the fuzzing campaign should
        be allowed to run, given in minutes.
    num_inputs: int, optional
        The maximum number of inputs that may be evaluated.
    """
    wall_clock_mins = attr.ib(type=Optional[float], default=None)
    num_inputs = attr.ib(type=Optional[int], default=None)


@attr.s(frozen=True)
class ResourceUsage:
    """Describes the resources used by the fuzzer at a given moment in time.

    Attributes
    ----------
    wall_clock_mins: float
        The number of wall-clock minutes that the fuzzing campaign has lasted.
    num_inputs: int
        The number of unique inputs that have been evaluated.
    """
    wall_clock_mins = attr.ib(type=float, default=0.0)
    num_inputs = attr.ib(type=int, default=0)


@attr.s
class Fuzzer(Generic[T]):
    """Fuzzes a specified ROS application using a given strategy.

    Attributes
    ----------
    rsw: ROSWire
        A ROSWire instance.
    app: App
        An instrumented form of the application under test.
    inject: InputInjector[T]
        Used to inject fuzzing inputs into the application under test.
    inputs: InputGenerator[T]
        Produces a stream of fuzzing inputs.
    num_workers: int
        The number of parallel worker processes that should be used when
        fuzzing.
    resource_limits: ResourceLimits
        A description of the resource limits placed on the fuzzer.

    Raises
    ------
        ValueError: if number of workers is less than one.
    """
    rsw: ROSWire = attr.ib()
    app: App = attr.ib()
    inject: InputInjector[T] = attr.ib()
    inputs: InputGenerator[T] = attr.ib()
    detectors: List[FailureDetectorFactory] = attr.ib(converter=list)
    num_workers: int = attr.ib(default=1)
    resource_limits: ResourceLimits = attr.ib(default=ResourceLimits())
    _stopwatch: Stopwatch = attr.ib(default=Stopwatch())
    _num_executed_inputs: int = attr.ib(default=0)

    @property
    def resource_usage(self) -> ResourceUsage:
        """A summary of the resources used by this fuzzer."""
        return ResourceUsage(wall_clock_mins=self._stopwatch.duration / 60,
                             num_inputs=self._num_executed_inputs)

    @property
    def has_reached_resource_limits(self) -> bool:
        """Determines whether or not the fuzzer has hit its resource limit."""
        limits = self.resource_limits
        usage = self.resource_usage
        if limits.wall_clock_mins is not None:
            if usage.wall_clock_mins >= limits.wall_clock_mins:
                return True
        if limits.num_inputs is not None:
            if usage.num_inputs >= limits.num_inputs:
                return True
        return False

    @num_workers.validator
    def has_at_least_one_worker(self, attribute, num_workers) -> None:
        if num_workers < 1:
            raise ValueError('at least one worker must be used.')

    @detectors.validator
    def has_at_least_one_detector(self, attribute, detectors) -> None:
        if not detectors:
            raise ValueError('at least one failure detector must be used.')

    @contextlib.contextmanager
    def launch(self) -> Iterator[AppInstance]:
        with self.app.provision(self.rsw) as container:
            with container.launch() as inst:
                yield inst

    def execute(self, inp: Input[T]) -> Execution:
        """Spawns an instance of the app and fuzzes it with a given input.

        Parameters
        ----------
        inp: Input[T]
            An input to provide to the application under test.

        Returns
        -------
        Execution
            A summary of the execution.
        """
        # logger.info("fuzzing with input: %s", inp)
        with self.launch() as app:
            with contextlib.ExitStack() as stack:
                has_failed = threading.Event()
                detectors = []
                for factory in self.detectors:
                    detector = factory(app, has_failed)
                    logger.debug("enabling detector: %s", detector)
                    stack.enter_context(detector)
                    detectors.append(detector)

                # inject the input, block, wait for effects, and listen
                # for failure.
                stopwatch = Stopwatch()
                stopwatch.start()
                self.inject(app, has_failed, inp)
                time.sleep(15)  # TODO customise
                stopwatch.stop()

                # return a summary of the execution.
                duration = stopwatch.duration
                failures = [d.failure for d in detectors if d.failure]
                out = Execution(duration, failures, None)  # type: ignore
                logger.info("fuzzing outcome for input: %s", out)
                return out

            # TODO to collect coverage, we need to close the app binary.

    def fuzz(self) -> None:
        """Launches a fuzzing campaign using this fuzzing configuration."""
        logger.info("started fuzzing campaign")
        self._stopwatch.start()
        for inp in self.inputs:
            logger.info("fuzzing input #%d (running time: %.2f mins)",
                        self._num_executed_inputs,
                        self._stopwatch.duration / 60)
            if self.has_reached_resource_limits:
                logger.info("reached resource limits")
                break
            outcome = self.execute(inp)
            self._num_executed_inputs += 1
        self._stopwatch.stop()
        logger.info("finished fuzzing campaign")
