# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

__all__ = [
    'Action',
    'ActionCollector',
    'ActionProxy',
    'get_action_identifier',
    'group_actions',
    'is_action',
    'is_action_type',
    'sort_actions',
]

import abc
import logging
from operator import attrgetter
from collections import OrderedDict
from construct import types, actionparams
from construct.utils import missing
from construct.actionrunner import ActionRunner
from construct.tasks import sort_tasks
from construct.errors import ActionUnavailable


_log = logging.getLogger(__name__)


class Action(types.ABC):
    '''Action Base Class

    Attributes:
        label (str): Nice name used for labeling like: 'New Project'
        identifier (str): Used to find and run the action like: 'new.project'
        description (str): Description of what the action does
        parameters (dict or staticmethod): Description of parameters for
        validation like:

        {
            'str_param': {
                'label': 'Str Param',
                'type': str,
                'required': True,
            },
            'int_param': {
                'label': 'Int Param',
                'type': int,
                'required': False,
                'default': 1
            },
            ...
        }

    '''

    runner_cls = ActionRunner
    parameters = {}

    @abc.abstractproperty
    def label(self):
        pass

    @abc.abstractproperty
    def description(self):
        pass

    @abc.abstractproperty
    def identifier(self):
        pass

    @abc.abstractmethod
    def available(ctx):
        '''
        Return True if this action is available in the provided Context. Must
        be a classmethod or staticmethod.

        Arguments:
            ctx (Context): Context class
        '''

    @classmethod
    def params(cls, ctx):
        if callable(cls.parameters):
            return cls.parameters(ctx)
        return cls.parameters

    def __init__(self, **kwargs):
        from construct.api import get_context
        from construct.actioncontext import ActionContext

        # Create action context
        ctx = kwargs.pop('ctx', get_context())
        self.ctx = ActionContext(self, kwargs, ctx)

        # Validate params
        params = self.params(self.ctx)
        actionparams.validate(params)

        # Validate kwargs against params
        actionparams.validate_kwargs(params, self.ctx.kwargs)

        # Create action runner
        self.runner = self.runner_cls(self, self.ctx)

    def __call__(self):
        return self.runner.run()

    def __getattr__(self, attr):
        return self.ctx.__dict__.get(attr)

    def retry_group(self, priorty):
        return self.runner.retry_group(priority)

    def run_group(self, priority):
        return self.runner.run_group(priority)

    def run(self):
        return self.runner.run()


def is_action_type(obj):
    return (
        obj is not Action and
        isinstance(obj, type) and
        issubclass(obj, Action)
    )


def is_action(obj):
    return isinstance(obj, Action)


def get_action_identifier(action_or_identifier):

    identifier = getattr(action_or_identifier, 'identifier', None)
    if identifier:
        return identifier

    if isinstance(action_or_identifier, basestring):
        return action_or_identifier

    raise RuntimeError(
        'Can not determine identifier of %s' % action_or_identifier
    )


class ActionCollector(object):

    def __init__(self, extension_collector):
        self._extensions = extension_collector

    def __iter__(self):
        for action in self.collect().values():
            yield action

    def __getattr__(self, identifier):
        return self.get(identifier)

    def get(self, identifier, ctx=None):
        from construct.api import get_context
        ctx = ctx or get_context()
        try:
            action = self.collect(ctx)[identifier]
        except KeyError:
            _log.error('Action not found: %s', identifier, exc_info=True)
        else:
            if not action.available(ctx):
                raise ActionUnavailable('Action unavailable in ctx: %s', ctx)
            return action

    def collect(self, ctx=None):

        from construct.api import get_context
        ctx = ctx or get_context()
        actions = {}
        for name, extension in self._extensions.by_name.items():
            if extension.enabled and extension._available(ctx):
                ext_actions = extension.get_actions(ctx)
                for identifier, action in ext_actions.items():
                    if identifier in actions:
                        _log.warning(
                            'Action identifier collision: %s <-> %s',
                            actions[identifier], action
                        )
                    else:
                        actions[identifier] = action

        return actions

    def collect_tasks(self, action_or_identifier, ctx=None):

        from construct.api import get_context
        ctx = ctx or get_context()
        identifier = get_action_identifier(action_or_identifier)

        tasks = []
        for name, extension in self._extensions.by_name.items():
            if extension.enabled and extension._available(ctx):
                more_tasks = extension.get_tasks(identifier, ctx)
                tasks.extend(more_tasks)

        return sort_tasks(tasks)


class ActionProxy(object):

    def __init__(self, identifier):
        self.identifier = identifier

    @property
    def action(self):
        from construct import actions
        return actions.get(self.identifier)

    def instance(self, **kwargs):
        return self.action(**kwargs)

    def __repr__(self):
        return repr(self.action)

    def __str__(self):
        return str(self.action)

    def __getattr__(self, attr):
        return getattr(self.action, attr)

    def __call__(self, **kwargs):
        a = self.action(**kwargs)
        a.run()
        return a.ctx.artifacts


def sort_actions(actions):
    '''Sort the given actions by identifier'''

    return sorted(actions, key=attrgetter('identifier'))


def group_actions(actions):
    '''Group sorted actions in a tree structure.

    Returns:
        OrderedDict suitable for creating a nested menu
    '''

    if isinstance(actions, dict):
        actions = sort_actions(actions.values())
    else:
        actions = sort_actions(actions)

    groups = OrderedDict()
    for action in actions:
        parts = action.identifier.split('.')
        if len(parts) == 1:
            groups.setdefault('', [])
            groups[''].append(action)
        else:
            nodes = parts[:-1]
            section = None
            for node in nodes:
                if section is None:
                    section = groups.setdefault(node, OrderedDict())
                    section.setdefault('', [])
                else:
                    section = section.setdefault(node, OrderedDict())
                    section.setdefault('', [])
            section[''].append(action)

    return groups
