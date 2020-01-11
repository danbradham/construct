# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

# Standard library imports
import argparse
import logging
import os
from textwrap import dedent

# Third party imports
import fsfs
from scrim import get_scrim

# Local imports
import construct

# Local imports
from ..io.fsfs import select_by_name
from ..utils import classproperty, deprecated, get_subclasses, is_deprecated
from .constants import ARGUMENTS_TITLE, OPTIONS_TITLE
from .formatters import format_section
from .utils import error, styled


_log = logging.getLogger(__name__)
scrim = get_scrim()


class CliCommand(object):
    '''Base class for all CLI Commands. Override :meth:`setup_parser` to add
    arguments to a command. Implement :meth:`run` to customize what happens
    when the command is invoked.
    '''

    name = None

    def __init__(self, api, parent, formatter):
        self.api = api
        self.parent = parent
        self.parser = argparse.ArgumentParser(
            self.name,
            formatter_class=formatter
        )
        self.parser._optionals.title = OPTIONS_TITLE
        self.parser._positionals.title = ARGUMENTS_TITLE
        self.parser.add_argument(
            '-v',
            '--verbose',
            help='verbose output',
            action='store_true',
        )
        self._parser_setup = False

    @classmethod
    def is_available(cls, ctx=None):
        '''Implement this to set when a command is available.'''
        return True

    @property
    def arguments(self):
        return self.parser._get_positional_actions()

    @property
    def options(self):
        return self.parser._get_optional_actions()

    @property
    def usage(self):
        usage = styled('{bright}{} {}', self.parent.prog, self.name)
        for argument in self.arguments:
            usage += styled(' {fg.blue}<{}>', argument.dest)
        if self.options:
            usage += styled(' {fg.yellow}[options]')
        usage += styled('{reset}')
        return usage

    @classproperty
    def short_description(cls):
        return cls.__doc__.split('\n')[0]

    @classproperty
    def description(cls):
        parts = cls.__doc__.split('\n')
        short = parts[0]
        body = dedent('\n'.join(parts[1:]))
        text = '\n'.join([short, body])
        return text

    def _setup_parser(self, parser):
        if not self._parser_setup:
            self.setup_parser(self.parser)
        self._parser_setup = True

    def setup_parser(self, parser):
        return NotImplemented

    def parse(self, args):
        self._setup_parser(self.parser)
        args, extra_args = self.parser.parse_known_args(args)
        return args, extra_args

    def _run(self, args, *extra_args):
        if is_deprecated(self):
            print(styled(
                '{fg.red}{bright}*Deprecated* {reset}{}',
                self._deprecation_warning,
            ))
        self.run(args, *extra_args)

    def run(self, args, *extra_args):
        return NotImplemented


class Version(CliCommand):
    '''Construct Version Info'''

    name = 'version'

    def run(self, args, *extra_args):
        print()
        print(format_section(
            'Construct',
            [
                ('version', construct.__version__),
                ('url', construct.__url__),
                ('package', os.path.dirname(construct.__file__)),
                ('settings', self.api.settings.file),
            ],
            lcolor=styled('{bright}')
        ))

        import cerberus
        import entrypoints
        import fsfs
        import pymongo
        import yaml
        import qtsass
        import scrim
        deps = []
        deps.extend([
            ('cerberus', cerberus.__version__),
            ('entrypoints', entrypoints.__version__),
            ('fsfs', fsfs.__version__),
            ('pymongo', pymongo.__version__),
            ('pyyaml', yaml.__version__),
            ('qtsass', qtsass.__version__),
            ('scrim', scrim.__version__),
        ])
        try:
            import Qt
            deps.extend([
                ('Qt.py', Qt.__version__),
                ('Qt Binding', Qt.__binding__ + '-' + Qt.__binding_version__),
            ])
        except ImportError:
            pass

        print(format_section('Dependencies', deps, lcolor=styled('{bright}')))


