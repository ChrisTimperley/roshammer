#!/usr/bin/env python3
import logging

from roswire import ROSWire

import roshammer
import roshammer.bag
import roshammer.search
import roshammer.detect
from roshammer.bag import Bag


def main():
    log_to_stdout = logging.StreamHandler()
    log_to_stdout.setLevel(logging.DEBUG)
    logging.getLogger('roshammer').addHandler(log_to_stdout)
    logging.getLogger('roswire.proxy').addHandler(log_to_stdout)

    roswire = ROSWire()
    image = 'roswire/helloworld:buggy'
    desc = roswire.descriptions.load_or_build(image)

    # load the seed bags
    seeds = [Bag.load(desc.types, 'good.bag')]

    mutator = roshammer.bag.DropMessageMutator()
    launcher = roshammer.AppLauncher(
        image=image,
        description=desc,
        launch_filename='/ros_ws/src/ros_tutorials/roscpp_tutorials/launch/talker_listener.launch',
        roswire=roswire)
    inputs = roshammer.search.RandomInputGenerator(seeds, mutator)
    detector = roshammer.detect.NodeCrashDetector.factory(['listener'])
    injector = roshammer.bag.BagInjector()
    fuzzer = roshammer.Fuzzer(
        launcher=launcher,
        inject=injector,
        detectors=[detector],
        inputs=inputs)
    fuzzer.fuzz()


if __name__ == '__main__':
    main()
