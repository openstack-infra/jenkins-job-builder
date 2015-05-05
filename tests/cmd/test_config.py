import io
import os

from jenkins_jobs.cli import entry
from mock import patch
from tests.base import mock
from tests.cmd.test_cmd import CmdTestsBase


@mock.patch('jenkins_jobs.builder.Jenkins.get_plugins_info', mock.MagicMock)
class TestConfigs(CmdTestsBase):

    global_conf = '/etc/jenkins_jobs/jenkins_jobs.ini'
    user_conf = os.path.join(os.path.expanduser('~'), '.config',
                             'jenkins_jobs', 'jenkins_jobs.ini')

    def test_use_global_config(self):
        """
        Verify that JJB uses the global config file by default
        """

        args = ['test', 'foo']
        conffp = io.open(self.default_config_file, 'r', encoding='utf-8')

        with patch('os.path.isfile', return_value=True) as m_isfile:
            def side_effect(path):
                if path == self.user_conf:
                    return False
                if path == self.global_conf:
                    return True

            m_isfile.side_effect = side_effect

            with patch('io.open', return_value=conffp) as m_open:
                entry.JenkinsJobs(args)
                m_open.assert_called_with(self.global_conf, 'r',
                                          encoding='utf-8')

    def test_use_config_in_user_home(self):
        """
        Verify that JJB uses config file in user home folder
        """

        args = ['test', 'foo']

        conffp = io.open(self.default_config_file, 'r', encoding='utf-8')
        with patch('os.path.isfile', return_value=True) as m_isfile:
            def side_effect(path):
                if path == self.user_conf:
                    return True

            m_isfile.side_effect = side_effect
            with patch('io.open', return_value=conffp) as m_open:
                entry.JenkinsJobs(args)
                m_open.assert_called_with(self.user_conf, 'r',
                                          encoding='utf-8')

    def test_non_existing_config_dir(self):
        """
        Run test mode and pass a non-existing configuration directory
        """
        args = ['--conf', self.default_config_file, 'test', 'foo']
        jenkins_jobs = entry.JenkinsJobs(args)
        self.assertRaises(IOError, jenkins_jobs.execute)

    def test_non_existing_config_file(self):
        """
        Run test mode and pass a non-existing configuration file
        """
        args = ['--conf', self.default_config_file, 'test',
                'non-existing.yaml']
        jenkins_jobs = entry.JenkinsJobs(args)
        self.assertRaises(IOError, jenkins_jobs.execute)
