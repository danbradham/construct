# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import os
import sys

# Local imports
from .utils import unipath


PLATFORM = sys.platform.rstrip('1234567890')
if PLATFORM == 'darwin':
    PLATFORM = 'mac'

EXTENSIONS_ENTRY_POINT = 'construct.extensions'
SETTINGS_FILE = 'construct.yaml'
USER_SETTINGS_FILE = unipath('~/.construct/construct.yaml')
USER_PATH = unipath('~/.construct')

DEFAULT_API_NAME = 'global'
DEFAULT_PATHS = [
    unipath('~/.construct'),
]
DEFAULT_LOCATION = 'local'
DEFAULT_MOUNT = 'projects'
DEFAULT_LOCATIONS = {
    'local': {
        'projects': unipath('~/projects').as_posix(),
        'lib': unipath('~/lib').as_posix()
    }
}
DEFAULT_TREE = {
    'asset': '{mount}/{project}/{bin}/{asset}',
    'workspace': '{mount}/{project}/{bin}/{asset}/work/{task}/{host}',
    'publish': '{mount}/{project}/{bin}/{asset}/publish/{item}/v{version:0>3d}',
    'review': '{mount}/{project}/{bin}/{asset}/review/{task}/{host}',
    'render': '{mount}/{project}/{bin}/{asset}/render/{task}/{host}',
    'file': '{task_short}_{name}_v{version:0>3d}.{ext}',
    'file_sequence': '{task_short}_{name}_v{version:0>3d}.{frame}.{ext}',
}
DEFAULT_LOGGING = dict(
    version=1,
    formatters={'simple': {
        'format': '%(levelname).1s:%(name)s> %(message)s'
    }},
    handlers={
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        }
    },
    loggers={
        'construct': {
            'level': os.environ.get('CONSTRUCT_LOGGING_LEVEL', 'DEBUG'),
            'handlers': ['console'],
            'propagate': False,
        }
    })
DEFAULT_SETTINGS = {
    'my_location': DEFAULT_LOCATION,
    'my_mount': DEFAULT_MOUNT,
    'locations': DEFAULT_LOCATIONS,
    'logging': DEFAULT_LOGGING,
}
DEFAULT_HOST = 'standalone'
