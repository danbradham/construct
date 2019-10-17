# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Third party imports
from nose.tools import assert_raises

# Local imports
import construct

# Local imports
from . import setup_api, teardown_api


def setup_module():
    setup_api(__name__)


def teardown_module():
    teardown_api(__name__)


class SimpleAction(construct.Action):

    identifier = 'simple_action'
    label = 'Simple Action'
    icon = 'icons/simple_action.png'
    description = 'Performs a simple action.'

    def run(self, api, ctx):
        ctx['count'] += 1


class BadAction(construct.Action):

    identifier = 'bad_action'
    label = 'Bad Action'
    icon = 'icons/bad_action.png'
    description = 'An action that raises an exception.'

    def run(self, api, ctx):
        raise Exception('A bad thing happened....')


def test_simple_action():
    '''Register and call a simple action.'''

    api = construct.API(__name__)
    api.register_action(SimpleAction)

    simple_action = api.actions.get('simple_action')
    assert isinstance(simple_action, construct.Action)
    assert simple_action.api is api
    assert api.actions.loaded(SimpleAction)

    ctx = {'count': 0}
    simple_action(ctx)
    assert ctx['count'] == 1

    api.unregister_action(SimpleAction)
    assert not api.actions.loaded(SimpleAction)


def test_bad_action():
    '''Call an action that raises an exception.'''

    api = construct.API(__name__)
    api.register_action(BadAction)
    bad_action = api.actions.get('bad_action')

    with assert_raises(construct.ActionError):
        bad_action()

    api.unregister_action(BadAction)
