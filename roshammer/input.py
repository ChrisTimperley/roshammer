# -*- coding: utf-8 -*-
"""
This module provides the data structures that describe fuzzing inputs.
"""
__all__ = ('Input', 'Bag', 'SeedBag', 'MutatedBag')

from typing import Generator
import os

import attr


class Input:
    """An input that can be provided to the system under test."""


class Bag(Input):
    """Represents a bag of messages that can be replayed."""


@attr.s(frozen=True)
class SeedBag(Bag):
    """Represents an original bag file that is physically stored on disk."""
    filename: str = attr.ib()

    @filename.validator
    def file_must_exist(self, attribute, filename) -> None:
        if not os.path.isfile(filename):
            raise ValueError('non-existent bag file provided.')


@attr.s(frozen=True)
class MutatedBag(Bag):
    """
    Represents a bag file whose contents are obtained by applying a
    sequence of mutations to a seed bag.
    """
    original: SeedBag = attr.ib()
    # TODO add mutations
