# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Construct imports
import construct
from construct.extensions import Extension

# Local imports
from . import setup_api, teardown_api


def setup_module():
    setup_api(__name__)


def teardown_module():
    teardown_api(__name__)


class Counter(Extension):

    identifier = 'counter'
    label = 'Counter'
    icon = ''

    def setup(self, api):
        self._count = 0

    def load(self, api):
        api.extend('increment', self.increment)
        api.extend('decrement', self.decrement)
        api.extend('count', self.count)

    def unload(self, api):
        api.unextend('increment')
        api.unextend('decrement')
        api.unextend('count')

    def count(self):
        return self._count

    def increment(self):
        self._count += 1

    def decrement(self):
        self._count -= 1


def test_simple_extension():
    '''Register and use a simple extension'''

    api = construct.API(__name__)
    api.register_extension(Counter)

    assert hasattr(api, 'increment')
    assert hasattr(api, 'decrement')
    assert hasattr(api, 'count')

    api.increment()
    assert api.count() == 1
    api.decrement()
    assert api.count() == 0

    api.unregister_extension(Counter)
    assert not hasattr(api, 'increment')
    assert not hasattr(api, 'decrement')
    assert not hasattr(api, 'count')


def test_builtins_loaded():
    '''Ensure all builtin extensions are loaded'''

    from construct import ext, hosts
    api = construct.API(__name__)

    for e in ext.extensions + hosts.extensions:
        assert api.extensions.loaded(e.identifier)
