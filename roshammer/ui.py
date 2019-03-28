# -*- coding: utf-8 -*-
"""
This module provides a user interface for the CLI.
"""
__all__ = ('ROSHammerUI',)

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
    def __init__(self, image: str) -> None:
        self.terminal = blessed.Terminal()
        self.__image = image

    def _draw_header(self) -> str:
        t = self.terminal
        b = f" roshammer (v0.0.1) [{self.__image}] "  # TODO obtain version
        b = t.bold(t.center(b, fillchar='='))
        b += '\n'
        return b

    def _draw_stuff(self) -> None:
        nodes = [
            '/robot_state_publisher',
            '/map_server',
            '/move_base',
            '/acml'
        ]

        # draw node table
        w = 40
        rule = w * '.'
        top = '..' + 'nodes'.ljust(w - 2, '.')
        left = ': '
        right = ' :'
        iw = w - len(left) - len(right)

        print(rule)
        title = 'nodes'
        head = f"{left}{title: <{iw}}{right}"
        head = t.bold(head)
        print(head)
        print(rule)
        for node in sorted(nodes):
            print(f': {node: <{iw}} :')
        print(rule)

    def _draw(self) -> None:
        header = self._draw_header()
        return header

    def _refresh(self) -> None:
        # swap the contents of the buffer
        buffr = self._draw()
        print(self.terminal.clear(), end='')
        print(buffr)

    def run(self) -> None:
        # TODO implement refresh rate
        t = self.terminal
        with t.fullscreen(), t.hidden_cursor():
            while True:
                self._refresh()
                time.sleep(1)  