def requires_scrim(command):
    '''Command becomes available only when cli run by scrim script...

    See also:
        https://github.com/danbradham/scrim
    '''

    command._is_available = command.is_available

    def is_available(cls, ctx=None):
        return command._is_available(ctx) and scrim.shell

    command.is_available = is_available

    return command


class Locations(CliCommand):
    '''List configured locations'''

    name = 'locations'

    def run(self, args, *extra_args):
        print()
        self.api.show(self.api.settings['locations'])


@requires_scrim
class Go(CliCommand):
    '''Navigate locations and projects

    Go to your default location and mount:
        > construct go

    Go to a specific location and mount:
        > construct go local/projects

    Once in a mount - Go to an asset in a project:
        > construct go MyProject/assets/table
    '''

    name = 'go'

    def setup_parser(self, parser):
        parser.add_argument(
            'name',
            nargs='?',
            help='Name or list of names separated by /',
        )

    def run(self, args, *extra_args):

        location = self.api.settings['my_location']
        mount = self.api.settings['my_mount']

        location_mount = self.api.get_mount_from_path(os.getcwd())
        if location_mount:
            location, mount = location_mount

        # No args - go to default location and mount
        if not args.name:
            mount = self.api.get_mount(location, mount)

            if not mount.is_dir():
                mount.mkdir(parents=True, exist_ok=True)

            scrim.pushd(mount)
            return

        selector_had_mount = False

        names = args.name.split('/')
        if names[0] in self.api.settings['locations']:
            location = names.pop(0)

        if len(names):
            if names[0] in self.api.settings['locations'][location]:
                mount = names.pop(0)
                selector_had_mount = True

        selector = '/'.join(names)

        # Name started with a mount name
        if selector_had_mount:
            mount = self.api.get_mount(location, mount)
            if not selector:

                if not mount.is_dir():
                    mount.mkdir(parents=True, exist_ok=True)

                scrim.pushd(str(mount))
                return

            root = mount
        else:
            root = os.getcwd()

        # Search by name selector from cwd
        found = select_by_name(root, selector)
        if found:
            scrim.pushd(str(found))
            return

        # Search current project or default mount
        if self.api.context.project:
            root = fsfs.search(
                root=os.getcwd(),
                direction=fsfs.UP,
            ).tags('project').one().path
        else:
            root = self.api.get_mount()

        found = select_by_name(root, selector)
        if found:
            scrim.pushd(str(found))
            return

        error('Could not find %s' % args.name)


@deprecated('Use go instead of push.', silent=True)
@requires_scrim
class Push(Go):
    '''Go to first search result - use go instead'''

    name = 'push'


@deprecated('Use go instead of home.', silent=True)
@requires_scrim
class Home(CliCommand):
    '''Go to default mount location - use go instead'''

    name = 'home'

    def run(self, args, *extra_args):

        location = self.api.settings['my_location']
        mount = self.api.settings['my_mount']

        location_mount = self.api.get_mount_from_path(os.getcwd())
        if location_mount:
            location, mount = location_mount

        mount = self.api.get_mount(location, mount)

        if not mount.is_dir():
            mount.mkdir(parents=True, exist_ok=True)

        scrim.pushd(str(mount))
        return


@requires_scrim
class Back(CliCommand):
    '''Go back to last location'''

    name = 'back'

    def run(self, args, *extra_args):
        scrim.popd()


@deprecated('Use back instead of home.', silent=True)
@requires_scrim
class Pop(Back):
    '''Go back to last location - use back instead'''

    name = 'pop'


