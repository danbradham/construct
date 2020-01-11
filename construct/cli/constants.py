# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Standard library imports
from collections import OrderedDict
from platform import platform

# Local imports
from .utils import styled


ACTION_CONTEXT_TITLE = styled('{normal}Action Context{reset}')
ACTIONS_TITLE = styled('{bright}{fg.blue}Actions{reset}')
ARGUMENTS_TITLE = styled('{bright}{fg.blue}Arguments{reset}')
ARTIFACTS_TITLE = styled('{bright}{fg.green}Artifacts{reset}')
COMMANDS_TITLE = styled('{bright}{fg.blue}Commands{reset}')
CONTEXT_TITLE = styled('{normal}Current Context{reset}')
DEPRECATED_TITLE = ''  # styled('{dim}{fg.blue}Deprecated{reset}')
OPTIONS_TITLE = styled('{bright}{fg.yellow}Options{reset}')

STATUS_LABELS = {
    'WAITING': styled('{dim}WAITING{reset}'),
    'PENDING': styled('{dim}PENDING{reset}'),
    'RUNNING': styled('{fg.green}RUNNING{reset}'),
    'SUCCESS': styled('{bright}{fg.green}SUCCESS{reset}'),
    'FAILED': styled('{bright}{fg.red}FAILED{reset}'),
    'SKIPPED': styled('{fg.cyan}SKIPPED{reset}'),
    'PAUSED': styled('{fg.red}PAUSED{reset}'),
    'DISABLED': styled('{dim}DISABLED{reset}'),
    'ENABLED': styled('{bright}ENABLED{reset}'),
}
ICONS = OrderedDict([
    ('ENABLED', styled('{dim}{fg.green}◌{reset}')),
    ('DISABLED', styled('{dim}{fg.red}◌{reset}')),
    ('WAITING', styled('{dim}◌{reset}')),
    ('RUNNING', styled('{fg.green}◌{reset}')),
    ('PENDING', styled('{bright}{fg.magenta}◌{reset}')),
    ('PAUSED', styled('{bright}{fg.cyan}◌{reset}')),
    ('SKIPPED', styled('{bright}{fg.blue}◌{reset}')),
    ('SUCCESS', styled('{bright}{fg.green}●{reset}')),
    ('FAILED', styled('{bright}{fg.red}●{reset}')),
])


if platform().startswith('Windows-7'):
    # Use cp437 compatible characters on Windows 7
    ICONS = OrderedDict([
        ('ENABLED', styled('{dim}{fg.green}○{reset}')),
        ('DISABLED', styled('{bright}{fg.red}○{reset}')),
        ('WAITING', styled('{dim}○{reset}')),
        ('RUNNING', styled('{fg.green}○{reset}')),
        ('PENDING', styled('{bright}{fg.magenta}○{reset}')),
        ('PAUSED', styled('{bright}{fg.cyan}○{reset}')),
        ('SKIPPED', styled('{bright}{fg.blue}○{reset}')),
        ('SUCCESS', styled('{bright}{fg.green}•{reset}')),
        ('FAILED', styled('{bright}{fg.red}•{reset}')),
    ])
