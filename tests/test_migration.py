# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Third party imports
import fsfs

# Construct imports
import construct
from construct import migrations
from construct.settings import restore_default_settings
from construct.utils import unipath

# Local imports
from . import data_dir, setup_api, teardown_api


MIGRATIONS_DIR = data_dir('migrations')


def _setup_project(where):

    def new_asset(p, col, typ, asset):
        return [
            (p/'3D'/col, 'collection'),
            (p/'3D'/col/typ, 'asset_type'),
            (p/'3D'/col/typ/asset, 'asset'),
            (p/'3D'/col/typ/asset/'model', 'task'),
            (p/'3D'/col/typ/asset/'model/work/maya', 'workspace'),
            (p/'3D'/col/typ/asset/'rig', 'task'),
            (p/'3D'/col/typ/asset/'rig/work/maya', 'workspace'),
            (p/'3D'/col/typ/asset/'shade', 'task'),
            (p/'3D'/col/typ/asset/'shade/work/maya', 'workspace'),
            (p/'3D'/col/typ/asset/'light', 'task'),
            (p/'3D'/col/typ/asset/'light/work/maya', 'workspace'),
            (p/'3D'/col/typ/asset/'comp', 'task'),
            (p/'3D'/col/typ/asset/'comp/work/maya', 'workspace'),
        ]

    def new_shot(p, col, seq, shot):
        return [
            (p/'3D'/col, 'collection'),
            (p/'3D'/col/seq, 'sequence'),
            (p/'3D'/col/seq/shot, 'shot'),
            (p/'3D'/col/seq/shot/'anim', 'task'),
            (p/'3D'/col/seq/shot/'anim/work/maya', 'workspace'),
            (p/'3D'/col/seq/shot/'light', 'task'),
            (p/'3D'/col/seq/shot/'light/work/maya', 'workspace'),
            (p/'3D'/col/seq/shot/'fx', 'task'),
            (p/'3D'/col/seq/shot/'fx/work/maya', 'workspace'),
            (p/'3D'/col/seq/shot/'comp', 'task'),
            (p/'3D'/col/seq/shot/'comp/work/maya', 'workspace'),
        ]

    entries = [(where, 'project')]
    entries.extend(new_asset(where, 'assets', 'prop', 'prop_01'))
    entries.extend(new_asset(where, 'assets', 'product', 'product_01'))
    entries.extend(new_asset(where, 'assets', 'character', 'char_01'))
    entries.extend(new_shot(where, 'shots', 'seq_01', 'seq_01_010'))
    entries.extend(new_shot(where, 'shots', 'seq_01', 'seq_01_020'))
    entries.extend(new_shot(where, 'shots', 'seq_01', 'seq_01_030'))
    entries.extend(new_shot(where, 'users', 'user_01', 'user_01_010'))
    entries.extend(new_shot(where, 'users', 'user_01', 'user_01_020'))
    entries.extend(new_shot(where, 'users', 'user_01', 'user_01_030'))

    for path, tag in entries:
        fsfs.tag(str(path), tag)


def setup_module():
    setup_api(__name__)


def teardown_module():
    teardown_api(__name__)


def test_initial_migration():

    project_root = data_dir(__name__, 'projects', 'old_style_project')
    _setup_project(project_root)

    api = construct.API(__name__)

    # Make sure our project is invalid
    prj = api.io.get_project('old_style_project')
    assert '_id' not in prj

    try:
        api.io.get_folders(prj)
        assert True
    except:
        assert False, 'project does not need migration.'

    # Perform migration
    migrations.initial_migration(api, project_root)

    # Validate migration
    prj = api.io.get_project('old_style_project')

    expected_assets = ['prop_01', 'product_01', 'char_01']
    actual_assets = []
    for asset in api.io.get_assets(prj, 'asset'):
        actual_assets.append(asset['name'])
        assert '_id' in asset
    assert set(expected_assets) == set(actual_assets)

    seq = api.io.get_folder('seq_01', prj)
    expected_shots = ['seq_01_010', 'seq_01_020', 'seq_01_030']
    actual_shots = []
    for shot in api.io.get_assets(seq, 'shot'):
        actual_shots.append(shot['name'])
        assert '_id' in shot
    assert set(expected_shots) == set(actual_shots)

    seq = api.io.get_folder('user_01', prj)
    expected_shots = ['user_01_010', 'user_01_020', 'user_01_030']
    actual_shots = []
    for shot in api.io.get_assets(seq, 'shot'):
        actual_shots.append(shot['name'])
        assert '_id' in shot
    assert set(expected_shots) == set(actual_shots)


def test_collect_migrations():

    expected = set(['M1', 'M2', 'M3', 'M4', 'M5'])
    retrieved_migrations = migrations.get_migrations(MIGRATIONS_DIR)
    retrieved = set([m.__name__ for m in retrieved_migrations])
    assert expected == retrieved


def test_forward_migration():

    api = construct.API(__name__)
    entity = {'_type': 'test', 'schema_version': '0.0.2'}

    result = migrations.forward(
        api,
        entity,
        to_version=None, # None will run forward to the latest version
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
