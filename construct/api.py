# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import atexit
import inspect
import logging
from logging.config import dictConfig

# Local imports
from . import migrations, schemas
from .compat import Mapping, basestring, wraps, zip_longest
from .constants import DEFAULT_LOGGING
from .context import Context, validate_context
from .errors import ContextError
from .events import EventManager
from .extensions import ExtensionManager
from .io import IO
from .path import Path
from .settings import Settings
from .ui.manager import UIManager
from .utils import ensure_exists, unipath, yaml_dump


__all__ = ['API']

_log = logging.getLogger(__name__)
_cache = {}


def _on_exit():
    for api in list(_cache.values()):
        api.uninit()
    _cache.clear()


atexit.register(_on_exit)


class API(object):
    '''The API object is the central object in Construct. When initialized
    the API does the following.

    1. Sends the before_setup event
    2. Initializes a search path from CONSTRUCT_PATH
    3. Loads settings from a construct.yaml file found in the search path
    4. Discovers and loads Extensions
    5. Loads an initial Context from your environment
    6. Sends the after_setup event

    Usually API objects are constructed using the API function available
    in the construct module.

    >>> import construct
    >>> api = construct.API()

    Arguments:
        name (str): Name of the API
        path (list): A list of search paths. Defaults to:
            CONSTRUCT_PATH + ['~/.construct']
        logging: (dict): Logging configuration. Defaults to:
            construct.constants.DEFAULT_LOGGING

    Attributes:
        name: Name of this API object.
        path: :class:`construct.path.Path` object used for finding resources
            and settings files.
        settings: :class:`construct.settings.Settings` object used to access
            and manipulate settings values.
        extensions: :class:`construct.extensions.ExtensionManager` object used
            to discover and register :class:`construct.extensions.Extension` s.
        context: Access to the current :class:`construct.Context`.
        schemas: Access to :mod:`construct.schemas` used for data validation
            and normalization.
    '''

    def __init__(self, name=None, **kwargs):
        self.name = name
        self.events = EventManager()
        self.initialized = False
        self.path = Path(kwargs.pop('path', None))
        self.settings = Settings(self.path)
        self.extensions = ExtensionManager(self)
        self.context = Context()
        self.schemas = schemas
        self.migrations = migrations
        self.io = IO(self)
        self.ui = UIManager(self)
        self._logging_dict = kwargs.pop('logging', None)
        self._registered_members = {}
        self.init()

    def _setup_logging(self):
        if self._logging_dict is not None:
            dictConfig(self._logging_dict)
        else:
            dictConfig(self.settings.get('logging', DEFAULT_LOGGING))

    def init(self):

        _log.debug('Hi!')
        if self.initialized:
            _log.error('Construct is already initialized...')
            return

        self._setup_logging()

        _log.debug('Loading events...')
        self.events.load()

        self.events.send('before_setup', self)

        _log.debug('Loading path...')
        self.path.load()

        _log.debug('Loading settings...')
        self.settings.load()

        _log.debug('Loading IO...')
        self.io.load()

        _log.debug('Loading UI...')
        self.ui.load()

        _log.debug('Configuring logging...')
        self._setup_logging()

        _log.debug('Loading extensions...')
        self.extensions.load()

        _log.debug('Loading context...')
        self.context.load(
            location=self.settings['my_location'],
            mount=self.settings['my_mount'],
        )

        self.initialized = True
        _log.debug('Done initializing.')

        self.events.send('after_setup', self)

    def uninit(self):

        if not self.initialized:
            _log.debug('Construct is not initialized...')
            return

        self.events.send('before_close', self)

        _log.debug('Unloading path...')
        self.path.unload()

        _log.debug('Unloading UI...')
        self.ui.unload()

        _log.debug('Unloading IO...')
        self.io.unload()

        _log.debug('Unloading settings...')
        self.settings.unload()

        _log.debug('Unloading context...')
        self.context.unload()

        _log.debug('Unloading extensions...')
        self.extensions.unload()

        self.events.send('after_close', self)

        _log.debug('Unloading events...')
        self.events.unload()

        _cache.pop(self.name, None)
        self.initialized = False
        _log.debug('Done uninitializing.')
        _log.debug('Goodbye!')

    def get_context(self):
        '''Get a copy of the current context.

        .. seealso:: :class:`construct.context.Context.copy`
        '''

        return self.context.copy()

    def set_context(self, ctx):
        '''Set the current context.

        Examples:
            Set the active context permanently::

                >>> new_ctx = api.get_context()
                >>> new_ctx['project'] = 'A_PROJECT'
                >>> api.set_context(new_context)

            Temporarily set context::

                >>> with api.set_context(new_ctx):
                ...     # Do something while ctx is new_ctx

        Arguments:
            ctx (Context) - Sets api.
        '''

        _api = self
        _ctx = self.context
        self.context = ctx

        class _AsContextManager(object):

            def __enter__(self):
                pass

            def __exit__(self, *args):
                _api.context = _ctx

        return _AsContextManager()

    def update_context(self, **data):
        '''Update the current context.

        Arguments:
            **data - Context keys and values.
        '''

        self.context.update(data)

    def set_context_from_path(self, path):
        '''Set the current api context using a file or directory path.'''

        self.context = self.context_from_path(path)

    def _context_from_obj(self, obj, data):
        if obj['_type'] == 'project':
            data['project'] = obj['name']
            project = self.io.get_project_by_id(obj['_id'])
            project_path = self.io.get_path_to(project)
            location, mount = self.get_mount_from_path(project_path)
            data['location'] = location
            data['mount'] = mount
        elif obj['type'] == 'asset':
            data['asset'] = obj['name']
            data['bin'] = obj['bin']
            project = self.io.get_project_by_id(obj['project_id'])
            self._context_from_obj(project, data)

    def context_from_obj(self, obj, data=None):
        '''Returns a Context instance from the specific data obj.

        Arguments:
            obj (dict) - Project or asset data.
        '''

        data = {}
        self._context_from_obj(obj, data)

        context = Context(
            host=self.context['host'],
            location=self.context['location'],
            mount=self.context['mount'],
            **data
        )
        return context

    def validate_context(self, context):
        '''Returns True if the context is valid.'''

        return validate_context(self, context)

    def context_from_path(self, path):

        ctx = Context(host=self.context['host'])

        path = unipath(path)
        if path.is_file():
            ctx['file'] = path.as_posix()

        location_mount = self.get_mount_from_path(path)
        if location_mount:
            ctx.update(location=location_mount[0], mount=location_mount[1])
        else:
            raise ContextError(
                'Failed to extract context from path. '
                'Path does not appear to match your configured locations.'
            )

        # TODO: Extract remaining context from path

        return ctx

    def context_from_uri(self, uri):
        '''Create a Context object from an uri.

        Examples:

            >>> api.context_from_uri('cons://local/projects/project')
            {'location': 'local', 'mount': 'projects', 'project': 'project'}

            >>> api.context_from_uri('local/projects/project')
            {'location': 'local', 'mount': 'projects', 'project': 'project'}
        '''

        # Split off uri_prefix
        uri_prefix = None
        if '://' in uri:
            uri_prefix, uri = uri.split('://', 1)
            uri_prefix += '://'

        uri_parts = uri.strip(' /\\').split('/')
        uri_parts_map = [
            'location',
            'mount',
            'project',
            'bin',
            'asset',
            'workspace',
            'task',
            'file',
        ]

        context = Context(
            host=self.context['host'],  # Inject host from current context
        )
        for key, value in zip_longest(uri_parts_map, uri_parts):
            context[key] = value
        return context

    def uri_from_context(self, context):
        '''Create a Context object from an uri.

        Examples:

            >>> ctx = Context(
            ...     location='local',
            ...     mount='projects',
            ...     project='project'
            ... )
            >>> api.uri_from_context(ctx)
            'cons://local/projects/project'
        '''

        uri_parts = []
        uri_parts_map = [
            'location',
            'mount',
            'project',
            'bin',
            'asset',
            'task',
            'workspace',
            'file',
        ]
        for key in uri_parts_map:
            value = context.get(key, None)
            if value:
                uri_parts.append(value)
        return 'cons://' + '/'.join(uri_parts)

    def set_mount(self, location, mount):
        self.update_context(location=location, mount=mount)

    def get_mount(self, location=None, mount=None):
        '''Get a file system path to a mount. Uses the current context location
        and mount if they are not provided.

        Arguments:
            location (str): Name of location or context['location']
            mount (str): Name of mount or context['mount']
        '''

        location = location or self.context['location']
        mount = mount or self.context['mount']
        path = self.settings['locations'][location][mount]
        if isinstance(path, dict):
            path = path[self.context['platform']]
            ensure_exists(path)
            return unipath(path)
        else:
            ensure_exists(path)
            return unipath(path)

    def get_mount_from_path(self, path):
        '''Get the location and mount from a file path'''

        path = unipath(path)

        for location, mounts in self.settings['locations'].items():
            for mount, mount_path in mounts.items():
                if unipath(mount_path) in path.parents:
                    return location, mount

    def get_locations(self):
        '''Get locations from settings.'''

        return self.settings['locations']

    @property
    def host(self):
        '''Get the active Host Extension.'''

        return self.extensions.get(self.context['host'], None)

    def define(self, event, doc):
        '''Define a new event

        Arguments:
            event (str): Name of the event
            doc (str): Documentation for event
        '''

        self.events.define(event, doc)

    def undefine(self, event):
        '''Undefine an event

        Arguments:
            event (str): Name of the event
        '''

        self.events.undefine(event)

    def on(self, *args):
        '''Adds a handler to the specified event. Can be used as a decorator.

        Examples:
            >>> api.on('greet', lambda person: print('Hello %s' % person))
            >>> @api.on('greet')
            ... def greeter(person):
            ...     print('Hello %s' % person)

        Arguments:
            event (str): Name of event
            handler (callable): Function to add as handler
            priority (int): Priority of handler

        Decorator Arguments:
            event (str): Name of event
            priority (int): Priority of handler
        '''

        self.events.on(*args)

    def off(self, event, handler):
        '''Remove a handler from an event.

        Arguments:
            event (str): Name of the event
            handler (callable): Handler to remove
        '''

        self.events.off(event, handler)

    def send(self, event, *args, **kwargs):
        '''Send an event. Executes all the event handlers and returns a
        list of the handlers results.

        Arguments:
            event (str): Name of event to send
            *args: Event arguments
            **kwargs: Event keyword arguments
        '''

        return self.events.send(event, *args, **kwargs)

    def extend(self, name, member):
        '''Register an obj with the API at the specified name. This provides
        a way for Extensions to register objects to be first-class members of
        the API.

        Examples:
            >>> def say(message):
            ...     return message
            >>> api.extend('say', say)
            >>> api.say('Hello world!')
            'Hello world!
        '''

        if hasattr(self, name):
            raise NameError('API already has a member named "%s".' % name)

        if requires_wrapper(member):
            member = api_method_wrapper(self, member)

        _log.debug('Adding %s to api.' % name)
        self._registered_members[name] = member
        setattr(self, name, member)

    def unextend(self, name):
        '''Unregister a name that was registered using extend.

        Examples:
            >>> api.unextend('say')
        '''

        if name in self._registered_members:
            _log.debug('Removing %s from api.' % name)
            self._registered_members.pop(name, None)
            self.__dict__.pop(name, None)
        else:
            _log.debug(name + ' was not registered with api.extend.')

    def show(self, data, *include_keys):
        '''Pretty print a dict or list of dicts.'''

        if isinstance(data, Mapping):
            if include_keys:
                data = {k: data[k] for k in include_keys if k in data}
            print(yaml_dump(dict(data)).decode('utf-8'))
            return
        elif isinstance(data, basestring):
            print(data)
            return

        try:
            for obj in data:
                self.show(obj, *include_keys)
                print('')
        except:
            print('Can not format: %s' % data)


def api_method_wrapper(api, fn):

    @wraps(fn)
    def api_method_call(*args, **kwargs):
        return fn(api, *args, **kwargs)

    return api_method_call


def requires_wrapper(obj):
    return callable(obj) and 'api' in inspect.getargspec(obj)[0]
