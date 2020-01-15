# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import logging

# Local imports
from ..compat import Path
from . import fsfs
from .layer import IOLayer


_log = logging.getLogger(__name__)


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
        for entry in self._get_projects(location, mount):
            yield fsfs.read(entry)

    def get_project_by_id(self, _id, location=None, mount=None):

        location = self.api.context.location

        for project in self._get_projects(location, mount):
            if fsfs.get_id(project) == _id:
                return fsfs.read(project)

    def get_project(self, name, location, mount=None):
        if mount:
            root = self.api.get_mount(location, mount)
            for entry in fsfs.search(root, max_depth=1):
                if entry.name == name:
                    return fsfs.read(entry)
            return

        for mount in self.settings['locations'][location].keys():
            root = self.api.get_mount(location, mount)
            for entry in fsfs.search(root, max_depth=1):
                if entry.name == name:
                    return fsfs.read(entry)

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
        my_location = self.api.context.location
        project = self.get_project_by_id(project['_id'], my_location)
        assets = project['assets']

        for asset in assets.values():
            asset['project_id'] = project['_id']
            asset_path = self.get_path_to(asset)
            asset = fsfs.read(asset_path)
            if bin and asset['bin'] != bin:
                continue
            if asset_type and asset['asset_type'] != asset_type:
                continue
            if group and asset['group'] != group:
                continue
            yield asset

    def get_asset(self, project, name):
        potential_names = []
        for asset in self.get_assets(project):
            if name in asset['name']:
                potential_names.append(name)
            if asset['name'] == name:
                return asset

        if potential_names:
            return min(potential_names, key=len)

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

    def get_path_to(self, entity):
        '''Get a file system path to the provided entity.'''

        my_location = self.api.context.location

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