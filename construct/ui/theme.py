# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import logging
import re

# Third party imports
import qtsass

# Local imports
from ..compat import basestring, wraps
from ..types import WeakSet
from . import resources
from .scale import pt, px


_log = logging.getLogger(__name__)


def ensure_loaded(method):
    '''A decorator that ensures an objects resources are loaded before
    executing.
    '''

    @wraps(method)
    def call_method(self, *args, **kwargs):
        self.load()
        resources = getattr(self, 'resources', None)
        if resources:
            resources.load()
        return method(self, *args, **kwargs)
    return call_method


def clamp(value, lower, upper):
    '''Clamp a value between lower and upper bounds

    Arguments:
        value (int or float): the number to clamp
        lower (int or float): the lower bound
        upper (int or float): the upper bound
    '''
    return max(lower, min(value, upper))


def rgb_to_hex(r, g, b, a=None):
    '''Convert r, g, b ints to a hex string.

    Arguments:
        r (int): Red value between 0 and 255
        g (int): Green value between 0 and 255
        b (int): Blue value between 0 and 255
        a (int): OPTIONAL - Alpha value between 0 and 255
    Returns:
        Hex string in "#RRGGBB" or "#RRGGBBAA" format
    '''

    code = '#{:02x}{:02x}{:02x}'.format(
        clamp(r, 0, 255),
        clamp(g, 0, 255),
        clamp(b, 0, 255),
    )
    if a:
        code += '{:02x}'.format(clamp(a, 0, 255))
    return code


def is_rgb(value):
    '''Return True if value is an rgb or rgba sequence.'''

    return isinstance(value, (tuple, list)) and len(value) in (3, 4)


def hex_to_rgb(code):
    '''Convert a hex code to rgb tuple.

    Arguments:
        code (str): Hex code string like #FFFFFF
    Returns:
        Tuple of ints - (r, g, b) or (r, g, b, a)
    '''

    return tuple([ord(i) for i in code[1:].decode('hex')])


def is_hex_code(value):
    '''Return True if value is a hex code'''

    if not isinstance(value, basestring):
        return False
    if value.startswith('#'):
        return True


