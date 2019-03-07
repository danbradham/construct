# -*- coding: utf-8 -*-
from __future__ import absolute_import
__version__ = '1.0.0'
__title__ = 'construct'
__description__ = 'Extensible api for projects and asset libraries'
__author__ = 'Dan Bradham'
__email__ = 'danielbradham@gmail.com'
__url__ = 'https://github.com/construct-org/construct'


from .constants import DEFAULT_API_NAME
from . import api


def API(name=DEFAULT_API_NAME, **kwargs):
    '''Wrap api.API is a singleton'''

    if name not in api._cache:
        api._cache[name] = api.API(name, **kwargs)
    return api._cache[name]
