# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import logging

# Third party imports
import fsfs

# Local imports
from ..compat import Path


_log = logging.getLogger(__name__)


def search_by_id(path, _id, max_depth=10, return_typ=None):
    '''Search by id using recursive globbing'''

    roots = [Path(path)]
    entry_pattern = '*/.data/uuid_*'
    entry_id = 'uuid_' + _id
    level = 0

    while roots and level < max_depth:
        next_roots = []
        for root in roots:
            for entry in root.glob(entry_pattern):
                if entry.name == entry_id:
                    result = entry.parent.parent
                    if return_typ:
                        result = return_typ(result.as_posix())
                    return result
                else:
                    next_roots.append(entry.parent.parent)
        level += 1
        roots = next_roots


def search_by_name(path, name, max_depth=10, return_typ=None):
    '''Search by name using recursive globbing'''

    roots = [Path(path)]
    entry_pattern = '*/.data/uuid_*'
    entry_name = name
    level = 0
    potential_entries = []

    while roots and level < max_depth:
        next_roots = []
        for root in roots:
            for entry in root.glob(entry_pattern):
                entry = entry.parent.parent
                if entry_name in entry.name:
                    potential_entries.append(entry)
                if entry.name == entry_name:
                    if return_typ:
                        entry = return_typ(entry.as_posix())
                    return entry
                else:
                    next_roots.append(entry)
        level += 1
        roots = next_roots

    if potential_entries:
        # In almost all cases the best match will be the shortest path
        # with the least parts.
        best = min(
            potential_entries,
            key=lambda x: (len(x.parts), len(str(x)))
        )
        if return_typ:
            best = return_typ(best.as_posix())
        return best


def select_by_name(path, selector, max_depth=10, return_typ=None):
    '''Search for a nested name using a selector string.

    Selector strings are / separated names that look like file paths but
    can use partial names.
    '''

    names = selector.split('/')
    for name in names:
        path = search_by_name(path, name, max_depth, return_typ)
        if path is None:
            return
    return path


