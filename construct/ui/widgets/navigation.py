# -*- coding: utf-8 -*-

# Third party imports
from Qt import QtCore, QtGui, QtWidgets

# Local imports
from ..layouts import HBarLayout
from ..scale import px
from . import H2, Button, Glyph, IconButton, P, Widget


__all__ = [
    'Navigation',
]


class Navigation(Widget, QtWidgets.QWidget):

    css_id = 'navigation'
    css_properties = {
        'theme': 'surface',
    }
    uri_changed = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super(Navigation, self).__init__(*args, **kwargs)

        self.setFixedHeight(px(36))

        self.menu_button = IconButton(
            icon='menu',
            icon_size=(24, 24),
            parent=self,
        )
        self.home_button = IconButton(
            icon='home',
            icon_size=(24, 24),
            parent=self,
        )

        self.crumbs = Crumbs(parent=self)
        self.crumbs_editor = CrumbsEditor(parent=self)
        self.crumbs_editor.hide()
        self.crumbs_editor.returnPressed.connect(self.commit_edit_crumbs)
        self.crumbs_editor.focus_lost.connect(self.done_edit_crumbs)

        self.bookmark_button = IconButton(
            icon='bookmark_outline',
            icon_size=(24, 24),
            parent=self,
        )
        self.bookmark_button.setCheckable(True)

        self.layout = HBarLayout(parent=self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(*px(16, 6, 16, 6))
        self.layout.left.addWidget(self.menu_button)
        self.layout.left.addWidget(self.home_button)
        self.layout.center.addWidget(self.crumbs)
        self.layout.center.addWidget(self.crumbs_editor)
        self.layout.center.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.right.addWidget(self.bookmark_button)
        self.setLayout(self.layout)

        self.setAttribute(QtCore.Qt.WA_Hover)
        self.installEventFilter(self)

    def _update_focus_order(self):
        prev_widget = None
        for lo in (self.layout.left, self.layout.center, self.layout.right):
            for i in range(lo.count()):
                next_widget = lo.itemAt(i).widget()

                # We hit some crumbs baby
                if isinstance(next_widget, Crumbs):
                    for crumb in next_widget.iter():
                        if prev_widget:
                            self.setTabOrder(prev_widget, crumb.label)
                        self.setTabOrder(crumb.label, crumb.arrow)
                        prev_widget = crumb.arrow

                # It's a normal widget - probably an IconButton
                if next_widget:
                    if prev_widget:
                        self.setTabOrder(prev_widget, next_widget)
                    prev_widget = next_widget

    def edit_crumbs(self):
        self.crumbs.hide()
        self.crumbs_editor.show()
        uri = 'cons://' + '/'.join([
            c.label.text()
            for c in self.crumbs.iter()
            if c.label.text() and c.label.text() != 'home'
        ])
        self.crumbs_editor.setText(uri)
        self.crumbs_editor.setFocus()

    def done_edit_crumbs(self):
        self.crumbs.show()
        self.crumbs_editor.hide()
        self.parent().setFocus()

    def commit_edit_crumbs(self):
        self.done_edit_crumbs()
        uri = self.crumbs_editor.text()
        self.uri_changed.emit(uri)

    def eventFilter(self, obj, event):
        '''Sets appropriate cursor when hovering over Navigation.'''

        if event.type() == QtCore.QEvent.HoverMove:
            child = self.childAt(event.pos())
            if child and isinstance(child, Crumbs):
                self.setCursor(QtCore.Qt.IBeamCursor)
            else:
                self.setCursor(QtCore.Qt.ArrowCursor)
            return True

        if event.type() == QtCore.QEvent.Leave:
            self.setCursor(QtCore.Qt.ArrowCursor)
            return True

        return super(Navigation, self).eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            child = self.childAt(event.pos())
            if child and isinstance(child, Crumbs):
                self.edit_crumbs()


class CrumbsEditor(Widget, QtWidgets.QLineEdit):

    focus_lost = QtCore.Signal()

    css_id = 'crumbs'
    css_properties = {}

    def __init__(self, *args, **kwargs):
        super(CrumbsEditor, self).__init__(*args, **kwargs)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum,
        )

    def keyPressEvent(self, event):
        '''Sets appropriate cursor when hovering over Navigation.'''

        if event.key() == QtCore.Qt.Key_Escape:
            self.hide()
            return True

        return super(CrumbsEditor, self).keyPressEvent(event)

    def focusOutEvent(self, event):
        self.focus_lost.emit()


class Crumbs(Widget, QtWidgets.QWidget):

    css_id = 'crumbs'
    css_properties = {}

    def __init__(self, *args, **kwargs):
        super(Crumbs, self).__init__(*args, **kwargs)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

    def iter(self):
        for item in range(self.layout.count()):
            yield self.layout.itemAt(item).widget()

    def clear(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def add(self, label):
        crumb = Crumb(label, parent=self)
        self.layout.addWidget(crumb)
        return crumb


class Crumb(Widget, QtWidgets.QWidget):

    css_id = 'crumb'

    def __init__(self, label, *args, **kwargs):
        super(Crumb, self).__init__(*args, **kwargs)

        self.label = QtWidgets.QPushButton(label, parent=self)
        self.label.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.setProperty('position', 'left')

        self.menu = QtWidgets.QMenu(parent=self)
        self.menu.setWindowFlags(
            self.menu.windowFlags() | QtCore.Qt.NoDropShadowWindowHint
        )

        self.arrow = QtWidgets.QPushButton(parent=self)
        self.arrow.setFlat(True)
        self.arrow.setFixedWidth(px(16))
        self.arrow.setMenu(self.menu)
        self.arrow.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.setProperty('position', 'right')

        self.setAttribute(QtCore.Qt.WA_Hover)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.arrow)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.label.installEventFilter(self)
        self.arrow.installEventFilter(self)

    def eventFilter(self, obj, event):
        '''Sets appropriate cursor when hovering over Navigation.'''

        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Down:
                self.arrow.setFocus()
                self.arrow.click()
                return True

        return super(Crumb, self).eventFilter(obj, event)
