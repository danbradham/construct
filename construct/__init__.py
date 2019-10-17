# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Local imports
from . import api, constants, utils
from .api import *
from .errors import *


# Package metadata
__version__ = '0.2.0'
__title__ = 'construct'
__description__ = 'Extensible api for projects and asset libraries'
__author__ = 'Dan Bradham'
__email__ = 'danielbradham@gmail.com'
__url__ = 'https://github.com/construct-org/construct'


def API(name=DEFAULT_API_NAME, **kwargs):
    '''Wraps :class:`construct.api.API` and maintains a cache of API objects.

    This allows you to get the same API object each time you call API with the
    same name.

    Examples:
        >>> import construct
        >>> api = construct.API()
        >>> api is construct.API()
        True
    '''

    if name not in api._cache:
        api._cache[name] = api.API(name, **kwargs)
    return api._cache[name]
