
import jenkins_jobs.cli.subcommand.base as base


class DeleteSubCommand(base.BaseSubCommand):

    def parse_args(self, subparser):
        delete = subparser.add_parser('delete')

        self.parse_option_recursive_exclude(delete)

        delete.add_argument(
            'name',
            help='name of job',
            nargs='+')
        delete.add_argument(
            '-p', '--path',
            default=None,
            help='''colon-separated list of paths to YAML files or
            directories''')

    def execute(self, config):
        raise NotImplementedError