class Search(CliCommand):
    '''Search for Entries

    Examples:
      construct search my_project
      construct search my_project/my_asset
      construct search -t asset
      construct search -t workspace maya
    '''

    name = 'search'

    def setup_parser(self, parser):
        parser.add_argument(
            'name',
            nargs='?',
            help='Name of Entry',
        )
        parser.add_argument(
            '-r', '--root',
            default=os.getcwd(),
            help='Root directory of search',
            type=str,
        )
        parser.add_argument(
            '--up',
            action='store_true',
            default=False,
            help='Search up tree instead of down',
            dest='direction',
        )
        parser.add_argument(
            '-t', '--tags',
            nargs='*',
            help='List of tags like: project',
        )
        parser.add_argument(
            '-d', '--depth',
            type=int,
            required=False,
            help='Search depth',
        )

    def run(self, args, *extra_args):
        ctx = self.api.get_context()
        query = fsfs.search(
            root=args.root,
            direction=args.direction,
            depth=args.depth or (4 if ctx.project else 2),
        )
        if args.tags:
            query = query.tags(*args.tags)
        if args.name:
            query = query.name(args.name)

        i = 0
        for i, entry in enumerate(query):
            path = entry.path
            if args.name:
                parts = args.name.split('/')
                for part in parts:
                    highlight = styled('{bright}{fg.yellow}{}{reset}', part)
                    path = path.replace(part, highlight)
            print(path)

        if i == 0:
            print(('Found 0 result.'))


class Read(CliCommand):
    '''Read metadata'''

    name = 'read'

    def setup_parser(self, parser):
        parser.add_argument(
            '--root', '-r',
            default=os.getcwd(),
            help='Directory to read from'
        )
        parser.add_argument('keys', nargs=-1, help='keys to read')

    def run(self, args, *extra_args):
        import fsfs
        data = fsfs.read(args.root, *args.keys)
        print(fsfs.encode_data(data))


class Write(CliCommand):
    '''Write metadata'''

    name = 'write'

    def setup_parser(self, parser):
        parser.add_argument(
            '--root', '-r',
            default=os.getcwd(),
            help='Directory to read from'
        )
        parser.add_argument(
            '-k', '--key',
            dest='data',
            required=True,
            action='append',
            nargs=2,
            help='key value pairs to write'
        )
        parser.add_argument(
            '-d', '--delete',
            dest='delkeys',
            action='append',
            help='Keys to delete',
            nargs=1
        )

    def run(self, args, *extra_args):

        import fsfs
        from fsfs.cli import safe_eval

        entry = fsfs.get_entry(args.root)
        if args.delkeys:
            entry.remove(*args.delkeys)

        data = {k: safe_eval(v) for k, v in args.data}

        try:
            entry.write(**data)
        except Exception as e:
            print('Failed to write data: ')
            print(dict(data))
            print(e.message)
        else:
            print('Wrote data to ' + args.root)


class Tag(CliCommand):
    '''Tag a directory

    Examples:
        construct tag project
        construct tag task model

    Unless you know what you're doing, don't add tags.
    '''

    name = 'tag'

    def setup_parser(self, parser):
        parser.add_argument(
            '--root', '-r',
            default=os.getcwd(),
            help='Directory to tag'
        )
        parser.add_argument('tags', nargs='*', help='List of tags to add')

    def run(self, args, *extra_args):
        import fsfs
        fsfs.tag(args.root, *args.tags)


class Untag(CliCommand):
    '''Untag a directory

    Examples:
        construct untag project
        construct untag task model

    Unless you know what you're doing, don't remove tags.
    '''

    name = 'untag'

    def setup_parser(self, parser):
        parser.add_argument(
            '--root', '-r',
            default=os.getcwd(),
            help='Directory to tag'
        )
        parser.add_argument('tags', nargs='*', help='List of tags to remove')

    def run(self, args, *extra_args):
        import fsfs
        fsfs.untag(args.root, *args.tags)


commands = [
    Version,
    Locations,
    Search,
    Go,
    Push,
    Home,
    Back,
    Pop,
    Read,
    Write,
    Tag,
    Untag,
]


def get_available(ctx=None):
    return [c for c in commands if c.is_available(ctx)]
