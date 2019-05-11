# -*- coding: utf-8 -*-
__all__ = ('ROSHammer',)

from typing import Optional

from roswire import ROSWire

from .core import App


class ROSHammer:
    def __init__(self, roswire: Optional[ROSWire] = None):
        if not roswire:
            roswire = ROSWire()
        self.__roswire: ROSWire = roswire

    @property
    def roswire(self) -> ROSWire:
        """The ROSWire session associated with this ROSHammer session."""
        return self.__roswire

    def app(self,
            image: str,
            workspace: str,
            launch_filename: str
            ) -> App:
        """Loads a ROS application.

        Parameters
        ----------
        image: str
            The name of the Docker image that provides the application.
        workspace: str
            The absolute path to the Catkin workspace inside the container.
        launch_filename: str
            The absolute path to the launch file for the application.
        """
        desc = self.roswire.descriptions.load_or_build(image)
        return App(image, workspace, launch_filename, desc)
