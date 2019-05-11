#!/usr/bin/env python3
import logging

import roshammer
import roshammer.bag
import roshammer.search
import roshammer.detect
from roshammer import ROSHammer
from roshammer.bag import Bag
from roshammer.core import App


def main():
    log_to_stdout = logging.StreamHandler()
    log_to_stdout.setLevel(logging.DEBUG)
    logging.getLogger('roshammer').addHandler(log_to_stdout)
    logging.getLogger('roswire.proxy').addHandler(log_to_stdout)
    logging.getLogger('roswire.bag').addHandler(log_to_stdout)

    rsh = ROSHammer()
    roswire = rsh.roswire
    app = rsh.app('roswire/helloworld:buggy',
                  '/ros_ws',
                  '/ros_ws/src/ros_tutorials/roscpp_tutorials/launch/listener.launch')
    desc = app.description

    # load the seed bags
    seeds = [Bag.load(desc.types, 'bad.bag', ['/chatter'])]

    mutator = roshammer.bag.DropMessageMutator()
    launcher = roshammer.AppLauncher(app, roswire)
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
