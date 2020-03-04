# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Third party imports
from Qt import QtCore

# Local imports
from ..scale import px
from ..theme import theme
from ..widgets import H3, Glyph, IconButton, P
from . import FramelessDialog


__all__ = [
    'Notification',
]


class Notification(FramelessDialog):
    '''Notification dialog used to show quick messages to users.

    Arguments:
        type (str): Type or theme. One of ['alert', 'error', 'info', 'success']
        message (str): Message to display
        title (str): Dialog title
        icon (str): Name of icon to display along title / message
        close_icon (str): Name of close icon
        short (bool): Hides title when True

    Example:
        >>> alert = Notification('alert', 'Something Happened!')
        >>> alert.exec_()
    '''

    def __init__(
        self,
        type,
        message,
        title=None,
        icon=None,
        close_icon=None,
        short=None,
        parent=None,
    ):
        super(Notification, self).__init__(parent=parent)

        self.set_type(type)
        self.setMinimumWidth(px(272))

        self.header_message = P(message, parent=self)
        self.header_message.setAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        )
        self.body_message = P(message, parent=self)
        self.body_message.setAlignment(QtCore.Qt.AlignLeft)
        self.title = H3(title or type.title(), parent=self)
        self.title.setAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        )

        self.icon = icon
        self.glyph = Glyph(
            icon=icon or 'circle_outline',
            icon_size=(24, 24),
            parent=self,
        )
        if not icon:
            self.glyph.hide()

        self.close_button = IconButton(
            icon=close_icon or 'close',
            icon_size=(24, 24),
            parent=self,
        )
        self.close_button.clicked.connect(self.accept)

        self.header_layout.left.addWidget(self.glyph)
        self.header_layout.center.addWidget(self.header_message, stretch=1)
        self.header_layout.center.addWidget(self.title, stretch=1)
        self.header_layout.right.addWidget(self.close_button)
        self.body_layout.addWidget(self.body_message, stretch=1)

        if short is not None:
            self.set_short(short)
        else:
            self.set_short(len(message) < 72)

    def set_short(self, value):
        self.is_short = value
        if self.is_short:
            self.header_message.show()
            self.title.hide()
            self.body.hide()
            self.footer.hide()
            self.adjustSize()
        else:
            if self.icon:
                self.title.setAlignment(QtCore.Qt.AlignCenter)
            self.title.show()
            self.footer.setVisible(self.footer_layout.count())
            self.body.show()
            self.header_message.hide()
            self.adjustSize()

    def set_type(self, type):
        self.setProperty('theme', type.lower())
        theme.apply(self)

    def set_icon(self, icon):
        self.icon = icon
        if icon:
            self.glyph.set_icon(icon, (24, 24))
            self.glyph.show()
        else:
            self.glyph.hide()

    def set_close_icon(self, icon):
        self.close_icon.set_icon(icon, (24, 24))
