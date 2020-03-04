# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Local imports
import construct
from construct import migrations

# Local imports
from . import data_dir, setup_api, teardown_api


MIGRATIONS_DIR = data_dir('migrations')


def setup_module():
    setup_api(__name__)


def teardown_module():
    teardown_api(__name__)


def test_initial_migration():
    '''Migrate old style project.'''

    project_root = data_dir(__name__, 'projects', 'old_style_project')
    migrations.utils.create_old_project(project_root)

    api = construct.API(__name__)

    # Make sure our project is invalid
    prj = api.io.get_project('old_style_project')
    assert 'schema_version' not in prj

    # Perform migration
    migrations.initial_migration(api, project_root)

    # Validate migration
    prj = api.io.get_project('old_style_project')

    expected_assets = ['prop_01', 'product_01', 'char_01']
    actual_assets = []
    for asset in api.io.get_assets(prj, asset_type='asset'):
        actual_assets.append(asset['name'])
        assert '_id' in asset
        assert asset['name'] in prj['assets']
    assert set(expected_assets) == set(actual_assets)

    expected_shots = ['seq_01_010', 'seq_01_020', 'seq_01_030']
    actual_shots = []
    for shot in api.io.get_assets(prj, group='seq_01', asset_type='shot'):
        actual_shots.append(shot['name'])
        assert '_id' in shot
        assert shot['name'] in prj['assets']
    assert set(expected_shots) == set(actual_shots)

    expected_shots = ['user_01_010', 'user_01_020', 'user_01_030']
    actual_shots = []
    for shot in api.io.get_assets(prj, group='user_01', asset_type='shot'):
        actual_shots.append(shot['name'])
        assert '_id' in shot
        assert shot['name'] in prj['assets']
    assert set(expected_shots) == set(actual_shots)


def test_collect_migrations():
    '''Collect migrations from a folder.'''

    expected = set(['M1', 'M2', 'M3', 'M4', 'M5'])
    retrieved_migrations = migrations.get_migrations(MIGRATIONS_DIR)
    retrieved = set([m.__name__ for m in retrieved_migrations])
    assert expected == retrieved


def test_forward_migration():
    '''Migrate data forward.'''

    api = construct.API(__name__)
    entity = {'_type': 'test', 'schema_version': '0.0.2'}

    result = migrations.forward(
        api,
        entity,
        to_version=None,  # None will run forward to the latest version
        migrations_dir=MIGRATIONS_DIR,
    )
    assert result['schema_version'] == '1.0.1'

    result = migrations.forward(
        api,
        entity,
        to_version='0.2.1',
        migrations_dir=MIGRATIONS_DIR,
    )
    assert result['schema_version'] == '0.2.1'


def test_backward_migration():
    '''Migrate date backward.'''

    api = construct.API(__name__)
    entity = {'_type': 'test', 'schema_version': '1.1.0'}

    result = migrations.backward(
        api,
        entity,
        to_version='0.0.1',
        migrations_dir=MIGRATIONS_DIR,
    )
    assert result['schema_version'] == '0.0.1'

    result = migrations.backward(
        api,
        entity,
        to_version='0.2.1',
        migrations_dir=MIGRATIONS_DIR,
    )
    assert result['schema_version'] == '0.2.1'
