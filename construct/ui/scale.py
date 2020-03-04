# -*- coding: utf-8 -*-

from __future__ import absolute_import


def dpi():
    '''Get screen DPI to scale UI independent of monitor size.'''

    from Qt import QtWidgets

    app = QtWidgets.QApplication.instance()
    if app:
        return float(app.desktop().logicalDpiX())
    return 96.0


def factor():
    '''Get UI scale factor'''

    return dpi() / 96.0


def px(*values):
    '''Scale a pixel value based on screen dpi.'''

    if len(values) == 1:
        return int(factor() * values[0])

    return [int(factor() * value) for value in values]


def pt(*values):
    '''Scale a point value based on screen dpi.'''

    if len(values) == 1:
        return int(factor() * values[0] * 1.33)

    return [int(factor() * value * 1.33) for value in values]
