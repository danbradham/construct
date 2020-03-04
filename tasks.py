#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Standard library imports
import os
import sys

# Third party imports
from invoke import Collection, Program, task


PY2 = sys.version_info.major < 3


def joinpath(*parts):
    return os.path.join(*parts).replace('\\', '/')


@task
def tests(ctx, level='WARNING', module=None):
    '''Run tests using nose'''

    nose_cmd = (
        'nosetests '
        '--verbosity=2 '
        '--nocapture '
        '--logging-level=%s ' % level
    )

    if PY2:
        # Prevent nose from importing UI modules
        nose_cmd += '--exclude-dir="construct/ui"'

    if module:
        nose_cmd += module

    ctx.run(nose_cmd)


@task
def build_docs(ctx):
    '''Build documentation using Sphinx.'''

    ctx.run('docs\\make html')


if __name__ == '__main__':
    Program(
        namespace=Collection.from_module(sys.modules[__name__])
    ).run()
