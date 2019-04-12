# -*- coding: utf-8 -*-
"""
This module provides the data structures that describe fuzzing inputs.
"""
__all__ = ('InputGenerator', 'CyclicGenerator')

from typing import Iterator, Generator, TypeVar, Sequence
import itertools

T = TypeVar('T')


class InputGenerator(Iterator[T]):
    """Produces a stream of inputs for fuzzing."""


class CyclicGenerator(InputGenerator[T]):
    """Produces a repeating stream of seed inputs."""
    def __init__(self, seeds: Sequence[T]) -> None:
        self.__stream: Iterator[T] = itertools.cycle(seeds)

    def __next__(self) -> T:
        return next(self.__stream)
