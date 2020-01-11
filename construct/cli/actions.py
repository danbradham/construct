# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

# Standard library imports
import logging
import os
import sys
import traceback

# Local imports
import construct

# Local imports
from ..compat import basestring
from .commands import CliCommand
from .formatters import format_context, format_section
from .utils import style, styled


_log = logging.getLogger(__name__)


class CliAction(CliCommand):
    '''BaseClass for all CliActions.

    Implement the setup_parser method to add your own cli arguments to the
    provided argparse.ArgumentParser.

    Implement the run method to perform some task with the cli arguments.
    Return a list of (str, str) tuples representing artifacts.
    '''

    def setup_parser(self, parser):
        '''Subclasses implement setup_parser to add arguments to the
        argparse.ArgumentParser for this CliAction.
        '''
        return NotImplemented

    def _run(self, args, *extra_args):
        api = construct.API()
        ctx = api.get_context()

        print()
        print(self.short_description + '\n')
        args_data = [(k, v) for k, v in args.__dict__.items()]
        if extra_args:
            args_data.append(('extra_args', str(extra_args)))
        args_section = format_section(
            styled('{bright}{fg.yellow}Options{reset}'),
            data=args_data,
            lcolor=style.bright,
        )
        print(args_section + '\n')
        print(format_context(ctx))

        try:
            artifacts = self.run(args, *extra_args)
        except Exception as e:
            print()
            msg = styled(
                '{bright}{fg.red}{}: {fg.reset}{}{reset}',
                e.__class__.__name__,
                e,
            )
            tb = traceback.format_exc()
            tb_lines = tb.split('\n')
            tb_lines[-2] = msg
            print('\n'.join(tb_lines[:-1]))
            sys.exit(1)

        if not artifacts:
            sys.exit(0)

        if isinstance(artifacts, tuple):
            artifacts = [artifacts]
        if isinstance(artifacts, basestring):
            artifacts = [(artifacts,)]
        print()
        msg = format_section(
            styled('{bright}{fg.green}Artifacts{reset}'),
            artifacts,
            lcolor=styled('{bright}'),
        )
        print(msg)

    def run(self, args, *extra_args):
        '''Subclasses implement run to perform some task with the parsed
        cli arguments. The return value should be a list of (str, str) tuples.
        These will be printed under an Artifacts section after the command
        runs successfully.

        Arguments:
            args (argparse.Namespace) - Parsed arguments
            extra_args - Unparsed extra arguments
        Returns:
            List[(str, str)] - List of tuples representing side effects
        '''
        return NotImplemented


class NewProject(CliAction):
    '''Create a new project

    Use default location and mount
        > cons new.project --name=My_Project

    Specify a location and mount
        > cons new.project --location=local --mount=lib --name=My_Library

    List your configured locations and mounts
        > cons locations
    '''

    name = 'new.project'

    @classmethod
    def is_available(cls, ctx=None):
        return ctx and not ctx.project

    def setup_parser(self, parser):

        location = self.api.settings['my_location']
        mount = self.api.settings['my_mount']
        location_mount = self.api.get_mount_from_path(os.getcwd())
        if location_mount:
            location, mount = location_mount

        parser.add_argument(
            '-n', '--name',
            help='Project name',
            type=str,
            required=True,
        )
        parser.add_argument(
            '-l', '--location',
            default=location,
            help='Location name',
            type=str,
        )
        parser.add_argument(
            '-m', '--mount',
            default=mount,
            help='Mount name',
            type=str,
        )

    def run(self, args, *extra_args):

        project = self.api.io.new_project(args.name, args.location, args.mount)
        project_path = self.api.io.get_path_to(project)

        return 'project', project_path


class NewFolder(CliAction):
    '''Create a new folder

    Create a new folder
        > cons new.folder --name=My_Folder
    '''

    name = 'new.folder'

    @classmethod
    def is_available(cls, ctx=None):
        return ctx and (
            ctx.project and
            not ctx.asset
        )

    def setup_parser(self, parser):
        parser.add_argument(
            '-n', '--name',
            help='Folder name',
            type=str,
            required=True,
        )

    def run(self, args, *extra_args):

        parent = self.api.context.folder or self.api.context.project
        folder = self.api.io.new_folder(args.name, parent)
        folder_path = self.api.io.get_path_to(folder)

        return 'folder', folder_path


class NewAsset(CliAction):
    '''Create a new asset

    Create a new asset
        > cons new.asset --name=My_Asset --asset_type=asset

    Create a new shot
        > cons new.asset --name=My_Shot --asset_type=shot
    '''

    name = 'new.asset'

    @classmethod
    def is_available(cls, ctx=None):
        return ctx and (
            ctx.project and
            not ctx.asset
        )

    def setup_parser(self, parser):
        parser.add_argument(
            '-n', '--name',
            help='Asset name',
            type=str,
            required=True,
        )
        parser.add_argument(
            '-t', '--asset_type',
            help='Asset Type',
            type=str,
            default='asset',
        )

    def run(self, args, *extra_args):

        parent = self.api.context.folder or self.api.context.project
        asset = self.api.io.new_asset(args.name, args.asset_type, parent)
        asset_path = self.api.io.get_path_to(asset)

        return 'asset', asset_path


class NewShot(CliAction):
    '''Create a new shot

    Alias for new.asset --asset_type=shot

    Create a new shot
        > cons new.shot --name=My_Shot
    '''

    name = 'new.shot'

    @classmethod
    def is_available(cls, ctx=None):
        return ctx and (
            ctx.project and
            not ctx.asset
        )

    def setup_parser(self, parser):
        parser.add_argument(
            '-n', '--name',
            help='Asset name',
            type=str,
            required=True,
        )
        parser.add_argument(
            '-t', '--asset_type',
            help='Asset Type',
            type=str,
            default='shot',
        )


class NewTask(CliAction):
    '''Create a new task

    Create a new model task
        > cons new.task --name=model

    Create a new anim task
        > cons new.task --name=anim
    '''

    name = 'new.task'

    @classmethod
    def is_available(cls, ctx=None):
        return ctx and (
            ctx.project and
            ctx.asset
        )

    def setup_parser(self, parser):
        parser.add_argument(
            '-n', '--name',
            help='Asset name',
            type=str,
            required=True,
        )

    def run(self, args, *extra_args):

        parent = self.api.context.asset
        task = self.api.io.new_task(args.name, parent)
        task_path = self.api.io.get_path_to(task)

        return 'task', task_path


actions = [
    NewProject,
    NewFolder,
    NewAsset,
    NewShot,
    NewTask,
]


def get_available(ctx=None):
    return [a for a in actions if a.is_available(ctx)]
