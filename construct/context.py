# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import copy
import getpass
import json
import os

# Local imports
from .compat import basestring
from .constants import DEFAULT_HOST, PLATFORM
from .errors import ContextError


__all__ = ['Context', 'validate_context']


def encode(obj):
    '''Encode objects to stuff in environment variables'''

    return json.dumps(obj)


def decode(obj):
    '''Decode objects stored in environment variables'''

    return json.loads(obj)


class Context(dict):
    '''Represents a state used to interact with Construct.

    >>> ctx = Context()
    >>> ctx['project'] == ctx.project

    Context objects can be loaded from and stored in environment variables
    prefixed with **CONSTRUCT_**.

    +-----------+------------------------------------------------------+
    |   key     |                     description                      |
    +===========+======================================================+
    | user      | usually the same as the logged in user               |
    +-----------+------------------------------------------------------+
    | platform  | Current platform [win, linux, mac]                   |
    +-----------+------------------------------------------------------+
    | host      | Host application like maya, nuke, standalone, etc... |
    +-----------+------------------------------------------------------+
    | location  | Location name                                        |
    +-----------+------------------------------------------------------+
    | mount     | Mount name                                           |
    +-----------+------------------------------------------------------+
    | project   | Project name                                         |
    +-----------+------------------------------------------------------+
    | bin       | Bin name                                             |
    +-----------+------------------------------------------------------+
    | asset     | Asset name                                           |
    +-----------+------------------------------------------------------+
    | task      | Task name                                            |
    +-----------+------------------------------------------------------+
    | workspace | Directory of current workspace                       |
    +-----------+------------------------------------------------------+
    | file      | Path to current working file                         |
    +-----------+------------------------------------------------------+

    The above keys default to None, convenient for quickly checking context.

    >>> if ctx['project'] and ctx['task']:
    ...     # Do something that depends on a project and task

    '''

    _keys = [
        'platform',
        'user',
        'host',
        'location',
        'mount',
        'project',
        'bin',
        'asset',
        'task',
        'workspace',
        'file',
    ]
    _defaults = {k: None for k in _keys}
    _defaults['user'] = getpass.getuser()
    _defaults['platform'] = PLATFORM
    _defaults['host'] = DEFAULT_HOST

    def __init__(self, **kwargs):
        self.update(**self._defaults)
        self.update(**kwargs)

    def trim(self, key):
        '''Returns a new context with context beyond key set to None.

        Example:
            >>> c = Context(location='location', mount='mount',
            ...             project='project', bin='bin', asset='asset')
            >>> c2 = c.trim('project')
            >>> assert c2['project'] == 'project'
            >>> assert c2['bin'] is None
            >>> assert c2['asset'] is None
        '''
        context = Context()
        include = [
            'host',
            'location',
            'mount',
            'project',
            'bin',
            'asset',
            'task'
            'workspace',
        ]
        include = include[:include.index(key) + 1]
        context.update(**{k: self[k] for k in include})
        return context

    def set(self, key, value):
        self[key] = value

    def copy(self, *include_keys):
        '''Copy this context'''
        return self.__class__(**copy.deepcopy(self))

    def load(self, env=None, **kwargs):
        '''Update ctx with values stored in environment variables. You can
        optionally pass a dictionary to load from. This is different than using
        update because it only updates standard context keys rather than
        updating all keys.
        '''

        env = env or os.environ
        self.update(**kwargs)

        for key in self._keys:
            env_key = ('construct_' + key).upper()
            value = env.get(env_key, None)
            if value:
                try:
                    self[key] = decode(value)
                except ValueError:
                    self[key] = value

    def unload(self):
        '''Restore this Context to defaults'''

        self.clear()
        self.update(**self._defaults)

    def store(self, env=None):
        '''Store this Context in os.environ. You may also pass a dict.'''

        env = env or os.environ
        env.update(self._to_env())

    def _to_env(self):
        '''Serialize ctx to strings storable as environment values.'''

        env = {}
        for key in self._keys:
            env_key = ('construct_' + key).upper()
            value = self.get(key, None)
            if value:
                if isinstance(value, basestring):
                    env[env_key] = value
                else:
                    env[env_key] = encode(value)
        return env

    @classmethod
    def clear_env(cls, env=None):
        env = env or os.environ
        for key in cls._keys:
            env_key = ('construct_' + key).upper()
            os.environ.pop(env_key, None)


def validate_context(api, context):
    '''Return True if context is Valid.'''

    # validate context
    locations = api.get_locations()
    if context['location'] and context['location'] not in locations:
        raise ContextError('Location does not exist: ' + context['location'])

    mounts = locations[context['location']]
    if context['mount'] and context['mount'] not in mounts:
        raise ContextError('Mount does not exist: ' + context['mount'])

    io_context = {
        'location': context['location'],
        'mount': context['mount'],
    }

    project = None
    if context['project']:
        with api.set_context(io_context):
            project = api.io.get_project(context['project'])
        if not project:
            raise ContextError('Project does not exist: ' + context['project'])
        path = api.io.get_path_to(project)
        location, mount = api.get_mount_from_path(path)
        context['mount'] = mount

    bin = None
    if context['bin']:
        conditions = [
            not project,
            context['bin'] not in project['bins'],
        ]
        if any(conditions):
            raise ContextError('Bin does not exist: ' + context['bin'])
        bin = context['bin']

    asset = None
    if context['asset']:
        conditions = [
            not project,
            not bin,
            context['asset'] not in project['assets'],
        ]
        if any(conditions):
            raise ContextError('Asset does not exist: ' + context['asset'])
        asset = context['asset']

    task = None
    if context['task']:
        conditions = [
            not project,
            context['task'] not in project['task_types']
        ]
        if any(conditions):
            raise ContextError('Task is invalid: ' + context['task'])

    return context
