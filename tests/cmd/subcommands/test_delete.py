import os

from tests.base import mock
from tests.cmd.test_cmd import CmdTestsBase


@mock.patch('jenkins_jobs.builder.Jenkins.get_plugins_info', mock.MagicMock)
class DeleteTests(CmdTestsBase):

    @mock.patch('jenkins_jobs.cmd.Builder.delete_job')
    def test_delete_single_job(self, delete_job_mock):
        """
        Test handling the deletion of a single Jenkins job.
        """

        args = ['--conf', self.default_config_file, 'delete', 'test_job']
        self.execute_jenkins_jobs_with_args(args)

    @mock.patch('jenkins_jobs.cmd.Builder.delete_job')
    def test_delete_multiple_jobs(self, delete_job_mock):
        """
        Test handling the deletion of multiple Jenkins jobs.
        """

        args = ['--conf', self.default_config_file,
                'delete', 'test_job1', 'test_job2']
        self.execute_jenkins_jobs_with_args(args)

    @mock.patch('jenkins_jobs.builder.Jenkins.delete_job')
    def test_delete_using_glob_params(self, delete_job_mock):
        """
        Test handling the deletion of multiple Jenkins jobs using the glob
        parameters feature.
        """

        args = ['--conf', self.default_config_file,
                'delete', '--path',
                os.path.join(self.fixtures_path,
                             'cmd-002.yaml'),
                '*bar*']
        self.execute_jenkins_jobs_with_args(args)
        calls = [mock.call('bar001'), mock.call('bar002')]
        delete_job_mock.assert_has_calls(calls, any_order=True)
        self.assertEqual(delete_job_mock.call_count, len(calls),
                         "Jenkins.delete_job() was called '%s' times when "
                         "expected '%s'" % (delete_job_mock.call_count,
                                            len(calls)))
