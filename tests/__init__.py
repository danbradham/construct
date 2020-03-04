# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

# Standard library imports
import os
import shutil
import sys
from copy import deepcopy

# Third party imports
from nose.tools import nottest

# Local imports
import construct
from construct.settings import restore_default_settings
from construct.utils import unipath


this_dir = os.path.abspath(os.path.dirname(__file__))
TEST_LOGGING = dict(
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
            'level': 'WARNING',
            'handlers': ['console'],
        }
    },
)


@nottest
def test_dir(*paths):
    return unipath(this_dir, *paths)


def data_dir(*paths):
    return test_dir('data', *paths)


@nottest
def testAPI(name, **kwargs):
    '''Makes sure all API instances use the --logging-level set by cmd line'''

    args = sys.argv
    level = 'WARNING'
    for arg in args:
        if arg.startswith('--logging-level'):
            level = arg.split('=')[-1].strip('"\'')
    TEST_LOGGING['loggers']['construct']['level'] = level

    return construct.API(name, logging=TEST_LOGGING, **kwargs)


def setup_api(name, **settings):

    settings_path = data_dir(name, 'settings')
    restore_default_settings(settings_path)
    api = testAPI(
        name,
        path=[settings_path]
    )
    settings.setdefault(
        "locations",
        {'local': {
            'projects': data_dir(name, 'projects').as_posix(),
            'lib': data_dir(name, 'lib').as_posix()
        }}
    )
    api.settings.update(**settings)
    api.settings.save()
    return api


def teardown_api(name):
    api = testAPI(name)
    api.uninit()
    app_dir = data_dir(name)
    shutil.rmtree(str(app_dir))
    return api
