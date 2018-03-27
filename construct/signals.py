# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

__all__ = [
    'route',
    'chain',
    'send',
    'connect',
    'disconnect',
]

from collections import defaultdict
from fnmatch import fnmatch
from construct.types import weakset


_subscribers = defaultdict(weakset)


def get_subscribers(identifier):
    '''Yield all subscribers for identifier, including fuzzy matches.

    Arguments:
        identifier (str): Signal identifier

    Yields:
        callable subscribers
    '''

    for subscriber in _subscribers[identifier]:
        yield subscriber

    for key in _subscribers.keys():
        if key == identifier:
            continue

        # Fuzzy Subscription
        if fnmatch(identifier, key):
            for subscriber in _subscribers[key]:
                yield subscriber


def send(identifier, *args, **kwargs):
    '''Send signal

    Arguments:
        identifier (str): signal identifier
    '''

    results = []
    for subscriber in get_subscribers(identifier):
        results.append(subscriber(*args, **kwargs))
    return results


def chain(identifier, *args, **kwargs):
    '''Chain signal subscribers

    Arguments:
        identifier (str): signal identifier
    '''

    subscribers = list(get_subscribers(identifier))
    if not subscribers:
        return

    result = subscribers[0](*args, **kwargs)
    if len(subscribers) == 1:
        return result

    for subscriber in subscribers[1:]:
        result = subscriber(result)

    return result


def route(identifier):
    '''Connect function to signal via decorator, only works with functions.

    Arguments:
        identifier (str): signal identifier
    '''

    def connect_to_signal(obj):
        connect(identifier, obj)
        return obj
    return connect_to_signal


def connect(identifier, obj):
    '''Connect function to signal

    Arguments:
        identifier (str): signal identifier
        obj (callable): signal subscriber
    '''

    _subscribers[identifier].add(obj)


def disconnect(identifier, obj):
    '''Disconnect function to signal

    Arguments:
        identifier (str): signal identifier
        obj (callable): signal subscriber
    '''

    _subscribers[identifier].discard(obj)
