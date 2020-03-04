# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Third party imports
from Qt import QtCore, QtWidgets

# Local imports
from ..scale import px
from ..theme import theme
from . import Widget


__all__ = [
    'Frameless',
]
missing = object()


class Frameless(Widget):
    '''Mixin class for frameless resizeable widgets.

    Classes that have Widgets as a base class should set css_id and any
    css_properties used in themeing.

    Example:

        class MyDialog(Frameless, QtWidgets.QDialog):

            css_id = 'my_label'
            css_properties = {
                'error': False,
            }
    '''

    _resize_area_map = {
        (False, False, False, False): None,
        (True, False, False, False): 'left',
        (True, True, False, False): 'topLeft',
        (False, True, False, False): 'top',
        (False, True, True, False): 'topRight',
        (False, False, True, False): 'right',
        (False, False, True, True): 'bottomRight',
        (False, False, False, True): 'bottom',
        (True, False, False, True): 'bottomLeft'
    }
    _cursor_map = {
        None: QtCore.Qt.ArrowCursor,
        'left': QtCore.Qt.SizeHorCursor,
        'topLeft': QtCore.Qt.SizeFDiagCursor,
        'top': QtCore.Qt.SizeVerCursor,
        'topRight': QtCore.Qt.SizeBDiagCursor,
        'right': QtCore.Qt.SizeHorCursor,
        'bottomRight': QtCore.Qt.SizeFDiagCursor,
        'bottom': QtCore.Qt.SizeVerCursor,
        'bottomLeft': QtCore.Qt.SizeBDiagCursor
    }

    def __init__(self, *args, **kwargs):
        super(Frameless, self).__init__(*args, **kwargs)

        self._mouse_pressed = False
        self._mouse_position = None
        self._resize_area = None
        self.resize_area_size = px(5)
        self.setMouseTracking(True)
        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint
        )
        self.setWindowTitle('construct')
        self.setWindowIcon(theme.icon('brand/construct_icon-white.png'))
        self.setAttribute(QtCore.Qt.WA_Hover)
        self.installEventFilter(self)

        theme.apply(self)

    @property
    def resizing(self):
        return bool(self._resize_area)

    def _check_resize_area(self, pos):
        x, y = pos.x(), pos.y()
        return self._resize_area_map[(
            x < self.resize_area_size,
            y < self.resize_area_size,
            x > self.width() - self.resize_area_size,
            y > self.height() - self.resize_area_size,
        )]

    def _update_resize_area(self, pos):
        self._resize_area = self._check_resize_area(pos)

    def _update_cursor(self, cursor=missing):
        if cursor is not missing:
            self.setCursor(self._cursor_map[cursor])
        else:
            self.setCursor(self._cursor_map.get(self._resize_area, None))

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.HoverMove:
            self._update_cursor(self._check_resize_area(event.pos()))
            return True

        if event.type() == QtCore.QEvent.Leave:
            self.setCursor(QtCore.Qt.ArrowCursor)
            return True

        return False

    def mousePressEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            pos = event.pos()
            self._update_resize_area(pos)
            self._mouse_pressed = True
            self._mouse_position = pos

    def mouseMoveEvent(self, event):
        if not self._mouse_pressed:
            pos = event.pos()
            self._update_resize_area(pos)

        if self._mouse_pressed:
            vector = event.pos() - self._mouse_position
            offset = event.globalPos()

            if self.resizing:
                min_width = self.minimumWidth()
                min_height = self.minimumHeight()
                rect = self.geometry()
                resize_area = self._resize_area.lower()

                if 'left' in resize_area:
                    new_width = rect.width() - vector.x()
                    if new_width > min_width:
                        rect.setLeft(offset.x())

                if 'right' in resize_area:
                    new_width = rect.width() + vector.x()
                    if new_width > min_width:
                        rect.setRight(offset.x())

                if 'top' in resize_area:
                    new_height = rect.height() - vector.y()
                    if new_height > min_height:
                        rect.setTop(offset.y())

                if 'bottom' in resize_area:
                    new_height = rect.height() + vector.y()
                    if new_height > min_height:
                        rect.setBottom(offset.y())

                self.setGeometry(rect)

            else:
                self.move(self.mapToParent(vector))

    def mouseReleaseEvent(self, event):
        self._mouse_pressed = False
        self._mouse_position = None
