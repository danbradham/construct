# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Local imports
from ..compat import wraps


class EventLoop(object):

    _instance = None

    def __init__(self, event_loop, standalone):
        self.event_loop = event_loop
        self.standalone = standalone
        self.running = not self.standalone

    def quit(self):
        self.event_loop.quit()

    def start(self):
        if self.running:
            return

        self.running = True
        self.event_loop.setQuitOnLastWindowClosed(True)
        return self.event_loop.exec_()

    def stop(self):
        if not self.running:
            return

        self.event_loop.exit()
        self.running = False


def get_event_loop():
    '''Get the EventLoop instance.'''

    from Qt.QtWidgets import QApplication

    if not EventLoop._instance:

        standalone = False
        event_loop = QApplication.instance()

        if not event_loop:
            event_loop = QApplication([])
            standalone = True

        EventLoop._instance = EventLoop(event_loop, standalone)

    return EventLoop._instance


def requires_event_loop(fn):
    '''Make sure the event loop is started before executing the function.'''


    @wraps(fn)
    def start_then_call(*args, **kwargs):
        event_loop = get_event_loop()
        result = fn(*args, **kwargs)
        return result

    return start_then_call
