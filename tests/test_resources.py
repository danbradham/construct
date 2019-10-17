# -*- coding: utf-8 -*-

from __future__ import print_function

# Standard library imports
import sys

# Construct imports
import construct
from construct.ui import resources

# Local imports
from . import data_dir, setup_api, teardown_api


# Mock stuff
try:
    from unittest import mock
except:
    import mock
sys.modules['Qt'] = mock.MagicMock()
sys.modules['Qt.QtCore'] = mock.MagicMock()
sys.modules['Qt.QtGui'] = mock.MagicMock()
sys.modules['Qt.QtWidgets'] = mock.MagicMock()



def setup_module():
    setup_api(__name__)


def teardown_module():
    teardown_api(__name__)


def test_builtin_resources():
    '''Load and get builtin resources.'''

    r = resources.BuiltinResources()

    assert r.get('styles/theme.scss')

    try:
        r.get('doesnot/exist.png')
        assert False, 'Expected ResourceNotFoundError.'
    except resources.ResourceNotFoundError:
        assert True


def test_api_resources():
    '''Get API resources.'''

    api = construct.API(__name__)

    # Create fake resources to locate
    tmp_dir = data_dir(__name__, 'tmp')
    settings_dir = api.settings.folder
    files = [
        (tmp_dir / 'icons/unique01.png'),
        (tmp_dir / 'icons/multiple.png'),
        (tmp_dir / 'styles/theme.scss'),
        (tmp_dir / 'styles/unique01.scss'),
        (settings_dir / 'icons/unique02.png'),
        (settings_dir / 'icons/multiple.png'),
        (settings_dir / 'styles/dark.css'),
        (settings_dir / 'styles/unique02.scss'),
    ]
    for file in files:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch()

    api.path.insert(0, tmp_dir)

    # Expected resolution order
    # tmp_dir -> settings -> builtins
    resource_dir = resources.package_path
    tests = [
        ('icons/unique01.png', files[0]), # Unique to tmp_dir
        ('icons/multiple.png', files[1]), # First available
        ('styles/theme.scss', files[2]), # Builtin overriden by tmp_dir
        ('styles/unique01.scss', files[3]), # Unique to tmp_dir
        ('icons/unique02.png', files[4]), # Unique to settings_dir
        ('styles/unique02.scss', files[7]), # Unique to settings dir
        ('styles/_icons.scss', resource_dir / 'styles/_icons.scss'), # builtin
    ]
    for resource, expected_path in tests:
        resource_path = api.ui.resources.get(resource)
        err = '%s: %s != %s' % (resource, resource_path, expected_path)
        assert resource_path.samefile(expected_path), err
