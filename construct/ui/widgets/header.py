# -*- coding: utf-8 -*-

# Third party imports
from Qt import QtCore, QtWidgets

# Local imports
from ..layouts import HBarLayout
from ..scale import px
from . import H2, Glyph, IconButton, Widget


__all__ = [
    'Header',
]


class Header(Widget, QtWidgets.QWidget):

    css_id = 'background'
    css_properties = {
        'theme': 'background',
    }

    def __init__(self, label, *args, **kwargs):
        super(Header, self).__init__(*args, **kwargs)

        self.setFixedHeight(px(36))

        self.glyph = Glyph(
            'construct',
            icon_size=(24, 24),
            parent=self,
        )
        self.title = H2(
            label,
            parent=self,
        )
        self.close_button = IconButton(
            icon='close',
            icon_size=(24, 24),
            parent=self,
        )
        self.close_button.setFocusPolicy(QtCore.Qt.NoFocus)

        self.layout = HBarLayout()
        self.layout.setContentsMargins(*px(16, 0, 16, 0))
        self.layout.left.addWidget(self.glyph)
        self.layout.center.addWidget(self.title, stretch=1)
        self.layout.right.addWidget(self.close_button)
        self.setLayout(self.layout)
