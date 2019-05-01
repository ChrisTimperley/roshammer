# -*- coding: utf-8 -*-
"""
This module implements a number of search-based fuzzing strategies.
"""
from typing import TypeVar, FrozenSet
import random

import attr

from .core import Input, InputGenerator, Mutator

T = TypeVar('T')


@attr.s
class RandomInputGenerator(InputGenerator[T]):
    """
    Generates a stream of random inputs using a pool of seed inputs and an
    input mutator.
    """
    seeds: FrozenSet[T] = attr.ib(converter=frozenset)
    mutator: Mutator[T] = attr.ib()

    @seeds.validator
    def check(self, attr, seeds: FrozenSet[T]) -> None:
        if not seeds:
            raise ValueError("at least one seed must be provided.")

    def __next__(self) -> Input[T]:
        seed: T = random.sample(self.seeds, 1)[0]
        inp: Input[T] = Input(seed)
        return self.mutator(inp)
