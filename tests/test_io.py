# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Construct imports
import construct
from construct.settings import restore_default_settings

# Local imports
from . import data_dir, setup_api, teardown_api


def setup_module():
    setup_api(__name__)


def teardown_module():
    teardown_api(__name__)


def test_new_projects():
    '''Create two new projects'''

    api = construct.API(__name__)

    project = api.io.new_project(
        name='project',
        location='local',
        mount='projects',
        data={'is_project': True, 'is_library': False}
    )
    project_path = api.io.get_path_to(project)
    assert (project_path / '.data').exists()
    assert project_path.exists()
    assert project['is_project']
    assert not project['is_library']

    library = api.io.new_project(
        name='library',
        location='local',
        mount='lib',
        data={'is_project': False, 'is_library': True}
    )
    library_path = api.io.get_path_to(library)
    assert (library_path / '.data').exists()
    assert library_path.exists()
    assert library['is_library']
    assert not library['is_project']
