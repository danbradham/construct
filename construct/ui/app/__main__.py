# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Third party imports
from Qt import QtWidgets

# Local imports
import construct
from construct.ui.eventloop import get_event_loop
from construct.ui.theme import theme


def main():

    api = construct.API()

    event_loop = get_event_loop()

    app = api.ui.launcher()
    app.show()

    if QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():

        def on_tray_activated(reason):
            if reason == QtWidgets.QSystemTrayIcon.Context:
                return
            app.setVisible(not app.isVisible())

        tray = QtWidgets.QSystemTrayIcon(parent=app)
        tray.setIcon(theme.icon('icons/construct.svg'))
        tray.activated.connect(on_tray_activated)
        tray_menu = QtWidgets.QMenu(parent=app)
        tray_menu.addAction(
            theme.icon('close', parent=app),
            'Close',
            event_loop.quit
        )
        tray.setContextMenu(tray_menu)
        tray.show()

    event_loop.start()


if __name__ == '__main__':
    main()
