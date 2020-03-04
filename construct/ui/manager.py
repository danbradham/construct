# -*- coding: utf-8 -*-

# Standard library imports
from collections import defaultdict

# Local imports
from .eventloop import requires_event_loop
from .resources import Resources
from .theme import theme


class UIManager(object):
    '''Manages UI resources, themes, and dialogs.'''

    def __init__(self, api):
        self.api = api
        self.resources = Resources([])
        self.theme = theme
        self.menu_registry = defaultdict(list)

    def load(self):
        self.resources = Resources(self.api.path)
        self.theme.set_resources(self.resources)
        self.api.extend('alert', self.alert)
        self.api.extend('error', self.error)
        self.api.extend('success', self.success)
        self.api.extend('info', self.info)
        self.api.extend('ask', self.ask)
        self.api.extend('launcher', self.launcher)
        self.api.extend('register_menu', self.register_menu)
        self.api.extend('unregister_menu', self.unregister_menu)

    def unload(self):
        self.resources = Resources([])
        self.theme.set_resources(self.resources)
        self.api.unextend('alert')
        self.api.unextend('error')
        self.api.unextend('success')
        self.api.unextend('info')
        self.api.unextend('ask')
        self.api.unextend('launcher')
        self.api.unextend('register_menu')
        self.api.unextend('unregister_menu')

    def request_menu(self, identifier, context, menu=None):
        from Qt import QtCore, QtWidgets

        menu = menu or QtWidgets.QMenu()
        menu.setWindowFlags(
            menu.windowFlags() | QtCore.Qt.NoDropShadowWindowHint
        )

        for item in self.menu_registry[identifier]:
            item(menu, context)

        for child in menu.children():
            if isinstance(child, QtWidgets.QMenu):
                child.setWindowFlags(
                    child.windowFlags() | QtCore.Qt.NoDropShadowWindowHint
                )

        return menu

    def register_menu(self, identifier, handler):
        if handler not in self.menu_registry[identifier]:
            self.menu_registry[identifier].append(handler)

    def unregister_menu(self, identifer, handler):
        if handler in self.menu_registry[identifer]:
            self.menu_registry[identifer].remove(handler)

    @requires_event_loop
    def launcher(self, uri=None):
        '''Shows the Launcher application.

        Arguments:
            uri (str): Location where Launcher should start
        '''

        from .launcher import Launcher
        return Launcher(self.api, uri)

    @requires_event_loop
    def alert(self, message, title=None, short=None):
        '''Create an alert dialog.

        Arguments:
            message (str): Message to display
            title (str): Optional title
        '''
        from .dialogs import Notification
        return Notification(
            type='alert',
            message=message,
            title=title,
            icon='alert',
            close_icon='close',
            short=short,
        ).exec_()

    @requires_event_loop
    def error(self, message, title=None, short=None):
        '''Create an error dialog.

        Arguments:
            message (str): Message to display
            title (str): Optional title
        '''
        from .dialogs import Notification
        return Notification(
            type='error',
            message=message,
            title=title,
            icon='error',
            close_icon='close',
            short=short,
        ).exec_()

    @requires_event_loop
    def success(self, message, title=None, short=None):
        '''Create a success dialog.

        Arguments:
            message (str): Message to display
            title (str): Optional title
        '''
        from .dialogs import Notification
        return Notification(
            type='success',
            message=message,
            title=title,
            close_icon='check',
            short=short,
        ).exec_()

    @requires_event_loop
    def info(self, message, title=None, short=None):
        '''Create an info dialog.

        Arguments:
            message (str): Message to display
            title (str): Optional title
        '''
        from .dialogs import Notification
        return Notification(
            type='info',
            message=message,
            title=title,
            close_icon='check',
            short=short,
        ).exec_()

    @requires_event_loop
    def ask(self, title, message, yes_label='Yes', no_label='No', icon=None):
        '''Ask a question.

        Arguments:
            title (str): Title
            message (str): Message to display
            yes_label (str): Yes button text
            no_label (str): No button text
            icon (str): Icon to appear in header.
        '''
        from .dialogs import Ask
        return Ask(
            title=title,
            message=message,
            yes_label=yes_label,
            no_label=no_label,
            icon=icon,
        ).exec_()
