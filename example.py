#!/usr/bin/env python3
import logging

import roshammer
import roshammer.bag
import roshammer.search
import roshammer.detect
from roshammer import ROSHammer
from roshammer.bag import Bag
from roshammer.core import App, Sanitiser, CoverageLevel, ResourceLimits


def main():
    log_to_stdout = logging.StreamHandler()
    log_to_stdout.setLevel(logging.DEBUG)
    logging.getLogger('roshammer').addHandler(log_to_stdout)
    logging.getLogger('roswire').addHandler(log_to_stdout)
    # logging.getLogger('roswire.proxy').addHandler(log_to_stdout)
    # logging.getLogger('roswire.bag').addHandler(log_to_stdout)

    rsh = ROSHammer()
    roswire = rsh.roswire
    app = rsh.app('roswire/helloworld:buggy',
                  '/ros_ws',
                  '/ros_ws/src/ros_tutorials/roscpp_tutorials/launch/listener.launch')
    desc = app.description

    # load the seed bags
    seeds = [Bag.load(desc.types, 'bad.bag', ['/chatter'])]

    cov = CoverageLevel.FUNCTION
    sanitisers = [Sanitiser.ASAN]
    limits = ResourceLimits(wall_clock_mins=5, num_inputs=1)
    with rsh.prepare(app, cov, sanitisers) as prepared:
        mutator = roshammer.bag.DropMessageMutator()
        inputs = roshammer.search.RandomInputGenerator(seeds, mutator)
        detector = roshammer.detect.NodeCrashDetector.factory(['listener'])
        injector = roshammer.bag.BagInjector()
        fuzzer = roshammer.Fuzzer(
            rsw=roswire,
            app=prepared,
            inject=injector,
            detectors=[detector],
            resource_limits=limits,
            inputs=inputs)
        fuzzer.fuzz()


if __name__ == '__main__':
    main()
