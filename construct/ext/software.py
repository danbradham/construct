# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import logging
import os
import subprocess
import sys

# Local imports
from ..compat import basestring
from ..extensions import Extension
from ..utils import get_lib_path, update_dict, update_env


platform = sys.platform.rstrip('1234567890')
if platform == 'darwin':
    platform = 'mac'

_log = logging.getLogger(__name__)


class Software(Extension):

    identifier = 'software'
    label = 'Software Extension'

    def is_available(self, ctx):
        return ctx['project']

    def load(self, api):
        api.settings.add_section('software', 'software')
        api.extend('software', self)
        api.extend('launch', self.launch)
        api.extend('open_with', self.open_with)
        api.define(
            'before_launch',
            '(api, software, env, ctx): Called before application launch.'
        )
        api.define(
            'after_launch',
            '(api, ctx): Called after an application is launched.'
        )

    def unload(self, api):
        api.unextend('software')
        api.unextend('launch')
        api.unextend('open_with')

    @property
    def folder(self):
        return self.api.settings['software'].folder

    @property
    def software_settings(self):
        return self.api.settings['software']

    def __contains__(self, key):
        return key in self.software_settings

    def _get_project_software(self, project):
        if 'software' not in project:
            project = self.api.io.get_project_by_id(project['_id'])
        return project.get('software', {})

    def _available_software(self, software, ext=None):
        available = {}
        for software_name, software in software.items():
            if ext and ext not in software['extensions']:
                continue
            available[software_name] = software
        return available

    def get_by_name(self, name, project=None, file=None):
        try:
            return self.get(project, file)[name]
        except KeyError:
            raise NameError('Could not find software named ' + name)

    def get(self, project=None, file=None):
        '''Get the available software.

        If a project is provided get only software available in that project.

        If there is a project in the current context only return software in the
        project's "software" dict. If a file is provided only return software
        that can handle the file's extension.

        If a file is provided, only return software that can open that file.
        '''

        ext = None
        ctx = self.api.get_context()
        project = project or ctx['project']

        if file:
            ext = os.path.splitext(file)[-1]

        if project:
            if isinstance(project, basestring):
                project = self.api.io.get_project(name=project)
            software = self._get_project_software(project)
            return self._available_software(software, ext)

        return self._available_software(self.software_settings, ext)

    def save(self, name, data, project=None):
        '''Save software to settings or a project.'''

        if project:
            software = self._get_project_software(project)
            software[name] = self.software_settings.validate(data)
            self.api.io.update_project(project, {'software': software})
            return software[name]

        return self.software_settings.write(name, data)

    def update(self, name, data, project=None):
        '''Update software stored in settings or a project.'''

        if project:
            # Get updated project software
            software = self._get_project_software(project)
            software_data = software.get(name, {})

            # Update software data
            update_dict(software_data, data)

            # Validate software data
            software_data = self.software_settings.validate(software_data)
            software[name] = software_data

            # Update project with software
            self.api.io.update_project(project, {'software': software})
            return software[name]

        software_data = self.software_settings.get(name, {})
        update_dict(software_data, data)
        self.software_settings.write(name, software_data)
        return software_data

    def delete(self, name, project=None):
        '''Delete software by name from settings or a project.'''

        if project:
            software = self._get_project_software(project)
            if name not in software:
                return
            software.pop(name)
            self.api.io.update_project(project, {'software': software})

        self.software_settings.delete(name)

    def launch(self, name, *args, **kwargs):
        '''Launch the specified software.

        Arguments:
            name (str): Name of software to launch
            args: Arguments to pass to software executable
            context: Context to launch software in
        '''

        software = self.get_by_name(name)
        cmd = _get_command(software)

        ctx = kwargs.pop('context', self.api.context).copy()
        args = list(args or software['args'])
        cmd = [cmd] + args
        env = _get_software_env(software, ctx, self.api.path)

        # Let Host Extension add to the environment
        host = self.api.extensions.get(software['host'], None)
        if host:
            _log.debug('Executing before_launch: %s' % host)
            host.before_launch(self.api, software, env, ctx)
        else:
            _log.debug(
                'Skipping before_launch...'
                '%s has no registered ext.' % software['host']
            )

        self.api.send('before_launch', self.api, software, env, ctx)
        _log.debug('Launching %s' % name.title())
        _run(cmd, env=env)

    def open_with(self, name, file, *args, **kwargs):
        '''Open a file with the specified software.

        Arguments:
            name (str): Name of software to launch
            file (str): File to open with software
            *args: Arguments to pass to software executable
        '''

        software = self.get_by_name(name)
        cmd = _get_command(software)

        ext = os.path.splitext(file)[-1]
        if ext not in software['extensions']:
            raise OSError('Can not open %s with %s' % (name, file))

        ctx = kwargs.pop('context', self.api.context).copy()
        ctx['file'] = file
        args = list(args or software['args'])
        cmd = [cmd] + args + [file]
        env = _get_software_env(software, ctx, self.api.path)

        # Let Host Extension add to the environment
        host = self.api.extensions.get(software['host'], None)
        if host:
            _log.debug('Executing before_launch: %s' % host)
            host.before_launch(self.api, software, env, ctx)
        else:
            _log.debug(
                'Skipping before_launch...'
                '%s has no registered ext.' % software['host']
            )

        self.api.send('before_launch', self.api, software, env, ctx)
        _log.debug('Launching %s' % name.title())
        _run(cmd, env=env)


def _get_command(software):
    '''Get the platform specific command used to launch the software.'''

    cmd = software['cmd'].get(platform, None)
    if isinstance(cmd, basestring):
        if os.path.isfile(cmd):
            return cmd
    for item in cmd:
        if os.path.isfile(item):
            return item
    raise OSError(
        "Could not find executable for %s. Are you sure it's installed?"
        % software['name']
    )


def _get_software_env(software, ctx, path):
    '''Get the environment for the specified software.'''

    env = os.environ.copy()
    update_env(env, **ctx.to_envvars())
    update_env(env, **software['env'])
    update_env(
        env,
        CONSTRUCT_PATH=os.pathsep.join([str(p) for p in path]),
        CONSTRUCT_HOST=software['host'],
        PYTHONPATH=[get_lib_path().as_posix()]
    )
    return env


def _run(*args, **kwargs):
    '''On Windows start a detached process in it's own process group.'''

    if platform == 'win':
        create_new_process_group = 0x00000200
        detached_process = 0x00000008
        creation_flags = detached_process | create_new_process_group
        kwargs.setdefault('creationflags', creation_flags)

    kwargs.setdefault('shell', True)
    subprocess.Popen(*args, **kwargs)
