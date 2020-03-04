# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Third party imports
from Qt import QtCore
from Qt.QtWidgets import QBoxLayout

# Local imports
from ..scale import pt


class BarLayout(QBoxLayout):
    '''BarLayout like BoxLayout but with 3 sub layouts allowing users to add
    widgets to the start, middle and end of the layout.

    |start | -------- middle -------- | end|

    Attributes:
        start - QBoxLayout with default direction set to LeftToRight
        middle - QBoxLayout with default direction set to LeftToRight
        end - QBoxLayout with default direction set to LeftToRight
    '''

    def __init__(self, direction=None, parent=None):
        direction = direction or self.LeftToRight
        super(BarLayout, self).__init__(direction, parent)

        self.start = QBoxLayout(direction)
        self.start.setSpacing(pt(8))
        self.left = self.start
        self.top = self.start

        self.middle = QBoxLayout(direction)
        self.middle.setSpacing(pt(8))
        self.center = self.middle

        self.end = QBoxLayout(direction)
        self.end.setSpacing(pt(8))
        self.right = self.end
        self.bottom = self.end

        self.addLayout(self.start)
        self.addLayout(self.middle)
        self.addLayout(self.end)

        self.setStretch(1, 1)
        self.setSpacing(pt(8))
        self.setContentsMargins(0, 0, 0, 0)

        self.setDirection(direction)

    def count(self):
        '''Sum of the count of all sub layouts'''
        return self.start.count() + self.middle.count() + self.end.count()

    def setDirection(self, direction):
        '''Realign sub-layouts based on direction'''

        if direction in (self.LeftToRight, self.RightToLeft):
            self.start.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
            self.middle.setAlignment(QtCore.Qt.AlignCenter)
            self.end.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        elif direction in (self.TopToBottom, self.BottomToTop):
            self.start.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter)
            self.middle.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter)
            self.end.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        else:
            raise ValueError(
                'Got %s expected QBoxLayout.Direction' % direction
            )

        self.start.setDirection(direction)
        self.middle.setDirection(direction)
        self.end.setDirection(direction)
        super(BarLayout, self).setDirection(direction)


class HBarLayout(BarLayout):
    '''Horizontal BarLayout.

    Attributes:
        left - QBoxLayout alignment set to left
        center - QBoxLayout alignment set to center
        right - QBoxLayout alignment set to right
    '''

    def __init__(self, parent=None):
        super(HBarLayout, self).__init__(QBoxLayout.LeftToRight, parent)


class VBarLayout(BarLayout):
    '''Vertical BarLayout.

    Attributes:
        top - QBoxLayout alignment set to top
        center - QBoxLayout alignment set to center
        bottom - QBoxLayout alignment set to bottom
    '''

    def __init__(self, parent=None):
        super(VBarLayout, self).__init__(QBoxLayout.TopToBottom, parent)
