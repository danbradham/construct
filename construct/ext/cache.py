# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import logging
import shutil

# Local imports
from ..constants import USER_PATH
from ..extensions import Extension
from ..utils import yaml_dump, yaml_load


_log = logging.getLogger(__name__)
missing = object()


class Cache(Extension):
    '''A global cache shared between multiple users.'''

    identifier = 'cache'
    label = 'Cache'

    def is_available(self, ctx):
        return True

    def load(self, api):
        api.extend(self.identifier, self)
        # TODO: Switch cache backend based on settings
        # this could be mongodb or redis eventually
        self.cache = FSCache(api.settings.folder / 'cache')

    def unload(self, api):
        api.unextend(self.identifier)

    def __contains__(self, key):
        return self.cache.__contains__(key)

    def to_dict(self):
        return self.cache.to_dict()

    def keys(self):
        return self.cache.keys()

    def values(self):
        return self.cache.values()

    def items(self):
        return self.cache.items()

    def get(self, key, default=missing):
        return self.cache.get(key, default)

    def set(self, key, value):
        return self.cache.set(key, value)

    def delete(self, key):
        return self.cache.delete(key)

    def clear(self):
        return self.cache.clear()


class UserCache(Cache):
    '''The local user cache.

    Applies to only one user. Can be used to store things like UI state,
    favorites, and preferences.
    '''

    identifier = 'user_cache'
    label = 'User Cache'

    def is_available(self, ctx):
        return True

    def load(self, api):
        api.extend(self.identifier, self)
        self.cache = FSCache(USER_PATH / 'user')

    def unload(self, api):
        api.unextend(self.identifier)


class FSCache(object):
    '''Base implementation for filesystem Caches.

    Operates in a directory on the file system. Each key represents a single
    file within the directory.
    '''

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def __contains__(self, key):
        return self._file_for(key).exists()

    def _file_for(self, key):
        return self.cache_dir / key

    def to_dict(self):
        return {k: self.get(k) for k in self.keys()}

    def keys(self):
        return [c.name for c in self.cache_dir.iterdir() if c.is_file()]

    def values(self):
        return [self.get(k) for k in self.keys()]

    def items(self):
        return [(k, self.get(k)) for k in self.keys()]

    def get(self, key, default=missing):
        key_file = self._file_for(key)
        if not key_file.exists():
            if default is not missing:
                return default
            else:
                raise KeyError('Can not find %s in cache.' % key)
        data = key_file.read_text(encoding='utf-8')
        return yaml_load(data)

    def set(self, key, value):
        key_file = self._file_for(key)
        key_file.write_bytes(yaml_dump(value))

    def delete(self, key):
        key_file = self._file_for(key)
        if key_file.exists():
            key_file.unlink()

    def clear(self):
        if self.cache_dir.is_dir():
            shutil.rmtree(str(self.cache_dir))
