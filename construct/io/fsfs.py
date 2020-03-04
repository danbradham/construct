# -*- coding: utf-8 -*-
'''Lite reimplementation of github.com/danbradham/fsfs.

Uses Path objects instead of passing strings and fsfs.Entry objects around.
'''

from __future__ import absolute_import

# Standard library imports
import errno
import logging
import shutil
from copy import deepcopy

# Third party imports
from bson.objectid import ObjectId

# Local imports
from ..compat import Path, basestring
from ..utils import update_dict, yaml_dump, yaml_load


_log = logging.getLogger(__name__)
missing = object()
search_pattern = '*/.data/uuid_*'
data_dir = '.data'
data_file = 'data'
IGNORE_ERRNO = (
    errno.EACCES,
    errno.ENOENT,
    errno.EIO,
    errno.EPERM,
    59,  # WinError network access
    errno.EINVAL,  # WinError network access
)


class FileCache(object):
    '''Returns data for file only when mtime is unchanged.'''

    def __init__(self):
        self._cache = {}
        self._mtimes = {}

    def pop(self, file):
        self._mtimes.pop(file, None)
        return self._cache.pop(file, None)

    def set(self, file, data):
        self._cache[file] = deepcopy(data)
        self._mtimes[file] = file.stat().st_mtime

    def get(self, file, default=missing):
        if file not in self._cache:
            if default is missing:
                raise KeyError('File not in cache: ' + file.stem)
            return default

        if self._mtimes[file] < file.stat().st_mtime:
            self.pop(file)
            if default is missing:
                raise KeyError('File out of date: ' + file.stem)
            return default

        return deepcopy(self._cache[file])


cache = FileCache()


def search_by_id(path, _id, max_depth=10):
    '''Search by id'''

    for entry in search(path, max_depth):
        if get_id(entry) == _id:
            return entry


def search_by_tag(path, tags, max_depth=10):
    '''Search by tag'''

    if isinstance(tags, basestring):
        tags = [tags]

    for entry in search(path, max_depth):
        if tags.issubset(set(get_tags(entry))):
            yield entry


def search_by_name(path, name, max_depth=10):
    '''Search by name'''

    potential_entries = []

    for entry in search(path, max_depth):
        if entry.name == name:
            return entry
        if entry.name in name:
            potential_entries.append(entry)

    if potential_entries:
        # In almost all cases the best match will be the shortest path
        # with the least parts.
        best = min(
            potential_entries,
            key=lambda x: (len(x.parts), len(str(x)))
        )
        return best


def safe_iterdir(path):

    contents = path.iterdir()
    while True:
        try:
            yield next(contents)
        except (OSError, WindowsError) as e:
            if e.errno not in IGNORE_ERRNO:
                _log.exception('Unrecognized error in safe_iterdir.')
        except StopIteration:
            return


def search(path, max_depth=10):
    '''Yields directories with metadata.'''

    roots = list(safe_iterdir(path))
    level = 0

    while roots and level < max_depth:

        next_roots = []

        for root in roots:
            if root.is_file() or root.name == '.data':
                continue

            if exists(root):
                yield root

            next_roots.extend(list(safe_iterdir(root)))

        level += 1
        roots = next_roots

    return


def parents(path, tag=None):

    for parent in path.parents:
        if exists(parent):
            if tag and tag in get_tags(parent):
                yield parent


def parent(path, tag=None):
    for parent in parents(path, tag):
        return parent


def exists(path):
    '''Check if a path is already initialized.'''

    return (
        (path / data_dir).exists() and
        (path / data_dir / data_file).exists()
    )


def init(path, _id=None):
    '''Initialize .data for a directory.

    Arguments:
        path (Path): Directory to initialize
        _id (str): UUID value defaults to a new Bson ObjectID
    '''

    if not _id:
        _id = str(ObjectId())

    path_data_dir = path / data_dir
    path_data_file = path_data_dir / data_file
    path_uuid_file = path_data_dir / ('uuid_' + _id)

    path_data_dir.mkdir(parents=True, exist_ok=True)
    path_data_file.touch(exist_ok=True)

    existing = list((path / data_dir).glob('uuid_*'))
    if not existing:
        path_uuid_file.touch(exist_ok=True)


