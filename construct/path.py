# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import os

# Local imports
from .constants import DEFAULT_PATHS
from .utils import unipath


class Path(list):
    '''A list of folders used to lookup resources like settings, icons, and
    extensions.
    '''

    def __init__(self, path=None):
        super(Path, self).__init__()
        self._custom = bool(path)
        self._custom_path = path

    def load(self):
        if self._custom:
            self.extend(
                unipath(p) for p in self._custom_path
            )
            return
        try:
            env_paths = os.environ['CONSTRUCT_PATH'].strip(os.pathsep)
            self.extend(
                unipath(p) for p in env_paths.split(os.pathsep)
            )
        except KeyError:
            pass
        self.extend(DEFAULT_PATHS)

    def unload(self):
        self[:] = []

    def find(self, resource):
        '''Find a resource in one of this objects paths.

        Examples:
            >>> path = Path(['~/.construct'])
            >>> path.find('construct.yaml')
            '~/.construct/construct.yaml'
        '''
        for path in self:
            potential_path = path / resource
            if potential_path.exists():
                return potential_path

    def glob(self, pattern):
        '''Glob all paths using the specified pattern'''

        results = []
        for path in self:
            found = path.glob(pattern)
            if found:
                results.extend(found)
        return results
