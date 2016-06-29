import os

from jenkins_jobs.cli import entry
from tests import base
from tests.base import mock


class CmdTestsBase(base.BaseTestCase):

    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')

    def setUp(self):
        super(CmdTestsBase, self).setUp()

        # Testing the cmd module can sometimes result in the JobCache class
        # attempting to create the cache directory multiple times as the tests
        # are run in parallel.  Stub out the JobCache to ensure that each
        # test can safely create the cache directory without risk of
        # interference.
        cache_patch = mock.patch('jenkins_jobs.builder.JobCache',
                                 autospec=True)
        self.cache_mock = cache_patch.start()
        self.addCleanup(cache_patch.stop)

        self.default_config_file = os.path.join(self.fixtures_path,
                                                'empty_builder.ini')

    def execute_jenkins_jobs_with_args(self, args):
        jenkins_jobs = entry.JenkinsJobs(args)
        jenkins_jobs.execute()


class TestCmd(CmdTestsBase):

    def test_with_empty_args(self):
        """
        User passes no args, should fail with SystemExit
        """
        with mock.patch('sys.stderr'):
            self.assertRaises(SystemExit, entry.JenkinsJobs, [])
