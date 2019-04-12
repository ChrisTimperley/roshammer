# -*- coding: utf-8 -*-
"""
This module provides interfaces for executing fuzzing inputs.
"""
__all__ = ('InputExecutor', 'BagExecutor')

from typing import TypeVar, Generic

from .core import Bag

from roswire.proxy import ROSProxy

T = TypeVar('T')


class InputExecutor(Generic[T]):
    """Executes a given input on a provided app instance."""
    def __call__(self, ros: ROSProxy, inp: T) -> bool:
        raise NotImplementedError


class BagExecutor(InputExecutor[Bag]):
    """Executes a given bag on a provided app instance."""
