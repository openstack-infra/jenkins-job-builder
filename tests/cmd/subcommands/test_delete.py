import os
from jenkins_jobs import cmd
from tests.base import mock
from tests.cmd.test_cmd import CmdTestsBase


@mock.patch('jenkins_jobs.builder.Jenkins.get_plugins_info', mock.MagicMock)
class DeleteTests(CmdTestsBase):

    @mock.patch('jenkins_jobs.cmd.Builder.delete_job')
    def test_delete_single_job(self, delete_job_mock):
        """
        Test handling the deletion of a single Jenkins job.
        """

        args = self.parser.parse_args(['delete', 'test_job'])
        cmd.execute(args, self.config)  # passes if executed without error

    @mock.patch('jenkins_jobs.cmd.Builder.delete_job')
    def test_delete_multiple_jobs(self, delete_job_mock):
        """
        Test handling the deletion of multiple Jenkins jobs.
        """

        args = self.parser.parse_args(['delete', 'test_job1', 'test_job2'])
        cmd.execute(args, self.config)  # passes if executed without error

    @mock.patch('jenkins_jobs.builder.Jenkins.delete_job')
    def test_delete_using_glob_params(self, delete_job_mock):
        """
        Test handling the deletion of multiple Jenkins jobs using the glob
        parameters feature.
        """

        args = self.parser.parse_args(['delete',
                                       '--path',
                                       os.path.join(self.fixtures_path,
                                                    'cmd-002.yaml'),
                                       '*bar*'])
        cmd.execute(args, self.config)
        calls = [mock.call('bar001'), mock.call('bar002')]
        delete_job_mock.assert_has_calls(calls, any_order=True)
        self.assertEquals(delete_job_mock.call_count, len(calls),
                          "Jenkins.delete_job() was called '%s' times when "
                          "expected '%s'" % (delete_job_mock.call_count,
                                             len(calls)))
