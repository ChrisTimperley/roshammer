__all__ = ('Fuzzer',)

from typing import Optional


class Fuzzer:
    def __init__(self) -> None:
        pass

    def run_one(self, bag: Bag) -> bool:
        # TODO: use a nice context manager to prevent resource leaks
        # replay the provided bag
        # listen for crashes on a separate thread
        # impose a time limit
        ros.playback(fn_bag, block=True)

        # TODO: compute amount of time taken to replay bag
        # TODO: add additional time to end of test for messages to have effect
        # loop for N seconds

        return True

    def fuzz(self,
             image: str,
             dir_seeds: str,   # replace with actual seeds
             target_node: Optional[str] = None,
             ) -> None:
        # instrument the image
        # - rebuild image with appropriate instrumentation flags (e.g., `--asan`, `--coverage`).
        #   - need to tweak instrumentation options according to detectors.
        # - do we only want to rebuild with instrumentation for SOME packages?

        # analyse the image
        # - what topics/services/parameters does the target node use? used to slice the bag files.

        # prepare the seeds
        # - extract relevant parts of bag file (save sliced bags to a new, temporary directory).

        # generate a sequence of bag files
        # - keep evaluating bag files until termination criteria is satisfied
        # - evaluate in parallel! use separate processes? minimise shared state.

        # options:
        # - processpool: stupid processes can keep running (creates rogue processes) [probably best]
        # - asyncio

        # triage is a thing
        pass
