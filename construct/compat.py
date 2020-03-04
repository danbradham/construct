# -*- coding: utf-8 -*-
'''
Python2-3 Compatability
-----------------------
Rather than performing variable imports on a module by module basis, all
python compatability issues are handled here. This makes imports throughout
construct slightly neater than otherwise.
'''

# Third party imports
import six


try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

try:
    from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
except ImportError:
    from collections import Mapping, MutableMapping, MutableSequence, Sequence

if six.PY2:
    import functools
    _assignments = functools.WRAPPER_ASSIGNMENTS
    _updates = functools.WRAPPER_UPDATES
    def wraps(wrapped, assigned=_assignments, updated=_updates):
        members = dir(wrapped)
        assigned = set(members) & set(assigned)
        updated = set(members) & set(updated)
        return functools.wraps(wrapped, assigned, updated)

    from itertools import izip_longest as zip_longest
else:
    from functools import wraps
    from itertools import zip_longest

# Instead of python-future
basestring = six.string_types
reraise = six.reraise
