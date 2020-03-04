# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import logging

# Local imports
from ..compat import Path
from ..io import fsfs
from . import Migration


_log = logging.getLogger(__name__)


class InitialMigration(object):
    '''Migrates Construct 0.1.x projects.

    Special case - initial migration that needs to be updated until all old
    projects are migrated over.
    '''

    tree = {
        'asset': '{mount}/{project}/<bin_root>/{bin}/{group}/{asset}',
        'workspace': '{mount}/{project}/<bin_root>/{bin}/{group}/{asset}/{task}/work/{host}',
        'publish': '{mount}/{project}/<bin_root>/{bin}/{group}/{asset}/{task}/publish/{task_short}_{name}/v{version:0>3d}',
        'review': '{mount}/{project}/review/{task}/{bin}/{asset}',
        'render': '{mount}/{project}/<bin_root>/renders/{host}/{bin}/{asset}',
        'file': '{task_short}_{name}_v{version:0>3d}.{ext}',
        'file_sequence': '{task_short}_{name}_v{version:0>3d}.{frame}.{ext}',
    }
    project_tags = set(['project'])
    bin_tags = set(['collection'])
    group_tags = set(['asset_type', 'sequence'])
    asset_tags = set(['asset', 'shot'])
    task_tags = set(['task'])
    workspace_tags = set(['workspace'])

    def __init__(self, api, path):
        self.api = api
        self.path = path

    def forward(self):
        # Migrate root - should be project
        self.migrate(self.path)

        # Migrate bins and assets
        query = fsfs.search(self.path, max_depth=10)
        for path in query:
            self.migrate(path)

    def backward(self):
        pass

    def migrate(self, path):
        tags = set(fsfs.get_tags(path))

        if tags & self.project_tags:
            self.migrate_project(path)
        elif tags & self.bin_tags:
            self.migrate_bin(path)
        elif tags & self.asset_tags:
            self.migrate_asset(path)
        elif tags & self.task_tags:
            self.migrate_task(path)
        elif tags & self.workspace_tags:
            self.migrate_workspace(path)
        else:
            _log.debug('Could not migrate %s' % path)

    def migrate_project(self, path):
        _log.debug('Found project: %s' % path)

        data = fsfs.read(path)
        data.update(
            name=path.name,
            tree=self.tree,
        )

        # Fill data with defaults from schema
        data = self.api.schemas.validate('project', data)

        # Update tree
        first_child = next(fsfs.search(path))
        if first_child:
            bin_path = first_child.parent
            try:
                bin_root = str(bin_path.relative_to(path))
            except ValueError:
                bin_root = None

        for k, v in list(data['tree'].items()):
            if '<bin_root>' in v:
                if bin_root:
                    data['tree'][k] = v.replace('<bin_root>', bin_root)
                else:
                    data['tree'][k] = v.replace('/<bin_root>', '')

        fsfs.init(path)
        fsfs.tag(path, 'project')
        fsfs.set_id(path, data['_id'])
        fsfs.write(path, replace=True, **data)

    def migrate_bin(self, path):
        project_path = fsfs.parent(path, tag='project')
        _log.debug('Found bin: %s/%s' % (project_path.name, path.name))

        project = fsfs.read(project_path)
        bins = project.get('bins', {})

        if path.name in bins:
            return

        bin_data = {
            'name': path.name,
            'icon': '',
            'order': len(bins),
        }
        bins[bin_data['name']] = bin_data

        project['bins'] = bins
        fsfs.write(project_path, **project)

        fsfs.init(path)
        fsfs.tag(path, 'bin')
        fsfs.write(path, **bin_data)

    def migrate_asset(self, path):
        project_path = fsfs.parent(path, tag='project')
        _log.debug('Found asset: %s/%s' % (project_path.name, path.name))
        group_path = path.parent
        bin_path = path.parent.parent

        project = fsfs.read(project_path)
        tags = fsfs.get_tags(path)
        data = fsfs.read(path)

        if 'shot' in tags:
            asset_type = 'shot'
        else:
            asset_type = 'asset'

        data.update(
            project_id=project['_id'],
            name=path.name,
            asset_type=asset_type,
            group=group_path.name,
            bin=bin_path.name,
        )

        # Fill data with defaults from schema
        data = self.api.schemas.validate('asset', data)

        fsfs.init(path)
        fsfs.tag(path, 'asset')
        fsfs.write(path, **data)

        project['assets'][data['name']] = {
            '_id': data['_id'],
            'name': data['name'],
            'bin': data['bin'],
            'asset_type': data['asset_type'],
            'group': data['group'],
        }
        fsfs.write(project_path, **project)

    def migrate_task(self, task):
        pass

    def migrate_workspace(self, workspace):
        pass
