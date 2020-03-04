#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Creates uis with live-linked stylesheets."""

from __future__ import absolute_import

# Standard library imports
import argparse
import inspect
import sys

# Third party imports
from invoke import Collection, Config, Program, task
from qtsass.watchers import Watcher

# Local imports
import construct


@task
def watch(ctx):
    api = construct.API()
    watcher = Watcher(
        watch_dir=str(api.ui.resources.path / 'styles'),
        compiler=api.ui.theme.refresh_stylesheet,
    )
    watcher.start()


@task(watch)
def launcher(ctx):
    '''Show the Launcher App.'''

    from construct.ui.launcher import main
    main()


@task(watch)
def bookmarks(self):
    '''Show the Bookmarks Dialog.'''

    from construct.ui.state import State
    from construct.ui.dialogs import BookmarksDialog
    from construct.ui.eventloop import get_event_loop

    loop = get_event_loop()

    api = construct.API()
    state = State(
        api=api,
        context=api.get_context(),
        bookmarks=api.user_cache.get('bookmarks', []),
        uri=api.uri_from_context(api.get_context()),
    )
    dialog = BookmarksDialog(state)
    dialog.show()

    loop.start()


@task(watch)
def dialogs(ctx):
    '''Show a series of dialogs.'''

    short_notification(ctx, 'alert')
    short_notification(ctx, 'error')
    short_notification(ctx, 'success')
    short_notification(ctx, 'info')
    notification(ctx, 'alert')
    notification(ctx, 'error')
    notification(ctx, 'success')
    notification(ctx, 'info')
    ask(ctx)


@task(watch)
def short_notification(ctx, type):
    '''Show a short notification.'''

    api = construct.API()
    method = getattr(api, type)
    method('This is a short %s message.' % type)


@task(watch)
def notification(ctx, type):
    '''Show a notification.'''

    api = construct.API()
    method = getattr(api, type)
    method(
        'This is a much longer %s message.'
        ' There is a full header with an icon, title, and close button.'
        ' This dialog can include additional widgets if necessary.' % type
    )


@task(watch)
def ask(ctx, title=None, message=None, icon=None):
    '''Show an ask dialog.'''

    api = construct.API()
    api.ask(
        title=title or 'Question',
        message=message or 'This is a question. Do you choose yes or no?',
        icon=icon,
    )


@task(watch)
def flowlayout(ctx):
    '''Show a widget that uses a FlowLayout'''

    from Qt import QtWidgets, QtCore
    from construct.ui.layouts import FlowLayout
    from construct.ui.widgets import ToolButton
    from construct.ui.eventloop import get_event_loop

    api = construct.API()

    loop = get_event_loop()

    w = QtWidgets.QWidget()
    w.setWindowFlags(w.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
    w.setObjectName('surface')
    api.ui.theme.apply(w)

    l = FlowLayout()
    for icon in api.ui.resources.font_charmaps['construct'].keys():
        b = ToolButton(icon, icon=icon, icon_size=(24, 24), parent=w)
        l.addWidget(b)
    w.setLayout(l)

    w.show()

    loop.start()


if __name__ == '__main__':
    prog = Program(
        name='ui_tasks',
        version='0.1.0',
        namespace=Collection.from_module(sys.modules[__name__]),
    ).run()
