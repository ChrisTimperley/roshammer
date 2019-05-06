# -*- coding: utf-8 -*-
"""
This module implements various failure detection monitors that are used to
dynasmically identify instances of failure within the application under test.
"""
__all__ = ('NodeCrashed', 'NodeCrashDetector')

from typing import Tuple, Iterator, FrozenSet, Collection, Callable
import time
import functools
import contextlib
import threading
import logging

import attr
from roswire.proxy import ShellProxy, ROSProxy

from .core import (AppInstance, Failure, FailureDetector,
                   FailureDetectorFactory)

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@attr.s(frozen=True)
class NodeCrashed(Failure):
    """Thrown when a monitored node has crashed."""
    node: str = attr.ib()


class NodeCrashDetector(FailureDetector):
    """Detects the abrupt termination of any one of a given set of nodes."""
    @classmethod
    def factory(cls, nodes: Collection[str]) -> FailureDetectorFactory:
        return functools.partial(cls, nodes=nodes)

    def __init__(self,
                 app: AppInstance,
                 ros: ROSProxy,
                 has_failed: threading.Event,
                 nodes: Collection[str]
                 ) -> None:
        self.__nodes = frozenset(nodes)
        super().__init__(app, ros, has_failed)

    def listen(self) -> None:
        logger.debug("listening for failures [%s]", self)

        shell = self._app.shell
        nodes = [self._ros.nodes[n] for n in self.__nodes]
        while self.running:
            for node in nodes:
                if not node.is_alive():
                    failure = NodeCrashed(node)
                    self._report_failure(failure)
                    return
            time.sleep(0.1)
