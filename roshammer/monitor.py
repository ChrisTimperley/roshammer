__all__ = ('ProcessExited', 'ProcessMonitor')

from typing import Tuple
from contextlib import AbstractContextManager
import threading

import attr
from roswire.proxy import ShellProxy


class ProcessExited(Exception):
    """Thrown when a monitored process has exited."""


@attr.s
class ProcessMonitor(AbstractContextManager):
    """Used to monitor a given set of processes within a shell.

    Raises
    ------
    ProcessExited:
        if one of the monitored processes has exited.
    """
    _shell = attr.ib(type=ShellProxy)
    _pids = attr.ib(type=Tuple[int, ...], converter=tuple)
    _running = attr.ib(type=bool, default=False)

    def check(self) -> bool:
        """Checks whether any monitored process has exited."""
        for pid in self._pids:
            retcode = self._shell.execute(f'kill -0 {pid}')[0]
            if retcode != 0:
                return False
        return True

    def _monitor(self) -> None:
        """Blocks indefinitely until a monitored process exits.

        Raises
        ------
        ProcessExited:
            when a monitored process has exited.
        """
        while self._running:
            if not self.check():
                raise ProcessExited

    def __enter__(self) -> 'ProcessMonitor':
        """Begins monitoring the processes."""
        self._running = True
        self.__thread = threading.Thread(target=self._monitor)
        self.__thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stops monitoring the processes."""
        self._running = False
        self.__thread.join()
