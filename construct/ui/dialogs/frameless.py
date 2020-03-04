# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Third party imports
from Qt import QtCore, QtWidgets

# Local imports
from ..layouts import HBarLayout
from ..scale import px
from ..widgets import Frameless


__all__ = [
    'FramelessDialog',
]


class FramelessDialog(Frameless, QtWidgets.QDialog):

    css_id = ''
    css_properties = {
        'theme': 'surface'
    }

    def __init__(self, *args, **kwargs):
        super(FramelessDialog, self).__init__(*args, **kwargs)

        self.setWindowFlags(
            QtCore.Qt.Dialog |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint
        )

        self.header = QtWidgets.QWidget()
        self.header_layout = HBarLayout()
        self.header.setLayout(self.header_layout)

        self.body = QtWidgets.QWidget()
        self.body_layout = QtWidgets.QVBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(px(16))
        self.body.setLayout(self.body_layout)

        self.footer = QtWidgets.QWidget()
        self.footer_layout = HBarLayout()
        self.footer.setLayout(self.footer_layout)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(*px(16, 8, 16, 8))
        self.layout.setSpacing(px(16))
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.body)
        self.layout.addWidget(self.footer)
        self.setLayout(self.layout)
