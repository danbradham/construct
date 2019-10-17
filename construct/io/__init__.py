# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
from copy import deepcopy

# Local imports
from ..errors import ValidationError
from .fsfs import FsfsLayer


# from .mongo import MongoLayer


class IO(object):

    def __init__(self, api):
        self.api = api
        self.settings = self.api.settings
        self.fsfs = FsfsLayer(api)

    def load(self):
        self.api.define(
            'before_new_project',
            '(api, project): Sent before a project is created.'
        )
        self.api.define(
            'after_new_project',
            '(api, project): Sent after a project is created.'
        )
        self.api.define(
            'before_update_project',
            '(api, project, update): Sent before a project is updated.'
        )
        self.api.define(
            'after_update_project',
            '(api, project): Set after a project is updated.'
        )
        self.api.define(
            'before_new_folder',
            '(api, folder): Sent before a folder is created.'
        )
        self.api.define(
            'after_new_folder',
            '(api, folder): Sent after a folder is created.'
        )
        self.api.define(
            'before_update_folder',
            '(api, folder, update): Sent before a folder is updated.'
        )
        self.api.define(
            'after_update_folder',
            '(api, folder): Set after a folder is updated.'
        )

    def unload(self):
        self.api.undefine('before_new_project')
        self.api.undefine('after_new_project')
        self.api.undefine('before_update_project')
        self.api.undefine('after_update_project')
        self.api.undefine('before_new_folder')
        self.api.undefine('after_new_folder')
        self.api.undefine('before_update_folder')
        self.api.undefine('after_update_folder')

    def get_projects(self, location=None, mount=None):
        '''Get a list of projects in a location and mount. If no mount is
        provided list projects in all mounts of the given location.

        .. note:: Locations and mounts are configured in your construct.yaml

        Arguments:
            location (str): Location of projects. Default: my_location setting
            mount (str): Mount project resides in. Optional.

        Returns:
            Generator or cursor yielding projects
        '''

        location = location or self.settings['my_location']
        return self.fsfs.get_projects(location, mount)

    def get_project_by_id(self, _id, location=None, mount=None):
        '''Get one project that matches the given name. You can specify a
        location and mount to narrow the search.

        .. note:: Locations and mounts are configured in your construct.yaml

        Arguments:
            _id (str): Project id
            location (str): Location of projects. Default: my_location setting
            mount (str): Mount project resides in. Optional.

        Returns:
            Project dict or None
        '''

        return self.fsfs.get_project_by_id(_id, location, mount)

    def get_project(self, name, location=None, mount=None):
        '''Get one project that matches the given name. You can specify a
        location and mount to narrow the search.

        .. note:: Locations and mounts are configured in your construct.yaml

        Arguments:
            name (str): Partial name of project.
            location (str): Location of projects. Default: my_location setting
            mount (str): Mount project resides in. Optional.

        Returns:
            Project dict or None
        '''

        location = location or self.settings['my_location']
        return self.fsfs.get_project(name, location, mount)

    def new_project(self, name, location, mount, data=None):
        '''Create a new project in the specified location and mount.

        .. note:: Locations and mounts are configured in your construct.yaml

        Events:
            before_new_project: Sent with api and project data
            after_new_project: Sent with api and result project data

        Arguments:
            name (str): Full name of new project.
            location (str): Location of new project.
            mount (str): Mount within the specified location.

        Returns:
            New Project dict.
        '''

        # Prepare data
        data = data or {}
        data.setdefault('name', name)
        data.setdefault('locations', {location: mount})

        self.api.send('before_new_project', self.api, data)

        # Validate data
        v = self.api.schemas.get_validator('project', allow_unknown=True)
        data = v.validated(data)
        if not data:
            raise ValidationError(
                'Invalid project data: %s' % v.errors,
                errors=v.errors
            )

        # Create our new project
        result = self.fsfs.new_project(name, location, mount, data)

        self.api.send('after_new_project', self.api, result)
        return result

    def update_project(self, project, data):
        '''Update a project's data.

        Events:
            before_update_project: Sent with api, project, and update
            after_update_project: Sent with api, updated project

        Arguments:
            project (dict): Project data containing at least a name
            data (dict): Data to update

        Returns:
            Updated project data.
        '''

        self.api.send('before_update_project', self.api, project, data)


        #Update and validate data
        updated = deepcopy(project)
        updated.update(data)

        v = self.api.schemas.get_validator('project', allow_unknown=True)
        updated = v.validated(updated, update=True)
        if not updated:
            raise ValidationError(
                'Invalid project data: %s' % v.errors,
                errors=v.errors
            )

        # Update our project
        result = self.fsfs.update_project(project, updated)
        self.api.send('after_update_project', self.api, result)
        return result

    def delete_project(self, project):
        '''Delete a project.

        .. warning:: This does not delete your project data on the file system.
        It simply removes metadata. You are in charge of deleting on your
        file system.
        '''

        return self.fsfs.delete_project(project)

    def get_folders(self, parent):
        '''Get all the folders in the specified parent.

        Arguments:
            parent (dict): Project or Folder dict

        Returns:
            Generator or cursor yielding folders
        '''

        return self.fsfs.get_folders(parent)

    def get_folder(self, name, parent):
        '''Get one folder that matches the given name.

        Arguments:
            name (str): Partial name of folder.
            parent (dict): Project or Folder dict

        Returns:
            Folder dict or None
        '''

        return self.fsfs.get_folder(name, parent)

    def new_folder(self, name, parent, data=None):
        '''Create a new folder in the specified parent.

        Events:
            before_new_folder: Sent with api and folder data
            after_new_folder: Sent with api and result folder data

        Arguments:
            name (str): Full name of new folder.
            parent (dict): Project or Folder dict.

        Returns:
            New Folder dict.
        '''

        # TODO: Use a better error here.
        assert parent['_type'] in ['project', 'folder'], 'Parent must be a project or folder.'

        # Prepare data
        data = data or {}
        data.setdefault('name', name)
        data.setdefault('parent_id', parent['_id'])
        if parent['_type'] == 'project':
            data['project_id'] = parent['_id']
        else:
            data['project_id'] = parent['project_id']

        self.api.send('before_new_folder', self.api, data)

        # Validate data
        v = self.api.schemas.get_validator('folder', allow_unknown=True)
        data = v.validated(data)
        if not data:
            raise ValidationError(
                'Invalid folder data: %s' % v.errors,
                errors=v.errors
            )

        # Create our new project
        result = self.fsfs.new_folder(name, parent, data)

        self.api.send('after_new_folder', self.api, result)
        return result

    def update_folder(self, folder, data):
        '''Update a folder's data.

        Events:
            before_update_folder: Sent with api, folder, and update
            after_update_folder: Sent with api, updated folder

        Arguments:
            folder (dict): Folder data containing at least a name
            data (dict): Data to update

        Returns:
            Updated folder data.
        '''

        self.api.send('before_update_folder', self.api, folder, data)

        #Update and validate data
        updated = deepcopy(folder)
        updated.update(data)

        v = self.api.schemas.get_validator('folder', allow_unknown=True)
        updated = v.validated(updated, update=True)
        if not updated:
            raise ValidationError(
                'Invalid folder data: %s' % v.errors,
                errors=v.errors
            )

        # Update our project
        result = self.fsfs.update_folder(folder, updated)
        self.api.send('after_update_folder', self.api, result)
        return result

    def delete_folder(self, folder):
        '''Delete a folder.

        .. warning:: This does not delete your folder data on the file system.
        It simply removes metadata. You are in charge of deleting on your
        file system.
        '''

        return self.fsfs.delete_folder(folder)

    def get_assets(self, parent, asset_type=None):
        '''Get all the assets in the specified parent.

        Arguments:
            parent (dict): Project or asset dict
            asset_type (str): Optional asset_type filter

        Returns:
            Generator or cursor yielding assets
        '''

        return self.fsfs.get_assets(parent, asset_type)

    def get_asset(self, name, parent):
        '''Get one asset that matches the given name.

        Arguments:
            name (str): Partial name of asset.
            parent (dict): Project or Asset dict

        Returns:
            Asset dict or None
        '''

        return self.fsfs.get_asset(name, parent)

    def new_asset(self, name, asset_type, parent, data=None):
        '''Create a new asset in the specified parent.

        Events:
            before_new_asset: Sent with api and asset data
            after_new_asset: Sent with api and result asset data

        Arguments:
            name (str): Full name of new asset.
            asset_type (str): Type of asset (asset, shot, etc.)
            parent (dict): Project or asset dict.

        Returns:
            New asset dict.
        '''

        # TODO: Use a better error here.
        assert parent['_type'] in ['project', 'folder'], 'Parent must be a project or folder.'

        # Prepare data
        data = data or {}
        data.setdefault('name', name)
        data.setdefault('asset_type', asset_type)
        data.setdefault('parent_id', parent['_id'])
        if parent['_type'] == 'project':
            data['project_id'] = parent['_id']
        else:
            data['project_id'] = parent['project_id']

        self.api.send('before_new_asset', self.api, data)

        # Validate data
        v = self.api.schemas.get_validator('asset', allow_unknown=True)
        data = v.validated(data)
        if not data:
            raise ValidationError(
                'Invalid asset data: %s' % v.errors,
                errors=v.errors
            )

        # Create our new project
        result = self.fsfs.new_asset(name, parent, data)

        self.api.send('after_new_asset', self.api, result)
        return result

    def update_asset(self, asset, data):
        '''Update a asset's data.

        Events:
            before_update_asset: Sent with api, asset, and update
            after_update_asset: Sent with api, updated asset

        Arguments:
            asset (dict): asset data containing at least a name
            data (dict): Data to update

        Returns:
            Updated asset data.
        '''

        self.api.send('before_update_asset', self.api, asset, data)

        #Update and validate data
        updated = deepcopy(asset)
        updated.update(data)

        v = self.api.schemas.get_validator('asset', allow_unknown=True)
        updated = v.validated(updated, update=True)
        if not updated:
            raise ValidationError(
                'Invalid asset data: %s' % v.errors,
                errors=v.errors
            )

        # Update our project
        result = self.fsfs.update_asset(asset, updated)
        self.api.send('after_update_asset', self.api, result)
        return result

    def delete_asset(self, asset):
        '''Delete a asset.

        .. warning:: This does not delete your asset data on the file system.
        It simply removes metadata. You are in charge of deleting on your
        file system.
        '''

        return self.fsfs.delete_asset(asset)

    def get_tasks(self, parent):
        '''Get all the tasks in the specified asset.

        Arguments:
            parent (dict): Asset dict

        Returns:
            Generator or cursor yielding tasks
        '''

        return self.fsfs.get_tasks(parent)

    def get_task(self, name, parent):
        '''Get one task that matches the given name.

        Arguments:
            name (str): Partial name of task.
            parent (dict): Asset dict

        Returns:
            Task dict or None
        '''

        return self.fsfs.get_task(name, parent)

    def new_task(self, name, parent, data=None):
        '''Create a new task in the specified parent.

        Events:
            before_new_task: Sent with api and task data
            after_new_task: Sent with api and result task data

        Arguments:
            name (str): Full name of new task.
            parent (dict): Asset dict

        Returns:
            New task dict.
        '''

        # TODO: Use a better error here.
        assert parent['_type'] == 'asset', 'Parent must be an Asset.'

        # Prepare data
        data = data or {}
        data.setdefault('name', name)
        data.setdefault('parent_id', parent['_id'])
        if parent['_type'] == 'project':
            data['project_id'] = parent['_id']
        else:
            data['project_id'] = parent['project_id']

        self.api.send('before_new_task', self.api, data)

        # Validate data
        v = self.api.schemas.get_validator('task', allow_unknown=True)
        data = v.validated(data)
        if not data:
            raise ValidationError(
                'Invalid task data: %s' % v.errors,
                errors=v.errors
            )

        # Create our new project
        result = self.fsfs.new_task(name, parent, data)

        self.api.send('after_new_task', self.api, result)
        return result

    def update_task(self, task, data):
        '''Update a task's data.

        Events:
            before_update_task: Sent with api, task, and update
            after_update_task: Sent with api, updated task

        Arguments:
            task (dict): task data containing at least a name
            data (dict): Data to update

        Returns:
            Updated task data.
        '''

        self.api.send('before_update_task', self.api, task, data)

        #Update and validate data
        updated = deepcopy(task)
        updated.update(data)

        v = self.api.schemas.get_validator('task', allow_unknown=True)
        updated = v.validated(updated, update=True)
        if not updated:
            raise ValidationError(
                'Invalid task data: %s' % v.errors,
                errors=v.errors
            )

        # Update our project
        result = self.fsfs.update_task(task, updated)
        self.api.send('after_update_task', self.api, result)
        return result

    def delete_task(self, task):
        '''Delete a task.

        .. warning:: This does not delete your task data on the file system.
        It simply removes metadata. You are in charge of deleting on your
        file system.
        '''

        return self.fsfs.delete_task(task)

    def get_parent(self, entity):
        '''Get the parent of an entity.

        Arguments:
            entity (dict): Data dict including (_type, _id, name, etc.)

        Returns:
            dict: Parent entity
        '''

        return self.fsfs.get_parent(entity)

    def get_children(self, entity):
        '''Get the children of an entity.

        Arguments:
            entity (dict): Data dict including (_type, _id, name, etc.)

        Returns:
            dict containing children by type
        '''

        return self.fsfs.get_children(entity)

    def get_path_to(self, entity):
        '''Get a file system path to the provided entity.

        Arguments:
            entity (dict): Data dict including (_type, _id, name, etc.)

        Returns:
            pathlib.Path
        '''

        return self.fsfs.get_path_to(entity)
