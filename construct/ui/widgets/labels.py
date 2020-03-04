# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Third party imports
from Qt import QtWidgets

# Local imports
from . import Widget


__all__ = [
    'BaseLabel',
    'H1',
    'H2',
    'H3',
    'H4',
    'H5',
    'P',
]


class BaseLabel(Widget, QtWidgets.QLabel):

    def __init__(self, *args, **kwargs):
        super(BaseLabel, self).__init__(*args, **kwargs)


class H1(BaseLabel):

    css_id = 'h1'


class H2(BaseLabel):

    css_id = 'h2'


class H3(BaseLabel):

    css_id = 'h3'


class H4(BaseLabel):

    css_id = 'h4'


class H5(BaseLabel):

    css_id = 'h5'


class P(BaseLabel):

    css_id = 'p'

    def __init__(self, *args, **kwargs):
        super(P, self).__init__(*args, **kwargs)
        self.setWordWrap(True)
