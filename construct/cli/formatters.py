# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Standard library imports
import argparse
from collections import OrderedDict

# Local imports
import construct
from construct.cli.constants import (
    ACTIONS_TITLE,
    COMMANDS_TITLE,
    CONTEXT_TITLE,
    DEPRECATED_TITLE,
)

# Local imports
from ..utils import is_deprecated
from .utils import style, styled


reset = style.reset


def new_formatter(parent, formatter_type):
    return type(
        formatter_type.__name__,
        (formatter_type,),
        dict(
            parent=parent
        )
    )


def format_context(ctx):
    '''Format current context.'''

    ctx_data = []
    for k, v in ctx.items():
        if not v:
            continue
        try:
            ctx_data.append((k, v['name']))
        except (KeyError, TypeError):
            ctx_data.append((k, v))
    return format_section(
        CONTEXT_TITLE,
        ctx_data,
        lcolor=styled('{bright}')
    )


def format_commands(cmds, title=None):
    '''Format builtin cli commands.'''
    if not cmds:
        return

    c = [(c.name, c.short_description) for c in cmds if not is_deprecated(c)]
    d = [(c.name, c.short_description) for c in cmds if is_deprecated(c)]

    title = title or COMMANDS_TITLE
    result = ''
    if c:
        result += format_section(title, c, lcolor=styled('{bright}'))
    if d:
        result += '\n'
        result += format_section(DEPRECATED_TITLE, d, lcolor=styled('{dim}'))

    return result


def format_section(title, data, indent='', lcolor=reset, rcolor=reset):
    '''Format a section like...

    title:
        name - description
        ...
    '''

    if isinstance(data, dict):
        data = list(data.items())

    width = max(max([len(k) for k, v in data]), 12)
    line = indent + '  {lc}{:<{w}}{reset}  {rc}{}{reset}'

    lines = []
    if title:
        lines.append(indent + title)
    for key, value in data:
        lines.append(styled(line, key, value, w=width, lc=lcolor, rc=rcolor))
    return '\n'.join(lines)


class ContextualFormatter(
    argparse.RawDescriptionHelpFormatter,
    argparse.ArgumentDefaultsHelpFormatter
):

    def _format_action(self, action):
        '''Colorize Arguments section.'''

        help = super(ContextualFormatter, self)._format_action(action)
        lines = help.split('\n')
        name = lines[0].split()[0]
        nice_name = styled('{bright}{}{reset}', name)
        lines[0] = lines[0].replace(name, nice_name, 1)
        for i, line in enumerate(lines):
            if '(default: None)' in line:
                line = line.replace('(default: None)', '', 1)
                if not line.strip():
                    lines.pop(i)
                else:
                    lines[i] = line
        return '\n'.join(lines)

    def add_usage(self, usage, groups, prefix=None):

        parent = getattr(self, 'parent', None)
        if parent:
            usage = parent.usage
            description = parent.description
        else:
            description = None

        prefix = 'Usage: '
        super(ContextualFormatter, self).add_usage(usage, groups, prefix)
        if description:
            self.add_text('\n' + description)

    def add_section(self, header, lines):
        self.start_section(header)
        self.add_lines(lines)
        self.end_section()

    def add_lines(self, lines):
        def format_lines(*args):
            cind = self._current_indent * ' '
            text = cind + (('\n' + cind).join(args))
            return text
        self._add_item(format_lines, lines)


class RootFormatter(ContextualFormatter):

    def add_usage(self, usage, groups, prefix=None):
        super(RootFormatter, self).add_usage(usage, groups, prefix)
        from . import commands, actions
        api = construct.API()
        ctx = api.get_context()

        self.add_text(format_context(ctx))
        self.add_text(format_commands(commands.get_available(ctx)))
        actions = api.get_cli_actions(ctx) + actions.get_available(ctx)
        self.add_text(format_commands(actions, ACTIONS_TITLE))
