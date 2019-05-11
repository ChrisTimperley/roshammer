# -*- coding: utf-8 -*-
__all__ = ('ROSHammer',)

from typing import Optional, Iterator
import contextlib
import logging

import attr
from docker.models.images import Image as DockerImage
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

    @contextlib.contextmanager
    def prepare(self, app: App) -> Iterator[App]:
        """Prepares a given ROS application for fuzzing.

        Yields
        ------
        App
            A description of the prepared ROS application.
        """
        rsw = self.roswire
        with rsw.launch(app.image, app.description) as sut:
            image: DockerImage = sut.container.persist()
            # TODO build with instrumentation
            catkin = sut.catkin(app.workspace)
            catkin.clean()
            catkin.build()
        try:
            prepared = attr.evolve(app, image=image.id)
            yield prepared
        finally:
            rsw.client_docker.images.remove(image.id, force=True)
