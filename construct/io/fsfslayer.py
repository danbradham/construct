# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import logging

# Local imports
from ..compat import Path
from . import fsfs
from .layer import IOLayer


_log = logging.getLogger(__name__)


def _read_project(project):
    '''Packs project data with minimum data necessary for construct 0.2+'''

    data = fsfs.read(project)
    data.setdefault('name', project.name)
    data.setdefault('_id', fsfs.get_id(project))
    data.setdefault('_type', 'project')
    return data


class FsfsLayer(IOLayer):

    def __init__(self, api):
        self.api = api
        self.settings = api.settings

    def _get_projects(self, location, mount=None):
        if mount:
            root = self.api.get_mount(location, mount)
            for entry in fsfs.search(root, max_depth=1):
                yield entry
            return

        for mount in self.settings['locations'][location].keys():
            root = self.api.get_mount(location, mount)
            for entry in fsfs.search(root, max_depth=1):
                yield entry

    def get_projects(self, location, mount=None):
        for project in self._get_projects(location, mount):
            yield _read_project(project)

    def get_project_by_id(self, _id, location=None, mount=None):

        location = self.api.context['location']

        for project in self._get_projects(location, mount):
            if fsfs.get_id(project) == _id:
                return _read_project(project)

    def get_project(self, name, location, mount=None):
        if mount:
            root = self.api.get_mount(location, mount)
            for project in fsfs.search(root, max_depth=1):
                if project.name == name:
                    return _read_project(project)
            return

        for mount in self.settings['locations'][location].keys():
            root = self.api.get_mount(location, mount)
            for project in fsfs.search(root, max_depth=1):
                if project.name == name:
                    return _read_project(project)

    def new_project(self, name, location, mount, data):
        path = self.api.get_mount(location, mount) / name

        if fsfs.exists(path):
            raise OSError('Project already exists.')

        fsfs.init(path, data['_id'])
        fsfs.tag(path, 'project')
        fsfs.write(path, **data)

        return fsfs.read(path)

    def update_project(self, project, data):

        path = self.get_path_to(project)

        if not path.exists():
            raise OSError('Project does not exist.')

        fsfs.write(path, replace=True, **data)
        fsfs.set_id(path, data['_id'])
        return fsfs.read(path)

    def delete_project(self, project):

        path = self.get_path_to(project)
        fsfs.delete(path)

    def get_assets(self, project, bin=None, asset_type=None, group=None):
        my_location = self.api.context['location']

        for path in self._get_projects(my_location):
            if fsfs.get_id(path) == project['_id']:
                project_path = path

        project = fsfs.read(project_path)
        assets = project['assets']

        for asset in assets.values():
            asset['project_id'] = project['_id']
            asset['_type'] = 'asset'

            if bin and asset['bin'] != bin:
                continue
            if asset_type and asset['asset_type'] != asset_type:
                continue
            if group and asset['group'] != group:
                continue

            asset_path = self.get_path_to(asset, project_path)
            asset = fsfs.read(asset_path)
            yield asset

    def get_asset(self, project, name):
        my_location = self.api.context['location']

        for path in self._get_projects(my_location):
            if fsfs.get_id(path) == project['_id']:
                project_path = path

        project = fsfs.read(project_path)

        asset = project['assets'][name]
        asset['project_id'] = project['_id']
        asset['_type'] = 'asset'
        asset_path = self.get_path_to(asset, project_path)
        return fsfs.read(asset_path)

    def new_asset(self, project, data):
        path = self.get_path_to(data)

        fsfs.init(path, data['_id'])
        fsfs.tag(path, 'asset')
        fsfs.write(path, **data)

        return fsfs.read(path)

    def update_asset(self, asset, data):
        path = self.get_path_to(asset)

        fsfs.write(path, replace=True, **data)
        return fsfs.read(path)

    def delete_asset(self, asset):
        path = self.get_path_to(asset)
        fsfs.delete(path)

    def get_workfiles(self, asset):
        return NotImplemented

    def get_publishes(self, asset):
        return NotImplemented

    def get_latest_workfile(self, asset, name, task, file_type):
        return NotImplemented

    def get_latest_publish(self, asset, name, task, file_type, instance=0):
        return NotImplemented

    def get_next_workfile(self, asset, name, task, file_type):
        return NotImplemented

    def get_next_publish(self, asset, name, task, file_type, instance=0):
        return NotImplemented

    def new_workfile(self, asset, name, identifier, task, file_type, data):
        return NotImplemented

    def new_publish(self, asset, name, identifier, task, file_type, data):
        return NotImplemented

    def get_path_to(self, entity, project_path=None):
        '''Get a file system path to the provided entity.'''

        my_location = self.api.context['location']

        if entity['_type'] == 'project':

            entity_locations = entity.get('locations', {})

            if not entity_locations:
                for entry in self._get_projects(my_location):
                    if fsfs.get_id(entry) == entity['_id']:
                        return entry
            else:
                if my_location in entity_locations:
                    location = my_location
                    mount = entity['locations'][location]
                else:
                    location, mount = entity['locations'].items()[0]

                root = self.api.get_mount(location, mount)
                return root / entity['name']

        if entity['_type'] == 'asset':

            if project_path is None:
                for project in self._get_projects(my_location):
                    if fsfs.get_id(project) == entity['project_id']:
                        project_path = project
                        break

            location, mount = self.api.get_mount_from_path(project_path)
            mount = self.api.get_mount(location, mount)

            project = fsfs.read(project_path)

            asset_tmpl = project['tree']['asset']
            asset_path = Path(asset_tmpl.format(
                mount=mount,
                project=project['name'],
                bin=entity['bin'],
                asset_type=entity['asset_type'],
                group=entity['group'],
                asset=entity['name'],
            ))
            return asset_path

        raise OSError('Could not find ' + entity['name'])
