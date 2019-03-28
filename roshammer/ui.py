# -*- coding: utf-8 -*-
"""
This module provides a user interface for the CLI.
"""
__all__ = ('ROSHammerUI',)

from typing import List
import io
import time

import blessed



class ROSHammerUI:
    """Provides a terminal-based user interface.
    Note
    ----

        Right now, the implementation for this UI isn't particularly
        efficient: string operations are quite poor (e.g., creating
        new strings via += rather than writing to a buffer). A better
        solution is to write to an output stream and/or construct a
        template upon creation of the UI object and to complete that
        template at every _draw call.
    """
    def __init__(self,
                 image: str
                 ) -> None:
        self.terminal = blessed.Terminal()
        self.__image = image
        self.__frame_buffer = io.StringIO()

    def _print(self, m: str, end: str = '\n') -> None:
        """Prints a string to the frame buffer."""
        print(m, end=end, file=self.__frame_buffer)

    def _draw_header(self) -> str:
        p = self._print
        t = self.terminal
        # TODO obtain version
        header = f" roshammer (v0.0.1) [{self.__image}] "
        header = t.bold(t.center(header, fillchar='='))
        p(header)

    def _draw_panel(self,
                    header: str,
                    contents: List[str],
                    *,
                    width: int = 80,
                    is_top: bool = True
                    ) -> None:
        p = self._print
        t = self.terminal

        rule = width * '.'
        top = '..' + header.ljust(width - 2, '.')
        left = ': '
        right = ' :'
        iw = width - 4

        header = t.bold(header.ljust(iw))
        header = f"{left}{header}{right}"

        if is_top:
            p(rule)
        p(header)
        p(rule)
        for row in contents:
            p(f': {row: <{iw}} :')
        p(rule)

    def _draw(self) -> None:
        self._draw_header()

        nodes = [
            '/robot_state_publisher',
            '/map_server',
            '/move_base',
            '/acml'
        ]
        self._draw_panel('nodes', nodes)

        services = [
            '/move_base/make_plan',
            '/move_base/clear_unknown_space',
            '/move_base/clear_costmaps'
        ]
        self._draw_panel('services', services, is_top=False)

        actions = [
            '/move_base'
        ]
        self._draw_panel('actions', actions, is_top=False)

    def _refresh(self) -> None:
        # write to frame buffer and swap
        self._draw()
        print(self.terminal.clear(), end='')
        print(self.__frame_buffer.getvalue(), end='')
        self.__frame_buffer.close()
        self.__frame_buffer = io.StringIO()

    def run(self) -> None:
        # TODO implement refresh rate
        t = self.terminal
        with t.fullscreen(), t.hidden_cursor():
            while True:
                self._refresh()
                time.sleep(1)  
