# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import os

# Third party imports
from bson.objectid import ObjectId

# Construct imports
from construct.compat import basestring
from construct.context import Context


def test_default_context():
    '''Validate the default context'''

    ctx = Context()

    assert ctx.user is not None
    assert ctx.host is not None
    assert ctx.platform is not None
    assert 'project' in ctx
    assert 'folder' in ctx
    assert 'asset' in ctx
    assert 'task' in ctx
    assert 'version' in ctx
    assert 'file' in ctx


def test_context_attr_access():
    '''Context attr access'''

    ctx = Context()
    ctx.x = 1

    assert 'x' in ctx
    assert ctx['x'] == 1


def test_copy_context():
    '''Copy a Context'''

    ctx = Context()
    ctx['project'] = {'_id': str(ObjectId()), '_type': 'project'}

    new_ctx = ctx.copy()
    assert ctx is not new_ctx
    assert ctx['project'] == new_ctx['project']


def test_store_and_load_context():
    '''Store a context and then load it'''

    ctx = Context()
    project = {'_id': str(ObjectId()), '_type': 'project'}
    folder = {'_id': str(ObjectId()), '_type': 'folder'}
    asset = {'_id': str(ObjectId()), '_type': 'asset'}
    ctx.project = project
    ctx.folder = folder
    ctx.asset = asset
    ctx.store()

    assert isinstance(os.environ['CONSTRUCT_PROJECT'], basestring)
    assert isinstance(os.environ['CONSTRUCT_FOLDER'], basestring)
    assert isinstance(os.environ['CONSTRUCT_ASSET'], basestring)

    new_ctx = Context()
    new_ctx.load()

    assert new_ctx.project == project
    assert new_ctx.folder == folder
    assert new_ctx.asset == asset

    # Make sure we don't leak context to other tests
    new_ctx.clear_envvars()
