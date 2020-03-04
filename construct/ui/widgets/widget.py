# -*- coding: utf-8 -*-

# Third party imports
from Qt import QtCore


__all__ = [
    'Widget',
]


class Widget(object):
    '''Mixin class for all themable widgets.

    Classes that have Widgets as a base class should set css_id and any
    css_properties used in themeing.

    Example:

        class MyWidget(Widget, QtWidgets.QLabel):

            css_id = 'my_label'
            css_properties = {
                'error': False,
            }
    '''

    css_id = ''
    css_properties = {}

    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)

        for prop, value in self.css_properties.items():
            self.setProperty(prop, value)

        if self.css_id:
            self.setObjectName(self.css_id)

        self.setAttribute(QtCore.Qt.WA_StyledBackground)
