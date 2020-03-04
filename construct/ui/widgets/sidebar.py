# -*- coding: utf-8 -*-

# Third party imports
from Qt import QtCore, QtGui, QtWidgets

# Local imports
from .. import models
from ..scale import px
from . import Button, HLine, IconButton, Widget


__all__ = [
    'Sidebar',
]


class SidebarTree(Widget, QtWidgets.QTreeView):

    css_id = 'SidebarTree'
    css_properties = {}
    selection_changed = QtCore.Signal(object, object)

    def __init__(self, *args, **kwargs):
        super(SidebarTree, self).__init__(*args, **kwargs)
        self.setHeaderHidden(True)
        self.expandAll()
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )

    def select_by_name(self, *items):
        sel = self.selectionModel()
        model = self.model()

        selection = QtCore.QItemSelection()
        for item in items:
            index = model.match(
                model.index(0, 0),
                QtCore.Qt.DisplayRole,
                item,
                1,
                QtCore.Qt.MatchRecursive
            )
            if index:
                selection.merge(
                    QtCore.QItemSelection(index[0], index[0]),
                    sel.Select,
                )

        sel.blockSignals(True)
        sel.clear()
        sel.select(selection, sel.Select)
        sel.blockSignals(False)
        self.update()

    def get_selected_data(self):
        items = []
        for index in self.selectionModel().selectedIndexes():
            items.append(self.get_data(index))
        return items

    def get_data(self, index):
        proxy = self.model()
        model = proxy.sourceModel()
        index = proxy.mapToSource(index)
        return model.getNode(index).value()

    def get_parent(self, index):
        proxy = self.model()
        model = proxy.sourceModel()
        index = proxy.mapToSource(index)
        return self.get_data(model.parent(index))

    def selectionChanged(self, next, prev):
        self.selection_changed.emit(self.get_selected_data(), None)
        super(SidebarTree, self).selectionChanged(next, prev)


class SidebarTools(Widget, QtWidgets.QWidget):

    css_id = 'SidebarTools'
    css_properties = {}

    def __init__(self, *args, **kwargs):
        super(SidebarTools, self).__init__(*args, **kwargs)

        self.filter_button = IconButton(
            icon='filter',
            icon_size=(24, 24),
            parent=self,
        )
        self.filter = QtWidgets.QLineEdit(parent=self)
        self.filter.setPlaceholderText('Filter')
        self.menu_button = IconButton(
            icon='menu_dots',
            icon_size=(24, 24),
            parent=self,
        )

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setStretch(1, 1)
        self.layout.setContentsMargins(*px(16, 8, 8, 8))
        self.layout.addWidget(self.filter_button)
        self.layout.addWidget(self.filter)
        self.layout.addWidget(self.menu_button)
        self.setLayout(self.layout)


class SidebarTabs(Widget, QtWidgets.QWidget):

    css_id = 'SidebarTabs'
    css_properties = {
        'theme': 'surface',
    }
    changed = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        super(SidebarTabs, self).__init__(*args, **kwargs)

        self.tabs = []
        self.tabs_group = QtWidgets.QButtonGroup(parent=self)
        self.tabs_group.setExclusive(True)
        self.tabs_group.buttonClicked.connect(self.changed.emit)

        self.add_button = IconButton(
            icon='plus',
            icon_size=(14, 14),
            parent=self,
        )

        self.left = QtWidgets.QHBoxLayout()
        self.left.setContentsMargins(0, 0, 0, 0)
        self.left.setSpacing(0)

        self.right = QtWidgets.QHBoxLayout()
        self.right.addWidget(self.add_button)
        self.right.setContentsMargins(*px(8, 8, 8, 8))

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.left)
        self.layout.addLayout(self.right)
        self.layout.addStretch(1)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.layout)
        self.setFixedHeight(px(36))
        self.setMinimumWidth(px(256))

    def get(self):
        return self.tabs_group.checkedButton().text()

    def set(self, label):
        for tab in list(self.tabs):
            if tab.text() == label:
                tab.setChecked(True)

    def add(self, label, icon=None):
        tab = Button(label, icon=icon, parent=self)
        tab.setObjectName('tab')
        tab.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Maximum
        )
        tab.setFixedHeight(px(36))
        tab.setCheckable(True)
        tab.setChecked(True)
        self.tabs.append(tab)
        self.left.addWidget(tab)
        self.tabs_group.addButton(tab)
        return tab

    def remove(self, label):
        for tab in list(self.tabs):
            if tab.text() == label:
                self.tabs_group.removeButton(tab)
                self.tabs.remove(tab)
                tab.setParent(None)
                tab.deleteLater()

    def clear(self):
        while self.tabs:
            tab = self.tabs.pop()
            self.tabs_group.removeButton(tab)
            tab.setParent(None)
            tab.deleteLater()


class SidebarBase(Widget, QtWidgets.QWidget):

    css_id = 'Sidebar'
    css_properties = {
        'theme': 'surface',
    }

    def __init__(self, *args, **kwargs):
        super(SidebarBase, self).__init__(*args, **kwargs)

        self.tabs = SidebarTabs(parent=self)
        self.tools = SidebarTools(parent=self)
        self.tree = SidebarTree(parent=self)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setStretch(3, 1)
        self.layout.addWidget(self.tabs)
        self.layout.addWidget(self.tools)
        self.layout.addWidget(HLine(self))
        self.layout.addWidget(self.tree)
        self.setLayout(self.layout)

        self.setMinimumWidth(px(200))
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )


