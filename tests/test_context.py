# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import os

# Local imports
from construct.context import Context


def test_default_context():
    '''Validate the default context'''

    ctx = Context()

    # These values are not None
    assert ctx['user'] and ctx['host'] and ctx['platform']


def test_copy_context():
    '''Copy a Context'''

    ctx = Context()
    ctx['project'] = 'a_project'

    new_ctx = ctx.copy()
    assert ctx is not new_ctx
    assert ctx['project'] == new_ctx['project']


def test_store_and_load_context():
    '''Store a context and then load it'''

    ctx = Context()
    ctx['project'] = 'project'
    ctx['bin'] = 'bin'
    ctx['asset'] = 'asset'
    ctx.store()

    assert 'CONSTRUCT_PROJECT' in os.environ
    assert 'CONSTRUCT_BIN' in os.environ
    assert 'CONSTRUCT_ASSET' in os.environ

    new_ctx = Context()
    new_ctx.load()

    assert new_ctx['project'] == 'project'
    assert new_ctx['bin'] == 'bin'
    assert new_ctx['asset'] == 'asset'

    # Make sure we don't leak context to other tests
    new_ctx.clear_env()
