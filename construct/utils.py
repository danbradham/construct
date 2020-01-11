# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import inspect
import os
import shutil
import sys
import warnings
from contextlib import contextmanager
from functools import wraps

# Third party imports
import yaml

# Local imports
from .compat import Mapping, Path, basestring


__all__ = [
    'classproperty',
    'deprecated',
    'ensure_exists',
    'get_lib_path',
    'get_subclasses',
    'import_file',
    'isolated_imports',
    'iter_modules',
    'unipath',
    'unload_modules',
    'update_dict',
    'update_env',
    'update_envvar',
]
package_path = Path(__file__).parent.resolve()


def get_lib_path():
    lib = package_path.parent
    if lib.name == 'construct':
        # We're in develop mode so we check a construct dep instead
        import entrypoints
        return Path(entrypoints.__file__).parent
    return lib


def yaml_dump(data, **kwargs):
    kwargs.setdefault('allow_unicode', True)
    kwargs.setdefault('encoding', 'utf-8')
    kwargs.setdefault('default_flow_style', False)
    return yaml.safe_dump(data, **kwargs)


def yaml_load(data):
    return yaml.safe_load(data)


def unipath(*paths):
    return Path(*paths).expanduser().resolve()


def ensure_exists(*folders):
    for folder in folders:
        if not os.path.exists(str(folder)):
            os.makedirs(str(folder))


def update_dict(a, b):
    '''Recursively update one dictionary with another.'''

    for key, b_value in b.items():
        a_value = a.get(key, None)
        if not isinstance(a_value, Mapping):
            a[key] = b_value
        elif isinstance(a_value, Mapping) and isinstance(b_value, Mapping):
            update_dict(a_value, b_value)
        else:
            a[key] = b_value


def update_env(d, **values):
    '''Updates an environment dict with the specified values. An environment
    dict is like os.environ; it includes os.pathsep separators.

    Behavior:
        - List values are combined with the existing values in d.
        - String values override values in d.
        - Dicts containing platform keys ('win', 'linux', 'mac') are selected
          based on the current platform. If the current platform is missing
          the key will not be updated.

    Example:
        >>> import os
        >>> env = os.environ.copy()
        >>> update_env(env, PATH=['some_path'], VAR='value')

    Arguments:
        d (dict): Environment dict to update
        **values: Values to update d with
    '''

    for k, v in values.items():
        update_envvar(d, k, v)

    # TODO: We can expand path values containing string template tokens like
    # ${variable} here if we want. This would have to be expanded twice to
    # handle values referencing other variables.


def update_envvar(d, k, v):
    '''Used by update_env to update a single key with the specified value.'''
    from .constants import PLATFORM

    if isinstance(v, basestring):
        d[k] = v
    elif isinstance(v, list):
        v = os.pathsep.join(v)
        if k not in d:
            d[k] = v
        else:
            d[k] = os.pathsep.join([v, d[k]])
    elif isinstance(v, dict):
        # This is not a platform dict let's throw an error
        if not set(['win', 'linux', 'mac']) & set(v.keys()):
            # TODO: is this the correct thing to do?
            raise ValueError(
                'Got dict expected one of: str, list, int, float'
            )
        # Handle a platform dict
        v = v.get(PLATFORM, None)
        if v is not None:
            update_envvar(d, k, v)
    else:
        d[k] = str(v)


@contextmanager
def isolated_imports(path=None, restore=True):
    '''Contextmanager that isolates all import'''

    old_path_cache = {k: v for k, v in sys.path_importer_cache.items()}
    old_modules = {k: v for k, v in sys.modules.items()}
    old_path = sys.path[:]

    try:

        if path:
            sys.path.insert(0, path)
        yield

    finally:

        sys.path[:] = old_path

        if restore:
            for k in list(sys.modules.keys()):
                if k in old_modules:
                    sys.modules[k] = old_modules[k]
                else:
                    del(sys.modules[k])

            for k in list(sys.path_importer_cache.keys()):
                if k in old_path_cache:
                    sys.path_importer_cache[k] = old_path_cache[k]
                else:
                    del(sys.path_importer_cache[k])


def unload_modules(*names):
    '''Removes modules and their children from sys.modules

    This is intended for use within the isolated_imports contextmanager.
    '''

    for name in names:
        for k in list(sys.modules.keys()):
            if k.startswith(name):
                del(sys.modules[k])


def import_file(path, isolated=True):
    '''Import python module by absolute path. The imported module is removed
    from sys.modules before being returned. This means the same module
    imported using import_file multiple times will return different module
    objects. I haven't decided on whether this is desirable for our use
    case yet, Extension loading. There have been no apparent downsides yet.
    '''

    path = Path(path)
    root = path.parent
    name = path.stem

    with isolated_imports(str(root), restore=isolated):
        unload_modules(name)
        mod = __import__(name, globals(), locals(), [])

    return mod


def iter_modules(*paths):
    '''Iterate over paths yielding all contained python modules and packages.

    The modules are removed from sys.modules after importing and before
    they are yielded.
    '''

    for path in paths:
        path = Path(path)
        for py_file in path.glob('*.py'):
            mod = import_file(py_file, isolated=False)
            yield mod

        for py_pkg in path.glob('*/__init__.py'):
            mod = import_file(py_pkg.parent, isolated=False)
            yield mod


def copy_file(src, dest):
    '''Copy a source file to the specified location.

    Arguments:
        src (str or Path): Source file to copy
        dest (str or Path): Destination file or directory
    '''
    shutil.copy(str(src), str(dest))


def get_subclasses(typ, subclasses=None, recursive=True):
    '''Get all subclasses of the given typ.'''

    if subclasses is None:
        subclasses = []

    for subcls in typ.__subclasses__():
        if subcls not in subclasses:
            subclasses.append(subcls)
        if recursive:
            get_subclasses(subcls, subclasses)

    return subclasses


class classproperty(object):
    '''Like a property but for a Class object.'''

    def __init__(self, fn):
        self.fn = fn

    def __get__(self, obj, type):
        return self.fn(type)


def deprecated(msg, silent=False):
    '''Decorator that marks a function, method, or class as deprecated.'''

    def deprecate_obj(obj):
        obj._deprecated = True
        obj._deprecation_warning = msg

        if silent:
            return obj

        elif inspect.isclass(obj):

            _init = obj.__init__

            def warn_on_init(self, *args, **kwargs):
                warnings.warn(obj._deprecation_warning)
                _init(self, *args, **kwargs)

            obj.__init__ = warn_on_init
            return obj

        else:

            @wraps(obj)
            def warn_on_call(*args, **kwargs):
                warnings.warn(obj._deprecation_warning)
                return obj(*args, **kwargs)

            return warn_on_call

    return deprecate_obj


def is_deprecated(obj):
    '''Return True if an obj is marked as deprecated.'''

    return getattr(obj, '_deprecated', False)