class FsfsLayer(object):

    # This maintains backwards compatability with construct 0.1.0
    # These tags should all be converted to folder when we make the switch
    _folder_tags = ['folder', 'collection', 'sequence', 'asset_type']
    _asset_tags = ['asset', 'shot']

    def __init__(self, api):
        self.api = api
        self.settings = api.settings

    def _get_projects(self, location, mount=None):
        if mount:
            root = self.api.get_mount(location, mount).as_posix()
            for entry in fsfs.search(root, levels=1).tags('project'):
                yield entry

        for mount in self.settings['locations'][location].keys():
            root = self.api.get_mount(location, mount).as_posix()
            results = fsfs.search(root, levels=1).tags('project')
            for entry in results:
                yield entry

    def get_projects(self, location, mount=None):
        for entry in self._get_projects(location, mount):
            yield entry.read()

    def get_project_by_id(self, _id, location=None, mount=None):

        first_location = location or self.settings['my_location']
        locations = sorted(
            self.settings['locations'].keys(),
            key=lambda location: int(location == first_location),
            reverse=True
        )
        for location in locations:
            for project in self._get_projects(location):
                if project.uuid == _id:
                    return project.read()

    def get_project(self, name, location, mount=None):
        if mount:
            root = self.api.get_mount(location, mount).as_posix()
            entry = fsfs.search(root, levels=1).name(name).one()
            if entry:
                return entry.read()
            return

        for mount in self.settings['locations'][location].keys():
            root = self.api.get_mount(location, mount).as_posix()
            entry = fsfs.search(root, levels=1).name(name).one()
            if entry:
                return entry.read()

    def new_project(self, name, location, mount, data):
        path = self.api.get_mount(location, mount) / name
        entry = fsfs.get_entry(path.as_posix())

        if entry.exists:
            raise OSError('Project already exists.')

        entry.tag('project')
        entry.write(**data)
        entry.uuid = data['_id']
        return entry.read()

    def update_project(self, project, data):

        path = self.get_path_to(project)
        entry = fsfs.get_entry(path.as_posix())

        if not entry.exists:
            raise OSError('Project does not exist.')

        entry.write(**data)
        entry.uuid = data['_id']
        return entry.read()

    def delete_project(self, project):

        path = self.get_path_to(project)
        entry = fsfs.get_entry(path.as_posix())
        entry.delete()

    def get_folders(self, parent):
        parent_path = self._get_parent_path(parent).as_posix()
        levels = 10 if parent['_type'] == 'project' else 1
        entries = fsfs.search(parent_path, levels=levels, skip_root=True)
        for entry in entries:
            if set(entry.tags).intersection(set(self._folder_tags)):
                yield entry.read()

    def get_folder(self, name, parent):
        prospect = None
        for folder in self.get_folders(parent):
            if name in folder['name']:
                prospect = folder
            if name == folder['name']:
                return folder
        return prospect

    def new_folder(self, name, parent, data):
        parent_path = self._get_parent_path(parent)
        folder_path = parent_path / name

        entry = fsfs.get_entry(folder_path.as_posix())
        entry.tag('folder')
        entry.write(**data)
        entry.uuid = data['_id']
        return entry.read()

    def update_folder(self, folder, data):

        path = self.get_path_to(folder)
        entry = fsfs.get_entry(path.as_posix())

        if not entry.exists:
            raise OSError('Folder does not exist.')

        entry.write(**data)
        entry.uuid = data['_id']
        return entry.read()

    def delete_folder(self, folder):

        path = self.get_path_to(folder)
        entry = fsfs.get_entry(path.as_posix())
        entry.delete()

    def get_assets(self, parent, asset_type=None):
        parent_path = self._get_parent_path(parent).as_posix()
        levels = 10 if parent['_type'] == 'project' else 1
        entries = fsfs.search(parent_path, levels=levels, skip_root=True)
        for entry in entries:
            if set(entry.tags).intersection(set(self._asset_tags)):
                if not asset_type or entry.read('asset_type') == asset_type:
                    yield entry.read()

    def get_asset(self, name, parent):
        prospect = None
        for asset in self.get_assets(parent):
            if name in asset['name']:
                prospect = asset
            if name == asset['name']:
                return asset
        return prospect

    def new_asset(self, name, parent, data):
        parent_path = self._get_parent_path(parent)
        asset_path = parent_path / name

        entry = fsfs.get_entry(asset_path.as_posix())
        entry.tag('asset')
        entry.write(**data)
        entry.uuid = data['_id']
        return entry.read()

    def update_asset(self, asset, data):
        path = self.get_path_to(asset)
        entry = fsfs.get_entry(path.as_posix())

        if not entry.exists:
            raise OSError('Asset does not exist.')

        entry.write(**data)
        entry.uuid = data['_id']
        return entry.read()

    def delete_asset(self, asset):
        path = self.get_path_to(asset)
        entry = fsfs.get_entry(path.as_posix())
        entry.delete()

    def get_tasks(self, asset):
        parent_path = self.get_path_to(asset).as_posix()
        entries = fsfs.search(parent_path, levels=1).tags('task')
        for entry in entries:
            yield entry.read()

    def get_task(self, name, asset):
        prospect = None
        for task in self.get_tasks(asset):
            if name in task['name']:
                prospect = task
            if name == task['name']:
                return asset
        return prospect

    def new_task(self, name, asset, data):
        parent_path = self.get_path_to(asset)
        task_path = parent_path / name

        entry = fsfs.get_entry(task_path.as_posix())
        entry.tag('task')
        entry.write(**data)
        entry.uuid = data['_id']
        return entry.read()

    def update_task(self, task, data):
        path = self.get_path_to(task)
        entry = fsfs.get_entry(path.as_posix())

        if not entry.exists:
            raise OSError('Task does not exist.')

        entry.write(**data)
        entry.uuid = data['_id']
        return entry.read()

    def delete_task(self, task):
        path = self.get_path_to(task)
        entry = fsfs.get_entry(path.as_posix())
        entry.delete()

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

    def get_parent(self, entity):
        project_id = entity.get('project_id', None)
        parent_id = entity.get('parent_id')

        if project_id:
            project = self.get_project_by_id(entity['project_id'])
            if project_id == parent_id:
                return project

            project_root = self.get_path_to(project)
            match = search_by_id(
                project_root,
                entity['parent_id'],
                return_typ=fsfs.get_entry
            )
            if match:
                return match.read()

    def get_children(self, entity):
        if entity['_type'] == 'project':
            return dict(folders=list(self.get_folders(entity)))

        if entity['_type'] == 'folder':
            return dict(
                folders=list(self.get_folders(entity)),
                assets=list(self.get_assets(entity))
            )

        if entity['_type'] == 'asset':
            return dict(
                tasks=list(self.get_tasks(entity))
            )

        if entity['_type'] == 'task':
            return dict(
                workfiles=list(self.get_workfiles(entity))
            )

    def _get_parent_path(self, parent):
        '''Get the path to a parent for creating new entities.'''

        parent_path = self.get_path_to(parent)
        if parent['_type'] == 'project':
            parent_path = parent_path / parent['tree']['folders']

        return parent_path

    def get_path_to(self, entity):
        '''Get a file system path to the provided entity.'''

        my_location = self.settings['my_location']

        if entity['_type'] == 'project':
            if my_location in entity['locations']:
                location = my_location
                mount = entity['locations'][location]
            else:
                location, mount = entity['locations'].items()[0]
            root = self.api.get_mount(location, mount)
            return root / entity['name']

        if 'project_id' in entity:
            project = self.get_project_by_id(entity['project_id'])
            project_path = self.get_path_to(project)
            folders_path = project_path / project['tree']['folders']
            match = search_by_id(folders_path, entity['_id'])
            if match:
                return match

        raise OSError('Could not find ' + entity['name'])
