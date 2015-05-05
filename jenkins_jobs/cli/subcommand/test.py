import sys

import jenkins_jobs.cli.subcommand.base as base


class TestSubCommand(base.BaseSubCommand):
    def parse_args(self, subparser):
        test = subparser.add_parser('test')

        self.parse_option_recursive_exclude(test)

        test.add_argument(
            'path',
            help='''colon-separated list of paths to YAML files or
            directories''',
            nargs='?',
            default=sys.stdin)
        test.add_argument(
            '-p',
            dest='plugins_info_path',
            default=None,
            help='path to plugin info YAML file')
        test.add_argument(
            '-o',
            dest='output_dir',
            default=sys.stdout,
            help='path to output XML')
        test.add_argument(
            'name',
            help='name(s) of job(s)', nargs='*')

    def execute(self, config):
        raise NotImplementedError