class Sidebar(SidebarBase):

    def __init__(self, state, *args, **kwargs):
        super(Sidebar, self).__init__(*args, **kwargs)
        self.state = state
        self._selection_disabled = False

        self.tabs.changed.connect(self._on_tab_changed)
        self.tree.doubleClicked.connect(self._on_tree_doubleClicked)
        self.tree.selection_changed.connect(self._on_tree_selection)
        self.tools.filter.textChanged.connect(self._on_filter_text_changed)

        self.state['context'].changed.connect(self._refresh)
        self.state['tree_model'].changed.connect(self._on_tree_model_changed)

        self._suppress_refresh = False
        self._refresh(self.state['context'].copy())

    def _on_filter_text_changed(self, text):
        model = self.state['tree_proxy_model'].get()
        model.setFilterRegExp(text)
        self.tree.expandAll()

    def _tree_requires_refresh(self, tree_context, context):
        for key in ['location', 'mount', 'project', 'bin']:
            if context.get(key, None) != tree_context.get(key, None):
                return True
        return False

    def _selection_requires_refresh(self, tree_context, context):
        for key in ['asset', 'project', 'mount']:
            if context.get(key, None) != tree_context.get(key, None):
                return True
        return False

    def _refresh(self, context):

        api = self.state['api'].get()
        context = context.copy()
        proxy = self.tree.model()
        if not proxy:
            tree_context = {}
        else:
            tree_context = proxy.sourceModel().context()

        self.tree.blockSignals(True)

        if self._tree_requires_refresh(tree_context, context):
            with api.set_context(context):
                if context['project']:
                    self.tree.setSelectionMode(
                        self.tree.ExtendedSelection
                    )
                    project = api.io.get_project(
                        context['project'],
                        context['location'],
                        context['mount'],
                    )
                    bin = context['bin'] or next(iter(project['bins']))
                    context['bin'] = bin

                    model = models.AssetsTreeModel(api, context, project, bin)
                    self._refresh_project_tabs(context, project, bin)
                elif context['location']:
                    self.tree.setSelectionMode(
                        self.tree.SingleSelection
                    )

                    mount = context['mount']
                    locations = api.get_locations()
                    mount = mount or next(iter(locations[context['location']]))
                    context['mount'] = mount

                    model = models.ProjectsTreeModel(api, context, mount)
                    self._refresh_location_tabs(context, mount)
                else:
                    self.tree.setSelectionMode(
                        self.tree.SingleSelection
                    )
                    self.tabs.hide()
                    model = models.LocationsTreeModel(api, context)

            self.state.set('tree_model', model)

        if self._selection_requires_refresh(tree_context, context):
            for item in ['asset', 'project', 'mount']:
                if context[item]:
                    self.tree.select_by_name(context[item])
                    break

        self.tree.blockSignals(False)

    def _refresh_project_tabs(self, context, project, bin):
        bins = sorted(project['bins'].items(), key=lambda b: b[1]['order'])
        self.tabs.clear()
        self.tabs.show()
        self.tabs.add_button.show()
        for bin_name, bin_data in bins:
            self.tabs.add(bin_name)

        self.tabs.set(bin)

    def _refresh_location_tabs(self, context, mount):
        api = self.state['api'].get()

        self.tabs.clear()
        self.tabs.show()
        self.tabs.add_button.hide()

        locations = api.get_locations()
        mounts = list(locations[context['location']])
        for mount_name in mounts:
            self.tabs.add(mount_name)

        self.tabs.set(mount)

    def _on_tab_changed(self, *args):
        context = self.state['context'].copy()
        tab_value = self.tabs.get()
        tab_key = None

        if context['project']:
            tab_key = 'bin'
        elif context['location']:
            tab_key = 'mount'
        else:
            return

        context = context.trim(tab_key)
        context[tab_key] = tab_value
        self.state.set('context', context)

    def _on_tree_doubleClicked(self, index):
        data = self.tree.get_data(index)

        if data['_type'] in ['location']:
            return

        new_context = {data['_type']: data['name']}
        if data['_type'] == 'mount':
            new_context['location'] = data['location']

        if data['_type'] in self.state['context']:
            context = self.state['context'].copy().trim(data['_type'])
            context.update(new_context)
            self.state.set('context', context)

    def _on_tree_selection(self, selection, prev_selection):
        self._suppress_refresh = True
        context = self.state['context'].copy()
        if selection:
            first = selection[0]
            if (
                first['_type'] == 'asset' and
                context['asset'] != first['name']
            ):
                context = context.trim('asset')
                context.update(bin=first['bin'], asset=first['name'])
                self.state.set('context', context)
            return

        if context['asset'] or context['bin']:
            context = context.trim('bin')
            self.state.set('context', context)
        elif context['project']:
            context = context.trim('project')
            self.state.set('context', context)

        self.state.set('selection', selection)
        self._suppress_refresh = False

    def _on_tree_model_changed(self, model):
        self.tree.blockSignals(True)
        proxy_model = QtCore.QSortFilterProxyModel(self.tree)
        proxy_model.setSourceModel(model)
        proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.state.set('tree_proxy_model', proxy_model)
        self.tree.setModel(proxy_model)
        self.tree.expandAll()
        self.tools.filter.setText('')
        self.tree.blockSignals(False)
