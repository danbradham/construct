# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Third party imports
from Qt import QtCore, QtWidgets

# Local imports
from ..scale import px
from ..theme import theme


class Node(object):

    def __init__(self, value, parent=None):
        self._value = value
        self._parent = parent
        self._children = []

        if parent:
            parent.addChild(self)

    def context(self):
        return self._value.get('context', {})

    def isTopLevel(self):
        return self.parent() and not self.parent().parent()

    def type(self):
        return self._value.get('_type', 'group')

    def value(self):
        return self._value

    def parent(self):
        return self._parent

    def row(self):
        return self._parent._children.index(self)

    def child(self, row):
        try:
            return self._children[row]
        except IndexError:
            pass

    def children(self):
        return self._children

    def addChild(self, node):
        self._children.append(node)

    def insertChild(self, index, child):
        try:
            self._children.insert(index, child)
            child._parent = self
            return True
        except IndexError:
            return False

    def removeChild(self, index):

        try:
            child = self._children.pop(index)
            child._parent = None
            return True
        except IndexError:
            return False

    def childCount(self):
        return len(self._children)

    def data(self, column):
        if column == 0:
            return self._value['name']

    def setData(self, column, value):
        if column == 0:
            self._value['name'] = value


class TreeModel(QtCore.QAbstractItemModel):

    selectable_types = ['mount', 'project', 'asset']

    def __init__(self, root=None, parent=None):
        super(TreeModel, self).__init__(parent)
        self._root = root or Node({'name': 'root'})

    def root(self):
        return self._root

    def context(self):
        return self._root.context()

    def type(self):
        return self._type

    def flags(self, index):
        if not index.isValid():
            return None

        node = self.getNode(index)
        if node.type() in self.selectable_types:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

        return QtCore.Qt.ItemIsEnabled

    def getNode(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node
        return self._root

    def parent(self, index):
        node = self.getNode(index)
        parent = node.parent()

        if self._root in [node, parent]:
            return QtCore.QModelIndex()

        return self.createIndex(parent.row(), 0, parent)

    def index(self, row, column, index=QtCore.QModelIndex()):
        parent = self.getNode(index)
        child = parent.child(row)

        if child:
            return self.createIndex(row, column, child)
        else:
            return QtCore.QModelIndex()

    def rowCount(self, index):
        if not index.isValid():
            parent = self._root
        else:
            parent = index.internalPointer()

        return parent.childCount()

    def columnCount(self, index):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(px(32), px(32))

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return node.data(index.column())

        if role == QtCore.Qt.DecorationRole:
            # if node.type() == 'group':
            #     return theme.icon('folder')
            # return theme.icon('square')
            return

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if index.isValid():
            if role == QtCore.Qt.EditRole:
                node = index.internalPointer()
                node.setData(index.column(), value)
                return True
        return False

    def insertRows(self, row, rows, parent=QtCore.QModelIndex()):
        parent = self.getNode(parent)

        self.beginInsertRows(parent, row, row + rows - 1)

        for row in range(rows):
            child = Node({'name': 'Untitled'})
            success = parent.insertChild(row, child)

        self.endInsertRows()
        return success

    def removeRows(self, row, rows, parent=QtCore.QModelIndex()):
        parent = self.getNode(parent)
        self.beginRemoveRows(parent, row, row + rows - 1)

        for row in range(rows):
            success = parent.removeChild(row)

        self.endRemoveRows()
        return success


class TreeItemDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent):
        super(TreeItemDelegate, self).__init__(parent)

    def sizeHint(self, option, index):
        if not index:
            return super(TreeItemDelegate, self).sizeHint(option, index)

        node = option.widget.model().getNode(index)
        return QtCore.QSize(*px(32, 32))

    def paint(self, painter, option, index):
        if not index:
            return super(TreeItemDelegate, self).paint(painter, option, index)

        self.initStyleOption(option, index)

        node = option.widget.model().getNode(index)

        groups = ['group', 'mount', 'location', 'bin']
        if node.isTopLevel() and node.type() in groups:
            option.font.setPixelSize(px(16))
        else:
            option.font.setPixelSize(px(14))

        super(TreeItemDelegate, self).paint(painter, option, index)


def LocationsTreeModel(api, context, parent=None):
    '''Create a hierarchy of Node objects from a locations dict.'''

    root = Node({'name': 'root', 'context': context})

    for location, mounts in sorted(api.get_locations().items()):
        parent_node = Node({'name': location, '_type': 'location'}, root)
        for mount, path in sorted(mounts.items()):
            Node(
                {
                    '_type': 'mount',
                    'name': mount,
                    'location': location,
                    'path': path,
                },
                parent_node,
            )

    return TreeModel(root, parent)


def MountsProjectsTreeModel(api, context, parent=None):
    '''Create a hierarchy of Node objects from a list of projects.'''

    root = Node({'name': 'root', 'context': context})

    mounts = api.get_locations()[context['location']]
    for mount, path in sorted(mounts.items()):
        parent_node = Node(
            {
                '_type': 'mount',
                'name': mount,
                'location': context['location'],
                'path': path,
            },
            root
        )
        projects = api.io.get_projects(context['location'], mount)
        for project in sorted(projects, key=lambda p: p['name']):
            Node(project, parent_node)

    return TreeModel(root, parent)


def ProjectsTreeModel(api, context, mount, parent=None):
    '''Create a hierarchy of Node objects from a list of projects.'''

    root = Node({'name': 'root', 'context': context})
    projects = api.io.get_projects(context['location'], mount)
    for project in sorted(projects, key=lambda p: p['name']):
        Node(project, root)

    return TreeModel(root, parent)


def AssetsTreeModel(api, context, project, bin, parent=None):
    '''Create a hierarchy of Node objects from a list of assets.'''

    root = Node({'name': 'root', 'context': context})
    assets = list(api.io.get_assets(project, bin=bin))

    groups = {}
    sorted_assets = sorted(
        assets,
        key=lambda a: (a['group'] or 'ZZ', a['name'])
    )
    for asset in sorted_assets:

        parent_node = root

        if bin is None:
            asset_bin = asset['bin']
            if asset_bin and asset_bin not in groups:
                groups[asset_bin] = Node(
                    {'name': asset_bin, '_type': 'bin'},
                    root
                )

            parent_node = groups.get(asset_bin, root)

        group = asset['group']
        if group and (bin, group) not in groups:
            groups[(bin, group)] = Node(
                {'name': group, '_type': 'group'},
                parent_node
            )

        parent_node = groups.get((bin, group), parent_node)
        Node(asset, parent_node)

    return TreeModel(root, parent)
