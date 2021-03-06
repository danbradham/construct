# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
import os
import sys
import argparse
import colorama
import construct
import warnings
from collections import OrderedDict
from construct import signals, get_context
from construct.constants import FAILED, SUCCESS, SKIPPED
from construct.cli.commands import commands, ActionCommand
from construct.cli.formatters import (
    Root,
    format_section,
)
from construct.cli.utils import styled, style
from construct.cli.constants import (
    OPTIONS_TITLE,
    ARTIFACTS_TITLE,
    ACTION_CONTEXT_TITLE,
    ICONS
)
from construct.cli import stout
from construct.cli.widgets import TaskLine, ProgressBar
import win_unicode_console


# Disable warnings
# TODO: Remove this in future release
warnings.simplefilter("ignore")


CONSOLE_WIDGETS = {}


@signals.route('action.before')
def on_action_before(ctx):
    print()
    print(ctx.action.description + '\n')

    if ctx.kwargs or ctx.args:
        args_data = [(k, v) for k, v in ctx.kwargs.items()]
        if ctx.args:
            args_data.append(('extra_args', ctx.args))
        args_section = format_section(
            styled('{bright}{fg.yellow}Options{reset}'),
            data=args_data,
            lcolor=style.bright
        )
        print(args_section + '\n')

    ctx_keys = ['action'] + ctx.keys
    ctx_data = []
    for k in ctx_keys:
        v = ctx[k]
        if not v:
            continue
        if k in ctx.entry_keys:
            ctx_data.append((k, v.name))
        else:
            ctx_data.append((k, v))

    ctx_section = format_section(
        ACTION_CONTEXT_TITLE,
        data=ctx_data,
        lcolor=style.bright
    )
    print(ctx_section + '\n')

    print('Status Key')
    key_tmpl = '    {} {:<8}'
    for status, icon in list(ICONS.items())[:5]:
        print(key_tmpl.format(icon, status), end='')
    print()
    for status, icon in list(ICONS.items())[5:]:
        print(key_tmpl.format(icon, status), end='')
    print('\n')

    console = stout.Console()
    console.init()
    stout.set_console(console)

    for group, tasks in ctx.task_groups.items():
        print(group.description)
        for task in tasks:
            w = TaskLine(task, console)
            CONSOLE_WIDGETS[task.identifier] = w
            console.add_widget(w)

    print()
    progress = ProgressBar('Tasks', len(ctx.tasks), console)
    CONSOLE_WIDGETS['progress'] = progress
    console.add_widget(progress)


@signals.route('action.after')
def on_action_after(ctx):

    console = stout.get_console()
    console.deinit()
    stout.set_console(None)

    # TODO: console deinit turns off colorama and win_unicode_console
    #       Might want to check colorama and win_unicode_console before
    #       console.init, if they are already enabled, don't disable them
    #       in console.deinit, assume someone else is handling it.
    win_unicode_console.enable()
    colorama.init()

    artifacts = ctx.artifacts.items()
    if not artifacts:
        print()
        return

    data = [(k, v) for k, v in artifacts if v]
    if data:
        artifacts = format_section(
            ARTIFACTS_TITLE,
            data=data,
            lcolor=style.bright
        )
        print('\n' + artifacts)
        print()


@signals.route('request.status.changed')
def on_request_status_change(request, last_status, status):

    console = stout.get_console()
    w = CONSOLE_WIDGETS[request.task.identifier]
    w.set_status(status)

    if status == FAILED:
        err = w.format_error(request.exception)
        console.insert(w.row, err)

    ctx = get_context()
    progress = CONSOLE_WIDGETS['progress']
    i = 0
    for request in ctx.requests.values():
        if request._status in [FAILED, SUCCESS, SKIPPED]:
            i += 1
    progress.set_value(i)


def logging_config(level):
    return dict(
        version=1,
        formatters={
            'simple': {
                'format': '%(levelname).1s:%(name)s> %(message)s'
            }
        },
        handlers={
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            }
        },
        loggers={
            'construct': {
                'level': level,
                'handlers': ['console'],
                'propagate': False
            }
        }
    )


def setup_parser():
    '''Build the root parser'''

    usage = styled(
        '{bright}construct '
        '{fg.blue}<command|action>{fg.reset} '
        '{fg.yellow}[options]{reset}'
    )
    parser = argparse.ArgumentParser(
        'construct',
        usage=usage,
        formatter_class=Root,
        add_help=False,
    )
    parser._optionals.title = OPTIONS_TITLE
    parser.add_argument(
        '-h',
        '--help',
        help='show this help message and exit',
        action='store_true',
        dest='-h'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        help='verbose output',
        action='store_true',
        dest='-v'
    )
    parser.add_argument(
        'command',
        help=argparse.SUPPRESS,
        action='store',
        nargs='?'
    )
    return parser


def main():
    '''CLI Entry Point'''

    # Enable ansi console colors
    win_unicode_console.enable()
    colorama.init()

    parser = setup_parser()
    args, extra_args = parser.parse_known_args()
    root_flags = [f for f, v in args.__dict__.items()
                  if f.startswith('-') and v]

    # Configure Construct
    logging_level = ('WARNING', 'DEBUG')[args.__dict__['-v']]
    construct.init(host='cli', logging=logging_config(logging_level))
    construct.set_context_from_path(os.getcwd())

    # Add all subcommands including contextual actions
    subcommands = OrderedDict()

    for command in commands:
        subcommands[command.name] = command(parser)

    for action in construct.actions:
        subcommands[action.identifier] = ActionCommand(action, parser)

    # Print root help if we received no command argument
    if not args.command:
        parser.print_help()
        sys.exit()

    command_name = args.command
    command_args = root_flags + extra_args

    if command_name not in subcommands:
        print('Command does not exist: ', command_name)
        sys.exit(1)

    command = subcommands[command_name]
    args, extra_args = command.parse(command_args)
    args.__dict__.pop('verbose')
    command.run(args, *extra_args)


if __name__ == '__main__':
    main()
