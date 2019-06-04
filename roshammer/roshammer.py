# -*- coding: utf-8 -*-
__all__ = ('ROSHammer',)

from typing import Optional, Iterator, Collection, List
import contextlib
import logging

import attr
from docker.models.images import Image as DockerImage
from roswire import ROSWire

from .core import App, Sanitiser, CoverageLevel

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
            launch_filename: str,
            launch_prefix: Optional[str] = None
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
        launch_prefix: str, optional
            An optional prefix to add before the roslaunch command.
        """
        desc = self.roswire.descriptions.load_or_build(image)
        return App(image, workspace, launch_filename, launch_prefix, desc)

    @contextlib.contextmanager
    def prepare(self,
                app: App,
                coverage: CoverageLevel = CoverageLevel.DISABLED,
                sanitisers: Optional[Collection[Sanitiser]] = None
                ) -> Iterator[App]:
        """Prepares a given ROS application for fuzzing.

        Yields
        ------
        App
            A description of the prepared ROS application.
        """
        logger.debug("preparing application: %s", app)
        if not sanitisers:
            sanitisers = []

        # determine the prefix for the application
        cov_opts = 'coverage=1:coverage_direct=1:coverage_dir=/tmp/cov'
        if coverage == CoverageLevel.DISABLED:
            prefix = ''
        elif Sanitiser.ASAN in sanitisers:
            prefix = f'ASAN_OPTIONS={cov_opts}'
        else:
            prefix = f'UBSAN_OPTIONS={cov_opts}'

        rsw = self.roswire
        with rsw.launch(app.image, app.description) as sut:
            cmake_args = ['-DCMAKE_CXX_COMPILER=clang++',
                          '-DCMAKE_C_COMPILER=clang',
                          '-DCMAKE_BUILD_TYPE=RelWithDebInfo']
            cxx_flags: List[str] = ['-g']

            # add sanitiser options
            fsan_opts: List[str] = []
            if Sanitiser.ASAN in sanitisers:
                fsan_opts += ['address']
            if Sanitiser.UBSAN in sanitisers:
                fsan_opts += ['undefined']
            if Sanitiser.MSAN in sanitisers:
                fsan_opts += ['memory']
            if Sanitiser.TSAN in sanitisers:
                fsan_opts += ['thread']
            if fsan_opts:
                cxx_flags += [f'-fsanitize={",".join(fsan_opts)}']

            # add coverage options
            if coverage == CoverageLevel.FUNCTION:
                cxx_flags += ['-fsanitize-coverage=func,trace-pc-guard']
            if coverage == CoverageLevel.EDGE:
                cxx_flags += ['-fsanitize-coverage=edge,trace-pc-guard']
            if coverage in (CoverageLevel.LINE, CoverageLevel.BLOCK):
                cxx_flags += ['-fsanitize-coverage=bb,trace-pc-guard']

            if cxx_flags:
                cmake_args += [f'-DCMAKE_CXX_FLAGS="{" ".join(cxx_flags)}"']

            catkin = sut.catkin(app.workspace)
            catkin.clean()
            catkin.build(cmake_args=cmake_args)

            # ensure that the coverage directory exists
            sut.files.mkdir('/tmp/cov')

            image: DockerImage = sut.container.persist()
        try:
            prepared = attr.evolve(app, image=image.id, launch_prefix=prefix)
            logger.debug("prepared application: %s -> %s", app, prepared)
            yield prepared
        finally:
            rsw.client_docker.images.remove(image.id, force=True)
