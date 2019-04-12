# -*- coding: utf-8 -*-
__all__ = ('Fuzzer',)

from typing import TypeVar

import attr
from roswire import SystemDescription

T = TypeVar('T')


@attr.s(slots=True)
class Fuzzer:
    """Fuzzes a ROS application according to a given fuzzing strategy.

    Attributes
    ----------
    system: SystemDescription
        A description of the system under test.
    inputs: InputGenerator
        Generates inputs that are used to fuzz the system under test.
    """
    system: SystemDescription
    inputs: InputGenerator[T]
    # we need a way of executing those inputs
    # termination conditions?

    def fuzz(self):
        return
