import pytest

from roshammer import FuzzTarget


def test_constructor():
    t = FuzzTarget(image="hello-world",
                   launch_filepath="/foo/bar",
                   nodes=["node-one"],
                   topics=["topic-a"])

    with pytest.raises(ValueError):
        FuzzTarget(image="hello-world",
                   launch_filepath="/foo/bar",
                   nodes=[],
                   topics=["foo"])

    with pytest.raises(ValueError):
        FuzzTarget(image="hello-world",
                   launch_filepath="/foo/bar",
                   nodes=["bar"],
                   topics=[])
