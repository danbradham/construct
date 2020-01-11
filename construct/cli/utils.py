# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Standard library imports
import sys

# Third party imports
import colorama


def error(msg):
    print(styled('{bright}{fg.red}Error! {reset}{}', msg))


def abort(msg=''):
    print(styled('{bright}{fg.yellow}Abort! {reset}{}', msg))
    sys.exit(1)


def extract_styles(obj):
    '''Extract styles from a colorama ansi code obj'''
    attrs = {k.lower(): v for k, v in obj.__dict__.items() if k.isupper()}
    return type(obj.__class__.__name__, (), attrs)


class style(object):
    fg = extract_styles(colorama.Fore)
    bg = extract_styles(colorama.Back)
    reset = colorama.Style.RESET_ALL
    dim = colorama.Style.DIM
    normal = colorama.Style.NORMAL
    bright = colorama.Style.BRIGHT


def styled(string, *args, **kwargs):
    '''Like string.format but includes ansi color styling keywords including
    fg, bg, and style. These are aliases to colorama.Fore, colorama.Back and
    colorama.Style. All codes should be referenced in lowercase. Finally
    colorama.Style.RESET_ALL is aliased as reset.

    Examples:
        >>> styled('{fg.red}WARNING:{reset}')  # doctest: +SKIP
        [31m[WARNING][0m
    '''

    kwargs.update(vars(style))
    return string.format(*args, **kwargs)
