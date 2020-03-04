# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Local imports
from ..app import App
from ..theme import theme


class Launcher(App):

    css_id = ''
    css_properties = {
        'theme': 'surface',
        'border': True,
        'windowTitle': 'Construct Launcher',
        'windowIcon': theme.resources.get('icons/construct.svg'),
    }

    def __init__(self, *args, **kwargs):
        super(Launcher, self).__init__(*args, **kwargs)
