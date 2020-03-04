# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
from collections import deque
from functools import partial

# Third party imports
from Qt import QtCore, QtWidgets

# Local imports
from ...context import Context
from .. import models
from ..dialogs import BookmarksDialog
from ..layouts import HBarLayout, VBarLayout
from ..scale import px
from ..state import State
from ..theme import theme
from ..widgets import Frameless, Header, HLine, IconButton, Navigation, Sidebar


class App(Frameless, QtWidgets.QDialog):

    css_id = ''
    css_properties = {
        'theme': 'surface',
        'border': True,
        'windowTitle': 'Construct',
        'windowIcon': theme.resources.get('icons/construct.svg'),
    }

    def __init__(self, api, context=None, uri=None, **kwargs):
        super(App, self).__init__(**kwargs)

        # Set App state
        if uri and not context:
            context = api.context_from_uri(uri)
        else:
            context = context or api.get_context()
            uri = api.uri_from_context(context)

        self.state = State(
            api=api,
            context=context,
            uri=uri,
            bookmarks=api.user_cache.get('bookmarks', []),
            crumb_item=None,
            history=deque(api.user_cache.get('history', []), maxlen=20),
            tree_model=None,
            selection=[],
        )
        self.state['context'].changed.connect(self._on_ctx_changed)
        self.state['uri'].changed.connect(self._on_uri_changed)
        self.state['crumb_item'].changed.connect(self._on_crumb_item_changed)
        self.state['bookmarks'].changed.connect(self._refresh_bookmark_button)
        self.state['selection'].changed.connect(self._on_selection_changed)

        # Create widgets
        self.header = Header('Launcher', parent=self)
        self.header.close_button.clicked.connect(self.hide)

        self.navigation = Navigation(parent=self)
        self.navigation.menu_button.clicked.connect(self._show_main_menu)
        self.navigation.home_button.clicked.connect(self._on_home_clicked)
        self.navigation.uri_changed.connect(self._on_uri_changed)
        self.navigation.bookmark_button.clicked.connect(self._show_bookmarks)

        self.sidebar = Sidebar(self.state, parent=self)
        self.body = QtWidgets.QWidget()

        self.splitter = QtWidgets.QSplitter(parent=self)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.body)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        # Layout widgets
        self.layout = VBarLayout(parent=self)
        self.layout.setContentsMargins(*px(1, 1, 1, 1))
        self.layout.setSpacing(0)
        self.layout.top.setSpacing(0)
        self.layout.top.addWidget(self.header)
        self.layout.top.addWidget(self.navigation)
        self.layout.top.addWidget(HLine(self))
        self.layout.center.addWidget(self.splitter)
        self.setLayout(self.layout)

        # Window Attributes
        self.setWindowFlags(
            self.windowFlags() |
            QtCore.Qt.Window
        )
        self.setMinimumSize(*px(600, 600))
        self.resize(*px(800, 600))
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

        # Apply theme
        theme.apply(self)

        # Update UI from initial state
        self._build_crumbs(self.state['context'].copy())
        self._refresh_bookmark_button(self.state['uri'].get())

        api.register_menu('crumb', self._on_crumb_menu_requested)

    def _show_main_menu(self):
        api = self.state['api'].get()
        menu = QtWidgets.QMenu(parent=self)
        menu.addAction('Toggle Tree')
        menu.addAction('Settings')
        menu = api.ui.request_menu(
            identifier='main',
            context=self.state['context'].copy(),
            menu=menu,
        )
        button = self.navigation.menu_button
        pos = button.mapToGlobal(button.rect().bottomLeft())
        menu.popup(pos)

    def _on_home_clicked(self):
        api = self.state['api'].get()
        context = Context(
            host=api.context['host']
        )
        self.state.set('context', context)

        with self.state.signals_blocked():
            self.state.set('uri', '')

    def _on_uri_changed(self, uri):
        api = self.state['api'].get()
        context = api.context_from_uri(uri)

        if api.validate_context(context):
            self.state.set('context', context)

    def _on_ctx_changed(self, context):
        api = self.state['api'].get()

        with self.state.signals_blocked():
            # Setting uri state will update context: see _on_uri_changed
            # By blocking signals here we prevent a loop
            uri = api.uri_from_context(context)
            self.state.set('uri', uri)

        self._refresh_bookmark_button(uri)
        self._refresh_crumbs(context)
        self.state['history'].appendleft((uri, dict(context)))

    def _refresh_bookmark_button(self, *args):
        uri = self.state['uri'].get()
        is_bookmarked = False
        for bookmark in self.state['bookmarks'].get():
            if uri == bookmark['uri']:
                is_bookmarked = True

        self.navigation.bookmark_button.set_icon(
            ('bookmark_outline', 'bookmark')[is_bookmarked]
        )

    def _show_bookmarks(self, value):
        dialog = BookmarksDialog(self.state, parent=self)
        dialog.finished.connect(
            lambda x: self.navigation.bookmark_button.setChecked(False)
        )
        dialog.show()
        dialog.setFocus()

        # Reposition dialog
        button = self.navigation.bookmark_button
        anchor = button.mapToGlobal(button.rect().bottomRight())
        dialog_anchor = dialog.mapToGlobal(dialog.rect().topRight())
        dialog_source = dialog.mapToGlobal(dialog.rect().topLeft())
        dialog.move(
            dialog_source + (anchor - dialog_anchor) + QtCore.QPoint(0, 1)
        )

    def _on_crumb_item_changed(self, value):
        for crumb in self.navigation.crumbs.iter():
            if crumb.label.text() == value:
                if not crumb.arrow.isHidden():
                    crumb.arrow.setFocus()
                else:
                    crumb.label.setFocus()

    def _build_crumb_menu(self, crumb, key):
        api = self.state['api'].get()
        context = self.state['context'].copy()
        crumb.menu.clear()
        menu_items = []
        if key == 'home':
            locations = api.get_locations()
            menu_context = Context(host=context['host'])
            for location in locations.keys():
                item_context = Context(
                    host=context['host'],
                    location=location,
                )
                menu_items.append((location, item_context))
        elif key == 'location':
            mounts = api.get_locations()[context['location']]
            menu_context = Context(
                host=context['host'],
                location=context['location'],
            )
            for mount in mounts.keys():
                item_context = Context(
                    host=context['host'],
                    location=context['location'],
                    mount=mount,
                )
                menu_items.append((mount, item_context))
        elif key == 'mount':
            with api.set_context(context):
                projects = api.io.get_projects()
            menu_context = Context(
                host=context['host'],
                location=context['location'],
                mount=context['mount'],
            )
            menu_items = []
            for project in projects:
                item_context = Context(
                    host=context['host'],
                    location=context['location'],
                    mount=context['mount'],
                    project=project['name'],
                )
                menu_items.append((project['name'], item_context))
        elif key == 'project':
            with api.set_context(context):
                project = api.io.get_project(
                    context['project'],
                )
            menu_context = Context(
                host=context['host'],
                location=context['location'],
                mount=context['mount'],
                project=context['project'],
            )
            menu_items = []
            for bin in project['bins'].values():
                item_context = Context(
                    host=context['host'],
                    location=context['location'],
                    mount=context['mount'],
                    project=context['project'],
                    bin=bin['name'],
                )
                menu_items.append((bin['name'], item_context))
        elif key == 'bin':
            with api.set_context(context):
                project = api.io.get_project(
                    context['project'],
                )
            menu_context = Context(
                host=context['host'],
                location=context['location'],
                mount=context['mount'],
                project=context['project'],
                bin=context['bin'],
            )
            menu_items = []
            for asset in project['assets'].values():
                if asset['bin'] != context['bin']:
                    continue
                item_context = Context(
                    host=context['host'],
                    location=context['location'],
                    mount=context['mount'],
                    project=context['project'],
                    bin=asset['bin'],
                    asset=asset['name'],
                )
                menu_items.append((asset['name'], item_context))
        elif key == 'asset':
            menu_context = Context(
                host=context['host'],
                location=context['location'],
                mount=context['mount'],
                project=context['project'],
                bin=context['bin'],
                asset=context['asset'],
            )

        api.ui.request_menu(
            identifier='crumb',
            context=menu_context,
            menu=crumb.menu
        )
        crumb.menu.addSeparator()

        for item_label, item_context in menu_items:
            callback = partial(
                self.state.update,
                context=item_context,
                crumb_item=item_label,
            )
            crumb.menu.addAction(item_label, callback)

    def _on_crumb_menu_requested(self, menu, ctx):
        if ctx['bin']:
            menu.addAction('New Asset')
        elif ctx['project']:
            menu.addAction('New Bin')
        elif ctx['mount']:
            menu.addAction('New Project')
        elif ctx['location']:
            menu.addAction('New Mount')
        else:
            menu.addAction('New Location')

    def _on_crumb_clicked(self, key):
        context = self.state['context'].copy()
        crumb_context = context.trim(key)
        self.state.update(
            context=crumb_context,
            crumb_item=crumb_context[key],
        )

    def _refresh_crumbs(self, context):
        api = self.state['api'].get()
        if context['project'] and not context['mount']:
            with api.set_context(context):
                p = api.io.get_project(context['project'])
                path = api.io.get_path_to(p)
            _, mount = api.get_mount_from_path(path)
            context['mount'] = mount

        for crumb in self.navigation.crumbs.iter():
            if crumb.key == 'home':
                continue
            label = context[crumb.key] or ''
            crumb.label.setText(label)
            crumb.setVisible(bool(label))

    def _build_crumbs(self, context):
        # Add home arrow
        crumb = self.navigation.crumbs.add('')
        crumb.key = 'home'
        crumb.label.hide()
        crumb.menu.aboutToShow.connect(partial(
            self._build_crumb_menu,
            crumb,
            'home',
        ))

        # Add context crumbs
        for key in ['location', 'mount', 'project', 'bin', 'asset']:
            label = context[key] or ''
            crumb = self.navigation.crumbs.add(label)
            crumb.key = key
            crumb.label.clicked.connect(partial(
                self._on_crumb_clicked,
                key
            ))
            crumb.menu.aboutToShow.connect(partial(
                self._build_crumb_menu,
                crumb,
                key,
            ))
            if not context[key]:
                crumb.hide()
            if key == 'asset':
                crumb.arrow.hide()

        # Update tab focus order
        self.navigation._update_focus_order()

    def _on_sidebar_clicked(self, index):
        pass

    def _on_selection_changed(self, selection):
        print(selection)
