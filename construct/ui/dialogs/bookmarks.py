# -*- coding: utf-8 -*-

# Standard library imports
from functools import partial

# Third party imports
from Qt import QtCore, QtWidgets

# Local imports
from ..layouts import HBarLayout, VBarLayout
from ..scale import px
from ..widgets import (
    H4,
    Button,
    Frameless,
    Glyph,
    HLine,
    IconButton,
    P,
    Widget,
)


__all__ = [
    'BookmarksDialog',
]


class BookmarkWidget(Widget, QtWidgets.QWidget):
    '''Bookmark view.'''

    def __init__(self, data, *args, **kwargs):
        super(BookmarkWidget, self).__init__(*args, **kwargs)

        self.data = data
        self.layout = HBarLayout(parent=self)
        self.icon = Glyph(
            icon=data.get('icon', 'square'),
            icon_size=(14, 14),
            parent=self,
        )
        self.label = P(data['name'], parent=self)
        self.label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.remove = IconButton(
            icon='minus',
            icon_size=(14, 14),
            parent=self,
        )
        self.remove.hide()

        self.setToolTip(data['uri'])
        self.setMouseTracking(True)

        self.layout.left.addWidget(self.icon)
        self.layout.center.addWidget(self.label)
        self.layout.right.addWidget(self.remove)

    def enterEvent(self, event):
        self.remove.show()

    def leaveEvent(self, event):
        self.remove.hide()


class BookmarksBase(Frameless, QtWidgets.QDialog):
    '''Base view for displaying and editing bookmarks. This is not connected
    to any signals.'''

    css_id = 'bookmarks'
    css_properties = {
        'theme': 'surface',
        'windowTitle': 'Bookmarks',
        'windowIcon': 'bookmarks',
    }
    added = QtCore.Signal()
    removed = QtCore.Signal()
    edited = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(BookmarksBase, self).__init__(*args, **kwargs)

        self.setMinimumWidth(px(256))
        self.setMinimumHeight(px(384))

        self.header = H4('Bookmarks', parent=self)
        self.header.setAlignment(QtCore.Qt.AlignCenter)
        self.header.setFixedHeight(px(32))

        self.name_label = P('name', parent=self)
        self.name_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        self.name = QtWidgets.QLineEdit(parent=self)
        self.add = Button(
            'add',
            parent=self,
        )
        self.add.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.remove = Button(
            'remove',
            parent=self,
        )
        self.remove.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.edit = Button(
            'edit',
            parent=self,
        )
        self.edit.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.list = QtWidgets.QListWidget(parent=self)

        self.tools = QtWidgets.QHBoxLayout()
        self.tools.addWidget(self.remove)
        self.tools.addWidget(self.edit)
        self.tools.addWidget(self.add)

        self.form = QtWidgets.QFormLayout()
        self.form.setContentsMargins(*px(16, 16, 16, 16))
        self.form.setSpacing(px(16))
        self.form.addRow(self.name_label, self.name)
        self.form.addRow(self.tools)

        self.layout = VBarLayout(parent=self)
        self.layout.setSpacing(0)
        self.layout.top.setSpacing(0)
        self.layout.top.addWidget(self.header)
        self.layout.top.addWidget(HLine(self))
        self.layout.top.addLayout(self.form)
        self.layout.top.addWidget(HLine(self))
        self.layout.center.addWidget(self.list)
        self.layout.center.setContentsMargins(*px(1, 0, 1, 1))
        self.setLayout(self.layout)

    def add_bookmark_item(self, bookmark, remove_callback):
        widget = BookmarkWidget(bookmark, parent=self.list)
        widget.remove.clicked.connect(remove_callback)
        item = QtWidgets.QListWidgetItem(parent=self.list)
        self.list.addItem(item)
        self.list.setItemWidget(item, widget)


class BookmarksDialog(BookmarksBase):
    '''Bookmarks Dialog. This is the stateful version of the BookmarksBase.

    Required State:
        api (API): Used to retrieve and persist bookmarks in user_cache.
        bookmarks (List[Dict]): Storage for bookmarks.
        context (Context): Causes a the dialog to refresh.
        uri (str): Set when a bookmark is clicked.
    '''

    def __init__(self, state, *args, **kwargs):
        super(BookmarksDialog, self).__init__(*args, **kwargs)

        self.remove.clicked.connect(self._on_rem_clicked)
        self.add.clicked.connect(self._on_add_or_edit_clicked)
        self.edit.clicked.connect(self._on_add_or_edit_clicked)
        self.list.itemClicked.connect(self._on_bookmark_clicked)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.state = state
        self.state['bookmarks'].changed.connect(self._refresh)
        self.state['context'].changed.connect(self._refresh)
        self._refresh()
        self.installEventFilter(self)

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.WindowDeactivate:
            self.accept()
        return super(BookmarksDialog, self).eventFilter(object, event)

    def _refresh(self):
        self.list.clear()

        bookmark = self._get_bookmark(self.state['uri'].get())
        if bookmark:
            self.name.setText(bookmark['name'])
            self.add.setEnabled(False)
            self.edit.setEnabled(True)
            self.remove.setEnabled(True)
        else:
            self.name.setText(self._name_from_context(self.state['context']))
            self.add.setEnabled(True)
            self.edit.setEnabled(False)
            self.remove.setEnabled(False)

        bookmarks = self.state['bookmarks'].get()
        for bookmark in reversed(bookmarks):
            self.add_bookmark_item(
                bookmark,
                partial(self._remove_bookmark, bookmark)
            )

    def _name_from_context(self, context):
        if context['asset']:
            parts = [context['location'], context['project'], context['asset']]
        elif context['bin']:
            parts = [context['location'], context['project'], context['bin']]
        elif context['project']:
            parts = [context['location'], context['project']]
        elif context['mount']:
            parts = [context['location'], context['mount']]
        elif context['location']:
            parts = [context['location']]
        else:
            parts = []
        return '  /  '.join([p.title() for p in parts])

    def _on_rem_clicked(self):
        bookmark = self._get_bookmark(self.state['uri'].get())
        if bookmark:
            self._remove_bookmark(bookmark)

    def _on_add_or_edit_clicked(self):
        self._cache_bookmark(dict(
            name=self.name.text(),
            uri=self.state['uri'].get(),
            context=dict(self.state['context'].get())
        ))

    def _on_bookmark_clicked(self, item):
        widget = self.list.itemWidget(item)
        bookmark = widget.data
        self.state.set('uri', bookmark['uri'])
        self.state.set('context', bookmark['context'])
        self.list.clearSelection()

    def _remove_bookmark(self, bookmark):
        api = self.state['api'].get()
        bookmarks = api.user_cache.get('bookmarks', [])
        try:
            bookmarks.remove(bookmark)
        except IndexError:
            return

        api.user_cache.set('bookmarks', bookmarks)
        self.state.set('bookmarks', bookmarks)

    def _cache_bookmark(self, bookmark):
        api = self.state['api'].get()
        bookmarks = api.user_cache.get('bookmarks', [])
        for b in bookmarks:
            if b['uri'] == bookmark['uri']:
                b['uri'] = bookmark['uri']
                b['name'] = bookmark['name']
                b['context'] = bookmark['context']
                break
        else:
            bookmarks.append(dict(
                uri=bookmark['uri'],
                name=bookmark['name'],
                context=bookmark['context'],
            ))

        api.user_cache.set('bookmarks', bookmarks)
        self.state.set('bookmarks', bookmarks)

    def _get_bookmark(self, uri):
        bookmarks = self.state['bookmarks'].get()
        for bookmark in bookmarks:
            if uri == bookmark['uri']:
                return bookmark
