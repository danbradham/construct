# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Third party imports
from Qt import QtCore

# Local imports
from ..scale import px
from ..widgets import H3, Button, Glyph, P
from . import FramelessDialog


__all__ = [
    'Ask',
]


class Ask(FramelessDialog):

    css_properties = {
        'theme': 'surface',
        'border': True,
    }

    def __init__(
        self,
        title,
        message,
        yes_label='Yes',
        no_label='No',
        icon=None,
        parent=None,
    ):
        super(Ask, self).__init__(parent=parent)
        self.setMinimumWidth(px(272))

        self.title = H3(title, parent=self)
        self.title.setAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        )
        self.body_message = P(message, parent=self)
        self.body_message.setAlignment(QtCore.Qt.AlignLeft)

        self.glyph = Glyph(icon or 'question', (24, 24))
        if not icon:
            self.glyph.hide()

        self.yes_button = Button(yes_label, parent=self)
        self.yes_button.clicked.connect(self.accept)

        self.no_button = Button(no_label, parent=self)
        self.no_button.clicked.connect(self.reject)

        self.header_layout.left.addWidget(self.glyph)
        self.header_layout.center.addWidget(self.title, stretch=1)
        self.body_layout.addWidget(self.body_message, stretch=1)
        self.footer_layout.right.addWidget(self.yes_button)
        self.footer_layout.right.addWidget(self.no_button)

        self.adjustSize()

    def set_icon(self, icon):
        if icon:
            self.glyph.set_icon(icon, (24, 24))
            self.glyph.show()
        else:
            self.glyph.hide()
