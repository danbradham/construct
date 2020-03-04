# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Third party imports
from Qt import QtCore, QtWidgets

# Local imports
from ..scale import pt, px
from ..theme import theme
from . import P, Widget


__all__ = [
    'Button',
    'Glyph',
    'IconButton',
    'ToolButton',
]


class Button(Widget, QtWidgets.QPushButton):

    css_id = ''
    css_properties = {
        'type': 'text',
    }

    def __init__(self, text=None, icon=None, icon_size=None, **kwargs):
        super(Button, self).__init__(**kwargs)
        self.setFlat(True)

        if text:
            self.setText(text)

        if icon:
            self.setIcon(theme.icon(icon))

        if icon_size:
            self.setIconSize(QtCore.QSize(*px(icon_size[0], icon_size[1])))
        else:
            self.size = QtCore.QSize(*px(24, 24))


class IconButton(Widget, QtWidgets.QPushButton):

    css_id = ''
    css_properties = {
        'type': 'icon',
    }

    def __init__(self, icon, icon_size=None, on_icon=None, **kwargs):
        super(IconButton, self).__init__(**kwargs)
        self.setFlat(True)
        self.set_icon(icon, icon_size)

        self._icon = icon
        self._icon_size = icon_size
        self._on_icon = on_icon

        if self._on_icon:
            self.toggled.connect(self.update_icon)

    def update_icon(self, state):
        icon = self._icon
        if state and self._on_icon:
            icon = self._on_icon
        self.set_icon(icon, self._icon_size)

    def set_icon(self, icon, icon_size=None, on_icon=None):
        self.setIcon(theme.icon(icon, parent=self))
        if icon_size:
            self.size = QtCore.QSize(*px(icon_size[0], icon_size[1]))
        else:
            self.size = QtCore.QSize(*px(24, 24))

        self.setIconSize(self.size)
        self.setFixedSize(self.size)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Fixed,
        )


class ToolButton(Widget, QtWidgets.QPushButton):

    css_id = ''
    css_properties = {
        'type': 'tool',
    }

    def __init__(self, text, icon=None, icon_size=None, **kwargs):
        super(ToolButton, self).__init__(**kwargs)

        self.label = P(text, parent=self)
        self.label.setWordWrap(True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setMouseTracking(False)
        self.label.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )

        self.glyph = Glyph(icon, icon_size, parent=self)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(*px(8, 8, 8, 8))
        self.layout.setSpacing(px(4))
        self.layout.addWidget(self.glyph)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def sizeHint(self):
        return QtCore.QSize(
            self.glyph.size.width() + px(16),
            self.glyph.size.height() + px(32),
        )


class Glyph(IconButton):

    css_id = 'icon'
    css_properties = {}

    def __init__(self, icon, icon_size=None, parent=None):
        super(Glyph, self).__init__(icon, icon_size, parent=parent)
        self.setDisabled(True)
