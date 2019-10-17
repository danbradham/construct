# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import logging
import sys
from collections import OrderedDict

# Local imports
from .compat import reraise
from .errors import ActionError


__all__ = [
    'Action',
    'ActionManager',
    'is_action_type',
    'is_action',
]


_log = logging.getLogger(__name__)


class Action(object):
    '''An action is an executable tool that can be presented to users in
    Constructs UI.
    '''

    description = ''
    icon = ''
    identifier = ''
    label = ''

    def __init__(self, api):
        self.api = api

    def __call__(self, ctx=None):
        try:
            self.run(self.api, ctx or self.api.context.copy())
        except:
            exc_typ, exc_value, exc_tb = sys.exc_info()
            reraise(ActionError, ActionError(exc_value), exc_tb)

    def run(self, api, ctx):
        '''Subclasses should implement run to perform the Action's work.'''
        return NotImplemented

    def is_available(self, ctx):
        '''Return True if the Action is available in the given context'''
        return True


ACTION_TYPES = (Action,)


def is_action_type(obj):
    '''Check if an obj is an Action type.'''

    return (
        obj not in ACTION_TYPES and
        isinstance(obj, type) and
        issubclass(obj, ACTION_TYPES)
    )


def is_action(obj):
    '''Check if an obj is an Action instance.'''

    return isinstance(obj, ACTION_TYPES)


class ActionManager(OrderedDict):

    def __init__(self, api):
        self.api = api

    def load(self):
        pass

    def unload(self):
        '''Unload all Actions'''
        self.clear()

    def register(self, action):
        '''Register an Action'''

        if self.loaded(action):
            _log.error('Action already loaded: %s' % action)
            return

        _log.debug('Loading action: %s' % action)
        if is_action_type(action):
            inst = action(self.api)
        elif is_action(action):
            inst = action
        else:
            _log.error('Expected Action type got %s' % action)
            return

        self[action.identifier] = inst

    def unregister(self, action):
        '''Unregister an Action'''

        identifier = getattr(action, 'identifier', action)
        self.pop(identifier, None)
        _log.debug('Unloading action: %s' % action)

    def loaded(self, action):
        '''Check if an Action has been loaded.'''

        identifier = getattr(action, 'identifier', action)
        return identifier in self

    def ls(self, typ=None):
        '''Get a list of available actions.

        Arguments:
            typ (Action, Optional): List only a specific type of Action.

        Examples:
            ls()  # lists all actions
            ls(ActionWrapper)  # list only ActionWrapper
        '''

        matches = []
        for action in self.values():
            if not type or isinstance(action, typ):
                matches.append(action)
        return matches

    def get_available(self, ctx=None, typ=None):
        '''Get actions available in the provided contaction.'''

        ctx = ctx or self.api.context.copy()
        return [action for action in self.values() if action.is_available(ctx)]
