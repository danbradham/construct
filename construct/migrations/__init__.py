# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import logging
from copy import deepcopy
from inspect import getmembers

# Local imports
from ..compat import Path, basestring
from . import utils


_log = logging.getLogger(__name__)


class Migration(object):

    schema_type = ''
    schema_version = (0, 1, 0)

    def __init__(self, api, entity):
        self.api = api
        self.entity = entity

    def log(self, direction):
        name = self.__class__.__name__
        if _log.isEnabledFor(logging.DEBUG):
            if self.__doc__:
                _log.debug('%s: %s', name, self.__doc__)
            _log.debug(
                '%s.%s() from %s to %s',
                name,
                direction,
                format_version(self.entity['schema_version']),
                format_version(self.schema_version),
            )

    def log_failure(self):
        _log.exception(
            '%s: Migration Failed. All changes discarded.',
            self.__class__.__name__,
        )

    def log_success(self, result):
        if _log.isEnabledFor(logging.DEBUG):
            _log.debug(result)
            _log.debug(self.__class__.__name__ + ': okay!')

    def _forward(self):
        self.log('forward')
        try:
            entity = self.forward()
        except:
            self.log_failure()
            raise

        self.log_success(entity)
        return entity

    def forward(self):
        return self.entity

    def _backward(self):
        self.log('backward')
        try:
            entity = self.backward()
        except:
            self.log_failure()
            raise

        self.log_success(entity)
        return entity

    def backward(self):
        return self.entity


def split_version(version):
    if version is None:
        return
    elif isinstance(version, tuple):
        return version
    elif isinstance(version, basestring):
        return tuple([int(v) for v in version.split('.')])
    else:
        raise ValueError('version: expected string or tuple got %s', version)


def format_version(version):
    if version is None:
        return
    elif isinstance(version, basestring):
        return version
    elif isinstance(version, tuple):
        return '.'.join([str(v) for v in version])
    else:
        raise ValueError('version: expected string or tuple got %s', version)


def is_migration(obj):
    if obj is Migration:
        return False
    try:
        return issubclass(obj, Migration)
    except TypeError:
        return False


def initial_migration(api, project):
    from .initial import InitialMigration
    InitialMigration(api, project).forward()


def requires_initial_migration(project):
    return 'schema_version' not in project


def get_migrations(migrations_dir=None):
    import sys
    relative_dir = Path(__file__).parent
    migrations_dir = migrations_dir or Path(__file__).parent

    if migrations_dir == relative_dir:
        for f in migrations_dir.glob('*.py'):
            if f.stem == '__init__':
                continue
            mod = __import__(f.stem, globals=globals(), level=1)
            for _, member in getmembers(mod, is_migration):
                yield member
    else:
        # Get migrations from another directory for testing purposes
        old_path = sys.path[:]
        sys.path.insert(0, str(migrations_dir))
        try:
            for f in migrations_dir.glob('*.py'):
                mod = __import__(f.stem)
                for _, member in getmembers(mod, is_migration):
                    yield member
        finally:
            sys.path[:] = old_path


def applicable_migrations(migrations, schema_type, from_version, to_version):

    if not migrations:
        return []

    applicable = [m for m in migrations if schema_type == m.schema_type]
    to_version = to_version or max([m.schema_version for m in applicable])

    backward = False
    if from_version > to_version:
        backward = True
        applicable = [
            m for m in applicable
            if from_version > m.schema_version
            and m.schema_version >= to_version
        ]

    else:
        applicable = [
            m for m in applicable
            if from_version < m.schema_version
            and m.schema_version <= to_version
        ]

    applicable = sorted(
        applicable,
        key=lambda x: x.schema_version,
        reverse=backward,
    )

    return applicable, from_version, to_version


def forward(api, entity, to_version=None, migrations_dir=None):

    name = entity.get('name', entity['_type'])
    schema_type = entity['_type']
    schema_version = split_version(entity['schema_version'])
    to_version = split_version(to_version)

    if to_version and schema_version > to_version:
        _log.info(
            'Skipping migration: %s is newer than %s',
            name,
            format_version(to_version)
        )
        return

    # Get applicable migrations
    migrations, from_version, to_version = applicable_migrations(
        get_migrations(migrations_dir),
        schema_type,
        schema_version,
        to_version,
    )

    _log.info(
        'Migrating from %s to %s',
        format_version(from_version),
        format_version(to_version)
    )
    _log.debug(entity)
    try:
        modified_entity = deepcopy(entity)
        for m in migrations:
            modified_entity = m(api, modified_entity)._forward()
    except:
        # TODO: rollback changes
        pass
    else:
        # TODO: commit changes to data layers
        pass

    return modified_entity


def backward(api, entity, to_version, migrations_dir=None):

    name = entity.get('name', entity['_type'])
    schema_type = entity['_type']
    schema_version = entity['schema_version']
    schema_version = split_version(entity['schema_version'])
    to_version = split_version(to_version)

    if schema_version < to_version:
        _log.info(
            'Skipping migration: %s is older than %s',
            name,
            format_version(to_version)
        )
        return

    # Get applicable migrations
    _log.debug('XXXX %s -> %s', schema_version, to_version)
    migrations, from_version, to_version = applicable_migrations(
        get_migrations(migrations_dir),
        schema_type,
        schema_version,
        to_version,
    )

    _log.info(
        'Migrating from %s to %s',
        format_version(from_version),
        format_version(to_version)
    )
    _log.debug(entity)
    try:
        modified_entity = deepcopy(entity)
        for m in migrations:
            modified_entity = m(api, modified_entity)._forward()
    except:
        # TODO: rollback changes
        pass
    else:
        # TODO: commit changes to data layers
        pass

    return modified_entity
