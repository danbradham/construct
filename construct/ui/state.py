# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import contextlib
from copy import deepcopy

# Third party imports
from Qt import QtCore

# Local imports
from ..compat import Mapping, Sequence, basestring


missing = object()


def value_factory(name, default, parent):

    value_map = [
        (basestring, Value),
        (Sequence, SequenceValue),
        (Mapping, MappingValue),
    ]

    for types, value_type in value_map:
        if isinstance(default, types):
            return value_type(name, default, parent)

    return Value(name, default, parent)


class Value(QtCore.QObject):
    '''Base Value type.

    All Value types should emit the changed signal when their internal value
    changes.
    '''

    changed = QtCore.Signal((object,))

    def __init__(self, name, default, parent):
        self.name = name
        self.value = default
        super(Value, self).__init__(parent=parent)

    def get(self):
        return self.value

    def set(self, value):
        old_value = self.value
        self.value = value
        if value != old_value:
            self.changed.emit(value)

    def copy(self):
        if hasattr(self.value, 'copy'):
            return self.value.copy()
        else:
            return deepcopy(self.value)


class SequenceValue(Value):
    '''Value type that handles Sequence Types like list, tuple, and deque.'''

    def __getitem__(self, index):
        return self.value[index]

    def __setitem__(self, index, value):
        self.value[index] = value
        self.changed.emit(self.value)

    def __delitem__(self, index):
        del self.value[index]
        self.changed.emit(self.value)

    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        return len(self.value)

    def extend(self, value):
        self.value.extend(value)
        self.changed.emit(self.value)

    def extendleft(self, value):
        try:
            self.value.extendleft(value)
        except AttributeError:
            value.extend(self.value)
            self.value = value
        self.changed.emit(self.value)

    def remove(self, value):
        self.value.remove(value)
        self.changed.emit(self.value)

    def popleft(self, value):
        try:
            value = self.value.popleft(value)
        except AttributeError:
            value = self.value[0]
            self.value = self.value[1:]
        self.changed.emit(self.value)
        return value

    def pop(self):
        if not len(self.value):
            return
        value = self.value.pop()
        self.changed.emit(self.value)
        return value

    def appendleft(self, value):
        try:
            self.value.appendleft(value)
        except AttributeError:
            self.value.insert(0, value)
        self.changed.emit(self.value)

    def append(self, value):
        self.value.append(value)
        self.changed.emit(self.value)

    def sort(self, key=None):
        old_value = self.value[:]
        self.value.sort(key=key)
        if self.value != old_value:
            self.changed.emit(self.value)


class MappingValue(Value):
    '''Value type that handles Mapping types like Dict.'''

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        self.value[key] = value
        self.changed.emit(self.value)

    def __delitem__(self, key):
        del self.value[key]
        self.changed.emit(self.value)

    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        return len(self.value)

    def __contains__(self, key):
        return key in self.value

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def set(self, *args):
        if len(args) == 1:
            self.value = args[0]
        if len(args) == 2:
            self.value[args[0]] = args[1]
        self.changed.emit(self.value)

    def get(self, key=missing, default=missing):
        if key is missing:
            return self.value
        if key not in self.value:
            if default is not missing:
                return default
            raise KeyError(key)
        return self.value[key]

    def popitem(self, *args):
        item = self.value.popitem(*args)
        self.changed.emit(self.value)
        return item

    def pop(self, *args):
        value = self.value.pop(*args)
        self.changed.emit(self.value)
        return value

    def update(self, *args, **kwargs):
        self.value.update(*args, **kwargs)
        self.changed.emit(self.value)

    def setdefault(self, *args, **kwargs):
        value = self.value.setdefault(*args, **kwargs)
        self.changed.emit(self.value)
        return value

    def items(self):
        return self.value.items()

    def keys(self):
        return self.value.keys()

    def values(self):
        return self.value.values()


class State(QtCore.QObject):

    changed = QtCore.Signal((str, object))

    def __init__(self, **kwargs):
        super(State, self).__init__(kwargs.pop('parent', None))
        self._signals_blocked = False

        self._data = {}
        for k, v in kwargs.items():
            self[k] = v

    def update(self, **kwargs):
        for k, v in kwargs.items():
            self.__setitem__(k, v)

    def get(self, key):
        return self.__getitem__(key)

    def set(self, key, value):
        self.__setitem__(key, value)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        if key not in self._data:
            value = value_factory(key, value, self)
            value.changed.connect(self._change_emitter(key))
            self._data[key] = value
        else:
            obj = self._data[key]
            previous_value = obj.get()
            if previous_value != value:
                obj.set(value)

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def _change_emitter(self, name):
        def emit_changed(value):
            self.changed.emit(name, value)
        return emit_changed

    def block_signals(self, value):
        self._signals_blocked = value
        self.blockSignals(value)
        for v in self._data.values():
            v.blockSignals(value)

    @contextlib.contextmanager
    def signals_blocked(self):
        self.block_signals(True)
        try:
            yield
        finally:
            self.block_signals(False)
