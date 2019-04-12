# -*- coding: utf-8 -*-
__all__ = ('Fuzzer',)

from typing import TypeVar, Generic
import logging

import attr
from roswire import SystemDescription, ROSWire

from .input import InputGenerator

T = TypeVar('T')

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@attr.s(slots=True)
class Fuzzer(Generic[T]):
    """Fuzzes a ROS application according to a given fuzzing strategy.

    Attributes
    ----------
    roswire: ROSWire
        The ROSWire session for interacting with app instances.
    image: str
        The name of the Docker image that provides the ROS application.
    system: SystemDescription
        A description of the system under test.
    inputs: InputGenerator
        Generates inputs that are used to fuzz the system under test.
    """
    roswire: ROSWire
    image: str
    system: SystemDescription
    inputs: InputGenerator[T]
    # need an oracle for assessing inputs: InputChecker
    # we need a way of executing those inputs
    # termination conditions?

    def execute(self, inp: T) -> bool:
        with self.roswire.launch(self.image, self.system) as sut:
            pass

    def fuzz(self):
        for inp in inputs:
            if self.execute(inp):
                logger.info("found a crash! %s", inp)

    run = fuzz
