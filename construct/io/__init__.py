# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
from copy import deepcopy

# Local imports
from ..errors import ValidationError
from .fsfslayer import FsfsLayer


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
            'before_new_bin',
            '(api, bin): Sent before a bin is created.'
        )
        self.api.define(
            'after_new_bin',
            '(api, bin): Sent after a bin is created.'
        )
        self.api.define(
            'before_update_bin',
            '(api, bin, update): Sent before a bin is updated.'
        )
        self.api.define(
            'after_update_bin',
            '(api, bin): Set after a bin is updated.'
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

        location = location or self.api.context['location']
        mount = mount or self.api.context['mount']

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

        location = location or self.api.context['location']
        mount = mount or self.api.context['mount']

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

        location = location or self.api.context['location']
        mount = mount or self.api.context['mount']

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

        # Update and validate data
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

    def get_assets(self, project, bin=None, asset_type=None, group=None):
        '''Get all the assets in the specified project.

        Arguments:
            project (dict): Project dict including _id
            bin (str): Optional bin filter
            asset_type (str): Optional asset_type filter
            group (str): Optional group filter

        Returns:
            Generator or cursor yielding assets
        '''

        return self.fsfs.get_assets(project, bin, asset_type, group)

    def get_asset(self, project, name):
        '''Get one asset that matches the given name.

        Arguments:
            project (dict): Project dict including _id
            name (str): Partial name of asset.

        Returns:
            Asset dict or None
        '''

        return self.fsfs.get_asset(project, name)

    def new_asset(self, project, name, bin, asset_type, data=None):
        '''Create a new asset in the specified project.

        Events:
            before_new_asset: Sent with api and asset data
            after_new_asset: Sent with api and result asset data

        Arguments:
            project (dict): Project dict including _id
            name (str): Full name of new asset.
            bin (str): Name of project bin
            asset_type (str): Type of asset (asset, shot, etc.)

        Returns:
            New asset dict.
        '''

        assert '_id' in project, 'project dict must include _id'
        assert project['_type'] == 'project', 'project _type must be "project"'

        # Retrieve existing assets
        project = self.get_project_by_id(project['_id'])
        assets = project.get('assets', {})

        if name in assets:
            raise OSError('Asset already exists: %s' % name)

        # Prepare data
        data = data or {}
        data['name'] = name
        data['bin'] = bin
        data['asset_type'] = asset_type
        data['project_id'] = project['_id']

        self.api.send('before_new_asset', self.api, data)

        # Validate data
        v = self.api.schemas.get_validator('asset', allow_unknown=True)
        data = v.validated(data)
        if not data:
            raise ValidationError(
                'Invalid asset data: %s' % v.errors,
                errors=v.errors
            )

        # Create our new asset
        result = self.fsfs.new_asset(project, data)

        self.api.send('after_new_asset', self.api, result)

        assets[result['name']] = {
            k: result[k]
            for k in ['_id', 'name', 'bin', 'asset_type', 'group']
        }
        self.update_project(project, {'assets': assets})

        return result

    def update_asset(self, asset, data):
        '''Update an asset's data.

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

        # Update and validate data
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
        '''Delete an asset.

        .. warning:: This does not delete your asset data on the file system.
        It simply removes metadata. You are in charge of deleting on your
        file system.
        '''

        return self.fsfs.delete_asset(asset)

    def get_bins(self, project):
        if 'bins' not in project:
            project = self.get_project_by_id(project['_id'])

        return project.get('bins', {})

    def get_bin(self, project, name):
        if 'bins' not in project:
            project = self.get_project_by_id(project['_id'])

        return project['bins'][name]

    def new_bin(self, project, name, data=None):

        # Retrieve existing project bins
        project = self.get_project_by_id(project['_id'])
        bins = project.get('bins', {})

        # Prepare data
        data = data or {}
        data['name'] = name
        data.setdefault('order', len(bins))
        data.setdefault('icon', '')

        # Update project with new bin
        bins[name] = data
        updated = self.update_project(project, {'bins': bins})

        return updated['bins'][name]

    def update_bin(self, project, name, data):

        # Retrieve existing project bins
        project = self.get_project_by_id(project['_id'])
        bins = project.get('bins', {})

        new_data = bins.pop(name)
        new_data.update(data)

        # Update project with new bins
        bins[new_data['name']] = new_data
        updated = self.update_project(project, {'bins': bins})

        return updated['bins'][new_data['name']]

    def delete_bin(self, project, name):

        # Retrieve existing project bins
        project = self.get_project_by_id(project['_id'])
        bins = project.get('bins', {})

        self.update_project(project, {'bins': bins})

    def get_asset_types(self, project):
        if 'asset_types' not in project:
            project = self.get_project_by_id(project['_id'])

        return project.get('asset_types', {})

    def get_asset_type(self, project, name):
        if 'asset_types' not in project:
            project = self.get_project_by_id(project['_id'])

        return project['asset_types'][name]

    def new_asset_type(self, project, name, data=None):

        # Retrieve existing project asset_types
        project = self.get_project_by_id(project['_id'])
        asset_types = project.get('asset_types', {})

        # Prepare data
        data = data or {}
        data['name'] = name
        data.setdefault('order', len(asset_types))
        data.setdefault('icon', '')

        # Update project with new asset_type
        asset_types[name] = data
        updated = self.update_project(project, {'asset_types': asset_types})

        return updated['asset_types'][name]

    def update_asset_type(self, project, name, data):

        # Retrieve existing project asset_types
        project = self.get_project_by_id(project['_id'])
        asset_types = project.get('asset_types', {})

        new_data = asset_types.pop(name)
        new_data.update(data)

        # Update project with new asset_types
        asset_types[new_data['name']] = new_data
        updated = self.update_project(project, {'asset_types': asset_types})

        return updated['asset_types'][new_data['name']]

    def delete_asset_type(self, project, name):

        # Retrieve existing project asset_types
        project = self.get_project_by_id(project['_id'])
        asset_types = project.get('asset_types', {})

        self.update_project(project, {'asset_types': asset_types})

    def get_task_types(self, project):
        if 'task_types' not in project:
            project = self.get_project_by_id(project['_id'])

        return project.get('task_types', {})

    def get_task_type(self, project, name):
        if 'task_types' not in project:
            project = self.get_project_by_id(project['_id'])

        return project['task_types'][name]

    def new_task_type(self, project, name, short, data=None):

        # Retrieve existing project task_types
        project = self.get_project_by_id(project['_id'])
        task_types = project.get('task_types', {})

        # Prepare data
        data = data or {}
        data['name'] = name
        data['short'] = short
        data.setdefault('order', len(task_types))
        data.setdefault('icon', '')

        # Update project with new task_type
        task_types[name] = data
        updated = self.update_project(project, {'task_types': task_types})

        return updated['task_types'][name]

    def update_task_type(self, project, name, data):

        # Retrieve existing project task_types
        project = self.get_project_by_id(project['_id'])
        task_types = project.get('task_types', {})

        new_data = task_types.pop(name)
        new_data.update(data)

        # Update project with new task_types
        task_types[new_data['name']] = new_data
        updated = self.update_project(project, {'task_types': task_types})

        return updated['task_types'][new_data['name']]

    def delete_task_type(self, project, name):

        # Retrieve existing project task_types
        project = self.get_project_by_id(project['_id'])
        task_types = project.get('task_types', {})

        self.update_project(project, {'task_types': task_types})

    def get_path_to(self, entity):
        '''Get a file system path to the provided entity.

        Arguments:
            entity (dict): Data dict including (_type, _id, name, etc.)

        Returns:
            pathlib.Path
        '''

        return self.fsfs.get_path_to(entity)
