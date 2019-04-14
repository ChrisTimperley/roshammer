import os

import pytest

from roswire.definitions import Message, Time
from roswire.bag.core import BagMessage

from roshammer.bag import Bag

from util import get_test_type_database


def build_test_bag(length: int) -> Bag:
    """
    Creates a simple bag that contains a specified number of messages of
    a single type (Vector3) on a single topic (/pos), where each message is
    separated by 1 second delay.
    """
    db_type = get_test_type_database()
    Vector3 = db_type['geometry_msgs/Vector3']
    topic = '/pos'
    period = 1.0
    messages = [Vector3(0.0 + i, 1.0 + i, 2.0 + i) for i in range(length)]
    times = [Time(secs=(1.0 * i), nsecs=0.0) for i in range(length)]
    bag_messages = [BagMessage(time=t, message=m, topic=topic)
                    for (t, m) in zip(times, messages)]
    return Bag(bag_messages)


def test_delete():
    length = 10
    bag_orig = build_test_bag(length)
    bag = Bag(bag_orig)
    for i in range(length):
        m = bag[i]
        bag_without_m = bag.delete(i)
        assert bag == bag_orig
        assert len(bag_without_m) == length - 1
        assert bag[i] == m
        if i < length - 1:
            assert bag_without_m[i] != m


def test_insert():
    db_type = get_test_type_database()
    Vector3 = db_type['geometry_msgs/Vector3']
    bag = build_test_bag(10)

    time = Time(0.3, 0.1)
    m = BagMessage(topic='/pos', message=Vector3(-1.0, -2.0, -3.0), time=time)
    bag_with_m = bag.insert(m)
    assert len(bag_with_m) == len(bag) + 1
    assert m not in bag
    assert m in bag_with_m
    assert all(x in bag_with_m for x in bag)
    assert bag_with_m.index(m) == 1