def read(path, *keys):
    '''Read metadata from directory

    Arguments:
        path (Path): Directory containing metadata
        *keys (List[str]): list of keys to retrieve. If no keys are passed
            return all key, value pairs.

    Returns:
        dict: key, value pairs stored at path
    '''

    path = Path(path)
    file = path / data_dir / data_file
    if not file.exists():
        raise OSError('Data file does not exist: ' + file.as_posix())

    try:
        data = cache.get(file)
    except KeyError:
        raw_data = file.read_text(encoding='utf-8')
        if not raw_data:
            return {}

        data = yaml_load(raw_data)
        cache.set(file, data)

    if not keys:
        return data

    if len(keys) == 1:
        return data[keys[0]]

    return dict((k, data[k]) for k in keys)


def write(path, replace=False, **data):
    '''Write metadata to directory

    Arguments:
        path (str): Directory to write to
        replace (bool): Overwrite directory data. Defaults to False.
        **data (dict): key, value pairs to write

    Returns:
        None
    '''

    path = Path(path)
    init(path)

    file = path / data_dir / data_file
    if not replace:
        new_data = read(path)
        update_dict(new_data, data)
    else:
        new_data = data

    file.write_bytes(yaml_dump(new_data))

    cache.pop(file)
    return new_data


def set_id(path, value):
    '''Set the id for the directory.

    Creates an empty file named uuid_<value> in the paths .data directory.

    Arguments:
        path (Path): Directory to set id for
        value (str): ID as string

    Returns:
        None
    '''

    path = Path(path)

    existing = (path / data_dir).glob('uuid_*')
    for file in existing:
        file.unlink()

    path_uuid_file = path / data_dir / ('uuid_' + value)
    path_uuid_file.touch(exist_ok=True)


def get_id(path):
    '''Get the id of a directory.

    Returns:
        str - uuid
    '''

    path = Path(path)

    existing = (path / data_dir).glob('uuid_*')
    for file in existing:
        return file.name.split('uuid_')[-1]


def delete(path, remove_root=False):
    '''Delete a directory's metadata and tags. If remove_root is True, remove
    the directory itself.

    Arguments:
        path (Path): Directory to remove metadata and tags from
        remove_root (bool): Delete the directory as well. Defaults to False.

    Returns:
        None
    '''

    path = Path(path)

    if not path.exists():
        return

    path_data_dir = path / data_dir
    if path_data_dir.exists():
        shutil.rmtree(path_data_dir.as_posix())

    if remove_root:
        shutil.rmtree(path.as_posix())


def get_tags(path):
    '''Get a directory's tags.

    Returns:
        List of tags as strings
    '''

    path = Path(path)

    return [
        f.name.split('tag_')[-1]
        for f in (path / data_dir).glob('tag_*')
    ]


def tag(path, *tags):
    '''Tag a directory as an Entry with the provided tags.

    Arguments:
        path (Path): Directory to tag
        *tags (List[str]): Tags to add to directory like: 'asset' or 'project'
    '''

    assert len(tags), 'Must provide at least one tag.'

    path = Path(path)

    init(path)

    for tag in tags:
        tag_file = path / data_dir / ('tag_' + tag)
        tag_file.touch(exist_ok=True)


def untag(path, *tags):
    '''Remove a tag from a directory.

    Arguments:
        path (Path): Directory to remove tags from
        *tags (List[str]): Tags to remove like: 'asset' or 'project'
    '''

    assert len(tags), 'Must provide at least one tag.'

    path = Path(path)

    if not path.exists():
        return

    for tag in tags:
        tag_file = path / data_dir / ('tag_' + tag)
        if tag_file.exists():
            tag_file.unlink()
