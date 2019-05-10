# -*- coding: utf-8 -*-
__all__ = ('ROSHammer',)

from typing import Optional

from roswire import ROSWire


class ROSHammer:
    def __init__(self, roswire: Optional[ROSWire] = None):
        if not roswire:
            roswire = ROSWire()
        self.__roswire: ROSWire = roswire

    @property
    def roswire(self) -> ROSWire:
        """The ROSWire session associated with this ROSHammer session."""
        return self.__roswire
