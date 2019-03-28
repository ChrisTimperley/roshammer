# -*- coding: utf-8 -*-
"""
This module provides a user interface for the CLI.
"""
__all__ = ('ROSHammerUI',)

from typing import List, Optional, Tuple, Sequence
import io
import time

import attr
import blessed


@attr.s
class Pane:
    title = attr.ib(type=Optional[str])
    contents = attr.ib(type=Sequence[str])

    def render(self,
               t: blessed.Terminal,
               *,
               width: int = 80,
               border_top: bool = True,
               border_bottom: bool = True,
               border_left: bool = True,
               border_right: bool = True
               ) -> List[str]:
        """Renders the contents of the pane to a list of lines."""
        lines: List[str] = []

        rule = width * '.'
        left = ': ' if border_left else ' '
        right = ' :' if border_right else ' '
        iw = width - len(left) - len(right)

        if border_top:
            lines.append(rule)

        if self.title:
            header = t.bold(self.title.ljust(iw))
            header = f"{left}{header}{right}"
            lines.append(header)

        lines += [f'{left}{l: <{iw}}{right}' for l in self.contents]
        if border_bottom:
            lines.append(rule)

        return lines


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
        self._build_static_panes()

    def _build_static_panes(self) -> None:
        """Constructs and stores each of the static panes."""
        # TODO fetch
        nodes = sorted([
            '/robot_state_publisher',
            '/map_server',
            '/move_base',
            '/acml'
        ])
        title = f'nodes [{len(nodes)}]'
        self.__pane_nodes = Pane(title, nodes)

        # TODO fetch
        services = sorted([
            '/move_base/make_plan',
            '/move_base/clear_unknown_space',
            '/move_base/clear_costmaps'
        ])
        title = f'services [{len(services)}]'
        self.__pane_services = Pane(title, services)

        # TODO fetch
        actions = sorted([
            '/move_base'
        ])
        title = f'actions [{len(actions)}]'
        self.__pane_actions = Pane(title, actions)

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

    def _draw(self) -> None:
        t = self.terminal
        self._draw_header()
        self._print('\n'.join(self.__pane_nodes.render(t)))

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
