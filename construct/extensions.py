# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import inspect
import logging
from collections import OrderedDict

# Third party imports
import entrypoints

# Local imports
from .constants import EXTENSIONS_ENTRY_POINT
from .utils import iter_modules


__all__ = [
    'Extension',
    'ExtensionManager',
    'Host',
    'is_extension_type',
    'is_extension',
]


_log = logging.getLogger(__name__)


class Extension(object):
    '''The Extension class allows users to extend Construct with their own
    behavior and functionality. When writing your own Extensions use the
    `setup` method instead of `__init__` to perform any setup your Extension
    requires like creating a database connection. The `load` method should be
    used to register event handlers and extend the base API. The `unload`
    method should be used to undo everything that was done in `load`.

    Extensions commonly do the following:

     - Emit custom events
     - Provide event handlers
     - Provide Methods and Objects to extend the base API

    Look at construct.builtins to see the Extensions that provide the core
    functionality of Construct.
    '''

    identifier = ''
    label = ''
    icon = ''

    def __init__(self, api=None):
        self.api = api

    def setup(self, api):
        '''Called by Construct prior to loading the extension. This is a good
        place to set up dependencies like database connections.
        '''

    def load(self, api):
        '''Called by Construct when loading the extension.

        This method should register event handlers and extend the base API.
        '''

    def unload(self, api):
        '''Called by Construct when unloading the extension.

        This method should undo everything that was done in `load`.
        '''

    def is_available(self, ctx):
        '''Return True if the Extension is available in the given context'''
        return True


class Host(Extension):
    '''An Extension providing a unified api to access the Host software that
    Construct is operating within like, Autodesk Maya or SideFX Houdini.
    The active Host Extension is bound to API.host.
    '''

    @property
    def version(self):
        '''Application version'''
        return NotImplemented

    def modified(self):
        '''Check if current file is modified'''
        return NotImplemented

    def save_file(self, file):
        '''Save a file'''
        return NotImplemented

    def open_file(self, file):
        '''Open a file'''
        return NotImplemented

    def get_selection(self):
        '''Get the host's selection'''
        return NotImplemented

    def set_selection(self, selection):
        '''Set the host's selection'''
        return NotImplemented

    def get_workspace(self):
        '''Get the host's workspace'''
        return NotImplemented

    def set_workspace(self, directory):
        '''Set the host's workspace'''
        return NotImplemented

    def get_filepath(self):
        '''Get the path to the host's current file'''
        return NotImplemented

    def get_filename(self):
        '''Get the name of the host's current file'''
        return NotImplemented

    def get_frame_rate(self):
        '''Get the frame rate of the host
        Returns:
            float - fps
        '''
        return NotImplemented

    def set_frame_rate(self, fps):
        '''Set the frame rate of the host
        Arguments:
            fps (float) - Frames per second
        '''
        return NotImplemented

    def get_frame_range(self):
        '''Get the frame range of the host
        Returns:
            [min_frame, start_frame, end_frame, max_frame]
        '''
        return NotImplemented

    def set_frame_range(self, min, start, end, max):
        '''Set the frame range of the host
        Arguments:
            min_frame (int): Min frame of timeline
            start_frame (int): Start frame of animation
            end_frame (int): End frame of animation
            max_frame (int): Max frame of timeline
        '''
        return NotImplemented

    def before_launch(self, api, software, env, ctx):
        '''Called before the Host is launched.

        Used to provision environment variables and setup a workspace.
        '''
        return NotImplemented

    def after_launch(self, api, ctx):
        '''Called after application is launched within the Host application.

        Implementations should do some of the following:

          - Register callbacks
          - Setup UI Menus
          - Setup Shelves
          - Setup UI Elements
          - Launch a dialog
        '''
        return NotImplemented

    def get_qt_parent(self):
        '''Get the host's main QT widget'''
        return NotImplemented

    def get_qt_app(self):
        from Qt import QtWidgets
        return QtWidgets.QApplication.instance()


EXTENSION_TYPES = (Extension, Host)


def is_extension_type(obj):
    '''Check if an obj is an Extension type.'''

    return (
        obj not in EXTENSION_TYPES and
        isinstance(obj, type) and
        issubclass(obj, EXTENSION_TYPES)
    )


def is_extension(obj):
    '''Check if an obj is an Extension instance.'''

    return isinstance(obj, EXTENSION_TYPES)


class ExtensionManager(OrderedDict):

    def __init__(self, api):
        super(ExtensionManager, self).__init__()
        self.api = api
        self.path = self.api.path
        self.settings = self.api.settings

    def load(self):
        '''Discover and load all Extensions'''

        for ext in self.discover():
            self.register(ext)

    def unload(self):
        '''Unload all Extensions'''

        for ext in self.values():
            _log.debug('Unloading extension: %s' % ext)
            ext.unload(self.api)

        self.clear()

    def register(self, ext):
        '''Register an Extension'''

        if self.loaded(ext):
            _log.error('Extension already loaded: %s' % ext)
            return

        _log.debug('Loading extension: %s' % ext)
        if is_extension_type(ext):
            inst = ext(self.api)
        elif is_extension(ext):
            inst = ext
        else:
            _log.error('Expected Extension type got %s' % ext)
            return

        try:
            inst.setup(self.api)
        except:
            _log.exception("Failed to setup extension: %s" % ext)
            return

        try:
            inst.load(self.api)
            self[ext.identifier] = inst
        except:
            _log.exception("Failed to load extension: %s" % ext)
            return

    def unregister(self, ext):
        '''Unregister an Extension'''

        identifier = getattr(ext, 'identifier', ext)
        inst = self.pop(identifier, None)
        _log.debug('Unloading extension: %s' % ext)
        try:
            inst.unload(self.api)
        except:
            _log.exception("Failed to unload extension: %s" % ext)
            return

    def loaded(self, ext):
        '''Check if an Extension has been loaded.'''

        identifier = getattr(ext, 'identifier', ext)
        return identifier in self

    def discover(self):
        '''Find and iterate over all Extension subclasses

        1. Yields Builtin Extensions
        2. Yields Extensions registered to construct.extensions entry_point
        2. Yields Extensions in python files in CONSTRUCT_PATH
        3. Yields Extensions in settings['extensions']
        '''

        from .ext import extensions
        for ext in extensions:
            yield ext

        from .hosts import extensions
        for ext in extensions:
            yield ext

        entry_points = entrypoints.get_group_all(EXTENSIONS_ENTRY_POINT)
        for entry_point in entry_points:
            obj = entry_point.load()
            for _, ext in inspect.getmembers(obj, is_extension_type):
                yield ext

        ext_paths = [p / 'extensions' for p in self.path]
        for mod in iter_modules(*ext_paths):
            for _, ext in inspect.getmembers(mod, is_extension_type):
                yield ext

        for module_path in self.settings.get('extensions', []):
            try:
                mod = __import__(module_path)
            except ImportError:
                _log.debug('Extension module does not exist: ' + module_path)
            for _, ext in inspect.getmembers(mod, is_extension_type):
                yield ext

    def ls(self, typ=None):
        '''Get a list of available extensions.

        Arguments:
            typ (Extension, Optional): List only a specific type of Extension.

        Examples:
            ls()  # lists all extensions
            ls(Host)  # list only Host extensions
        '''

        matches = []
        for ext in self.values():
            if not type or isinstance(ext, typ):
                matches.append(ext)
        return matches

    def get_available(self, ctx=None):
        '''Get extensions available in the provided context.'''

        ctx = ctx or self.api.context.copy()
        return [ext for ext in self.values() if ext.is_available(ctx)]
