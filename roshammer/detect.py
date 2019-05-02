# -*- coding: utf-8 -*-
"""
This module implements various failure detection monitors that are used to
dynasmically identify instances of failure within the application under test.
"""
__all__ = ('NodeCrashed', 'NodeCrashDetector')

from typing import Tuple, Iterator, FrozenSet, Collection, Callable
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
    pid: int = attr.ib()


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
        node_to_pid = {n: self._ros.nodes[n].pid for n in self.__nodes}
        logger.debug("monitoring PIDs: %s", list(node_to_pid.values()))
        while self.running:
            for node, pid in node_to_pid.items():
                retcode = shell.execute(f'kill -0 {pid}')[0]
                if retcode != 0:
                    failure = NodeCrashed(node, pid)
                    self._report_failure(failure)
                    return
