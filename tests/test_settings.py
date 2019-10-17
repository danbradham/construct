# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import os
import shutil
import sys

# Construct imports
from construct.constants import DEFAULT_SETTINGS
from construct.errors import InvalidSettings, ValidationError
from construct.settings import Settings, restore_default_settings

# Local imports
from . import data_dir


SETTINGS_FOLDER = data_dir('.cons')
SETTINGS_FOLDERS = [data_dir('.cons', f) for f in Settings.structure]
SETTINGS_FILE = data_dir('.cons', 'construct.yaml')
CONSTRUCT_PATH = [SETTINGS_FOLDER]
NEW_LOCATIONS = dict(
    local=dict(
        projects='~/projects',
        lib='~/lib'
    ),
    remote=dict(
        projects='//remote/projects',
        lib='//remote/lib',
    )
)
ITEMS_SECTION = ('items', {'value': {'type': 'string'}})


def teardown_module():
    shutil.rmtree(str(SETTINGS_FOLDER))


def test_create_default_settings():
    '''Create default settings'''

    restore_default_settings(SETTINGS_FOLDER)
    assert SETTINGS_FOLDER.is_dir()
    assert SETTINGS_FILE.is_file()
    assert all([f.is_dir() for f in SETTINGS_FOLDERS])

    settings = Settings(CONSTRUCT_PATH)
    settings.load()
    assert settings.file == SETTINGS_FILE
    assert settings.folder == SETTINGS_FOLDER


def test_save_settings():
    '''Save modified settings'''

    settings = Settings(CONSTRUCT_PATH)
    settings.load()
    settings['locations'] = NEW_LOCATIONS
    settings.save()

    settings = Settings(CONSTRUCT_PATH)
    settings.load()
    assert settings['locations'] == NEW_LOCATIONS


def test_restore_default_settings():
    '''Restore default settings'''

    restore_default_settings(SETTINGS_FOLDER)
    settings = Settings(CONSTRUCT_PATH)
    settings.load()
    for k, v in DEFAULT_SETTINGS.items():
        assert settings[k] == v


def test_section():
    '''Add and modify settings section'''

    settings = Settings(CONSTRUCT_PATH)
    settings.load()

    # Add new section and test dict get and set
    assert not (settings.folder / 'items').exists()
    settings.add_section(*ITEMS_SECTION)
    assert (settings.folder / 'items').exists()

    settings['items']['greeting'] = {'value': 'Hello World!'}
    assert (settings.folder / 'items' / 'greeting.yaml').exists()
    assert settings['items']['greeting']['value'] == 'Hello World!'

    # Make sure schema is validating
    try:
        settings['items']['funk'] = {'value': 2}
        assert False
    except ValidationError:
        assert True

    # Verify that settings loads sections from disk
    settings = Settings(CONSTRUCT_PATH)
    settings.load()
    settings.add_section(*ITEMS_SECTION)

    items = settings['items']
    assert items == {'greeting': {'value': 'Hello World!'}}
    assert items.files['greeting'] == items.folder / 'greeting.yaml'
