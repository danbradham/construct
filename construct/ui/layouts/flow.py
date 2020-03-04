# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Third party imports
from Qt import QtCore, QtWidgets

# Local imports
from ..scale import pt


class FlowLayout(QtWidgets.QLayout):
    '''A Layout that wraps widgets on overflow.
    ____________
    | [] [] [] |
    | [] [] [] |
    | [] []    |
    ------------
    '''

    def __init__(self, margin=16, hspacing=8, vspacing=8, parent=None):
        super(FlowLayout, self).__init__(parent=parent)
        self._margin = pt(margin)
        self._hspacing = pt(hspacing)
        self._vspacing = pt(vspacing)
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        while self.count():
            item = self.takeAt(0)
            del item

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        try:
            return self._items[index]
        except IndexError:
            return

    def takeAt(self, index):
        return self._items.pop(index)

    def horizontalSpacing(self):
        return self._hspacing

    def verticalSpacing(self):
        return self._vspacing

    def expandingDirections(self):
        return QtCore.Qt.Horizontal

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(
            QtCore.QRect(0, 0, width, 0),
            True
        )

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self._items:
            size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QtCore.QSize(
            margins.left() + margins.right(),
            margins.top() + margins.bottom()
        )
        return size

    def doLayout(self, rect, testOnly=False):

        m = self.contentsMargins()
        r = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x, y = r.x(), r.y()
        rows = []
        row = {'items': [], 'height': 0, 'space': 0, 'count': 0}
        rows.append(row)

        for item in self._items:
            w = item.widget()
            width, height = w.sizeHint().width(), w.sizeHint().height()
            space = self.horizontalSpacing()
            if space < 0:
                space = w.style().layoutSpacing(
                    QtWidgets.QSizePolicy.QPushButton,
                    QtWidgets.QSizePolicy.QPushButton,
                    QtCore.Qt.Horizontal,
                )

            if x + width < r.right():
                row['items'].append(item)
                row['height'] = max(row['height'], height)
                row['space'] += space
                row['count'] += 1
                x += width + space
            else:
                row['space'] += r.right() - x - space
                row = {
                    'items': [item],
                    'height': height,
                    'space': space,
                    'count': 1
                }
                rows.append(row)
                x = r.x() + width + space

        if testOnly:
            if len(rows) < 2:
                vspace = 0
            else:
                vspace = (len(rows) - 1) * self.verticalSpacing()
            vmargins = m.top() + m.bottom()
            return sum([r['height'] for r in rows]) + vspace + vmargins

        x, y = r.x(), r.y()
        for row in rows:

            if row['count'] < 2:
                space = 0
            else:
                space = row['space'] / len(row['items']) - 1

            for item in row['items']:
                item.setGeometry(QtCore.QRect(
                    QtCore.QPoint(x, y),
                    item.sizeHint()
                ))
                x += item.sizeHint().width() + space

            x = r.x()
            y += row['height'] + self.verticalSpacing()
