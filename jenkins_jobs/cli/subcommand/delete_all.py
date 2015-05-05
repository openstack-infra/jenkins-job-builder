
import jenkins_jobs.cli.subcommand.base as base


class DeleteAllSubCommand(base.BaseSubCommand):

    def parse_args(self, subparser):
        delete_all = subparser.add_parser(
            'delete-all',
            help='''delete *ALL* jobs from Jenkins server, including those not
            managed by Jenkins Job Builder.''')

        self.parse_option_recursive_exclude(delete_all)

    def execute(self, config):
        raise NotImplementedError
