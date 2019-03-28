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
                 image: str,
                 *,
                 width: int = 120
                 ) -> None:
        self.terminal = blessed.Terminal()
        self.width = width
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
        header = t.bold(t.center(header, width=self.width, fillchar='='))
        p(header)

    def _draw_panel(self,
                    header: str,
                    contents: List[str],
                    *,
                    width: int = 59,
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
        # p(rule)
        for row in contents:
            p(f': {row: <{iw}} :')
        p(rule)

    def _draw_nodes(self) -> None:
        nodes = sorted([
            '/robot_state_publisher',
            '/map_server',
            '/move_base',
            '/acml'
        ])
        title = f'nodes [{len(nodes)}]'
        self._draw_panel(title, nodes)

    def _draw_services(self) -> None:
        services = [
            '/move_base/make_plan',
            '/move_base/clear_unknown_space',
            '/move_base/clear_costmaps'
        ]
        title = f'services [{len(services)}]'
        self._draw_panel(title, services, is_top=False)

    def _draw_actions(self) -> None:
        actions = [
            '/move_base'
        ]
        title = f'actions [{len(actions)}]'
        self._draw_panel(title, actions, is_top=False)

    def _draw(self) -> None:
        self._draw_header()
        self._draw_nodes()
        self._draw_services()
        self._draw_actions()

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