class Theme(object):
    """Represents the UI Font and Color theme.

    Colors are based on the Material design color system. All attributes can
    be passed to the constructor. Colors can be passed as either Hex strings
    or RGB tuples.

    Attributes:
        name (str): name of the theme
        resources (Resource): resource object
        stylesheet (str): The compiled stylesheet

    Font Attributes:
        font_stack (str): Comma separated list of font-families
        font_size (str): Font point size
        font_weight (str): Font weight

    Color Attributes:
        primary (color): Used for accents and emphasis
        primary_variant (color): Variant of primary color
        on_primary (color): Color of type and icons on primary
        alert (color): Indicates warnings and alerts
        error (color): Indicates error
        success (color): Indicates success
        info (color): Indicates info
        on_secondary (color): Color of type and icons on secondary colors
        background (color): Used for underlying background fill
        on_background (color): Color of type and icons on background
        surface (color): Background color of most cards and widgets
        on_surface (color): Color of type on surface

    Arguments:
        resources (Resource): Used to lookup icons, pixmaps, and images
        **options: Pass any of the font or color attributes listed above
    """

    defaults = dict(
        name='default',
    )
    color_variables = [
        'primary',
        'primary_variant',
        'on_primary',
        'alert',
        'error',
        'success',
        'info',
        'on_secondary',
        'background',
        'on_background',
        'surface',
        'on_surface',
    ]
    variables = list(defaults.keys())

    def __init__(self, resources, **options):
        self.__dict__.update(**self.defaults)
        self.__dict__.update(**options)
        self.resources = resources
        self._stylesheet = None
        self._widgets = WeakSet()
        self._signals = None
        self._loaded = False

    def load(self):
        '''Creates a QObject used to dispatch on_theme_changed callbacks.'''

        if self._loaded:
            return

        from Qt.QtCore import QObject, Signal

        class ThemeSignals(QObject):
            changed = Signal(str)

        self._signals = ThemeSignals()
        self._signals.changed.connect(self.on_theme_changed)

        self._loaded = True

    def set_resources(self, resources):
        '''Sets the resources this theme uses'''

        self.resources = resources

    @ensure_loaded
    def apply(self, widget):
        '''Applies this theme to a widget and adds the widget to an internal
        set. If the theme changes, the theme will be reapplied.
        '''

        widget.setStyleSheet(self.stylesheet)
        self._widgets.add(widget)

    @property
    def stylesheet(self):
        if not self._stylesheet:
            self._stylesheet = self.compile_stylesheet()
        return self._stylesheet

    def compile_stylesheet(self):
        '''Compile a stylesheet for this theme.'''

        sass = ''
        var_tmpl = '${}: {};\n'
        rgb_tmpl = '${}: rgb({}, {}, {});\n'
        rgba_tmpl = '${}: rgba({}, {}, {}, {});\n'
        for var in self.color_variables:
            if not hasattr(self, var):
                continue
            value = getattr(self, var)
            if isinstance(value, basestring):
                sass += var_tmpl.format(var, value)
            elif isinstance(value, (tuple, list)):
                if len(value) == 3:
                    sass += rgb_tmpl.format(var, *value)
                elif len(value) == 4:
                    sass += rgba_tmpl.format(var, *value)
                else:
                    raise ValueError(
                        '%s: Expected a length or 3 or 4 got %s.' %
                        (var, len(value))
                    )
            else:
                raise TypeError(
                    '%s: Expected (str, tuple) got %s' %
                    (var, type(value))
                )

        sass += "@import 'theme'"

        css = qtsass.compile(
            sass,
            include_paths=[
                str(self.resources.path / 'styles'),
            ],
            custom_functions={
                'resource': sass_resource(self),
            },
        )

        # Scale pixel values
        def dpiaware_scale(value):
            value, unit = int(value.group(1)), value.group(2)
            return str(px(value)) + unit

        css = re.sub(r'(\d+)(px)', dpiaware_scale, css)

        return css

    def refresh_stylesheet(self):
        '''Recompile stylesheet and reapply to all themed widgets.'''
        self._stylesheet = self.compile_stylesheet()
        if self._signals:
            self._signals.changed.emit(self.stylesheet)
        else:
            self.on_theme_changed()

    def on_theme_changed(self):
        '''Reapplies stylesheet to all themed widgets.'''

        for widget in self._widgets:

            # Reapply to registered widget
            widget.setStyleSheet(self.stylesheet)

            # Reapply Stylesheet to children
            children = widget.children()
            while children:
                child = children.pop()
                if hasattr(child, 'setStyleSheet'):
                    child.setStyleSheet(self.stylesheet)
                if hasattr(child, 'children'):
                    children.extend(child.children())

    def set_color(self, name, value):
        '''Set a color value for this theme.

        Colors are converted to hex codes here.

        Arguments:
            name (str): Name of color attribute to set
            value (tuple or str): rgb tuple or hex code
        '''
        if name not in self.color_variables:
            raise NameError('"%s" is not a valid color.' % name)

        if is_rgb(value):
            setattr(self, name, rgb_to_hex(*value))
        elif is_hex_code(value):
            setattr(self, name, value)
        else:
            raise ValueError('Expected rgb tuple or hex code got %s' % value)

        self.refresh_stylesheet()

    def hex(self, name):
        '''Return the named color as a hex code string.'''

        if name not in self.color_variables:
            raise NameError('"%s" is not a valid color.' % name)

        return getattr(self, name)

    def rgb(self, name):
        '''Return the named color as an rgb tuple.'''

        if name not in self.color_variables:
            raise NameError('"%s" is not a valid color.' % name)

        return hex_to_rgb(getattr(self, name))

    @ensure_loaded
    def pixmap(self, resource, size=None, family=None):
        '''Get a pixmap for a resource.

        Arguments:
            resource (str):  Path relative to Construct PATH or font icon name
            size (tuple): Size of pixmap to return
            family (str): Font family for font icon character (optional)
        '''

        from Qt import QtCore
        from Qt.QtGui import QPixmap, QIcon
        from .widgets import FontIcon

        if size:
            size = QtCore.QSize(*px(*size))
        else:
            size = QtCore.QSize(*px(24, 24))

        path = self.resources.get(resource, None)
        if path:
            if path.suffix == '.svg':
                return QIcon(str(path)).pixmap(size)
            elif path.suffix in self.resources.image_extensions:
                return QPixmap(str(path), size)
            else:
                raise TypeError("Can't create a pixmap for %s" % str(path))

        char = self.resources.get_char(resource, family)
        return FontIcon(char, family).pixmap(size)

    @ensure_loaded
    def icon(self, resource, family=None, parent=None):
        '''Get a QIcon for a resource.

        Arguments:
            resource (str): Path relative to Construct PATH or font icon name
            family (str): Font family for font icon character (optional)
            parent (QWidget): Parent QWidget of QIcon - used for coloring
        '''

        from Qt.QtGui import QIcon
        from .widgets import SvgIcon, FontIcon

        path = self.resources.get(resource, None)
        if path:
            if path.suffix == '.svg':
                return SvgIcon(str(path), parent)
            elif path.suffix in self.resources.image_extensions:
                return QIcon(str(path))
            else:
                raise TypeError("Can't create a pixmap for %s" % str(path))

        char = self.resources.get_char(resource, family)
        return FontIcon(char, family, parent)


# Sass functions

def sass_resource(theme):
    '''Get an url for a construct resource.

    Usage:
        QPushButton {qproperty-icon: resource(icons/plus.svg);}
    '''
    def resolve_resource(resource):
        return 'url("%s")' % theme.resources.get(resource).as_posix()
    return resolve_resource


def sass_scale_pt(theme):
    '''Convert pt value to dpi aware pixel value.

    Usage:
        QPushButton {padding: scale_pt(8 24 8 24)}
        QLabel {margin-left: scale_pt(8); margin-right: scale_pt(8);}
    '''
    def scale_pt(value):
        if isinstance(value, float):
            return str(pt(value))

        # Handle sass types
        import sass
        if isinstance(value, sass.SassNumber):
            return str(pt(value.value)) + value.unit

        if isinstance(value, sass.SassList):
            result = []
            for item in value.items:
                result.append(str(pt(item.value)) + item.unit)
            return ' '.join(result)
    return scale_pt


def sass_scale_px(theme):
    '''Convert pixel value to dpi aware pixel value.

    Usage:
        QPushButton {padding: scale_px(8 24 8 24)}
        QLabel {margin-left: scale_px(8); margin-right: scale_px(8);}
    '''

    def scale_px(value):
        if isinstance(value, float):
            return str(px(value))

        # Handle sass types
        import sass
        if isinstance(value, sass.SassNumber):
            return str(px(value.value)) + value.unit

        if isinstance(value, sass.SassList):
            result = []
            for item in value.items:
                result.append(str(px(item.value)) + item.unit)
            return ' '.join(result)
    return scale_px


# Theme singleton
theme = Theme(resources.Resources([]))
