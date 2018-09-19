import io
import os

from mock import patch
from tests.base import mock
from tests.cmd.test_cmd import CmdTestsBase

from jenkins_jobs.cli import entry
from jenkins_jobs import builder


@mock.patch('jenkins_jobs.builder.JenkinsManager.get_plugins_info',
            mock.MagicMock)
class TestConfigs(CmdTestsBase):

    global_conf = '/etc/jenkins_jobs/jenkins_jobs.ini'
    user_conf = os.path.join(os.path.expanduser('~'), '.config',
                             'jenkins_jobs', 'jenkins_jobs.ini')
    local_conf = os.path.join(os.path.dirname(__file__),
                              'jenkins_jobs.ini')

    def test_use_global_config(self):
        """
        Verify that JJB uses the global config file by default
        """

        args = ['test', 'foo']
        conffp = io.open(self.default_config_file, 'r', encoding='utf-8')

        with patch('os.path.isfile', return_value=True) as m_isfile:
            def side_effect(path):
                if path == self.global_conf:
                    return True
                return False

            m_isfile.side_effect = side_effect

            with patch('io.open', return_value=conffp) as m_open:
                entry.JenkinsJobs(args, config_file_required=True)
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
                return False

            m_isfile.side_effect = side_effect
            with patch('io.open', return_value=conffp) as m_open:
                entry.JenkinsJobs(args, config_file_required=True)
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

    def test_config_old_plugin_format_warning(self):
        """
        Run test mode and check that old plugin settings result
        in a warning, while ensuring that missing sections do not
        trigger the same warning if a default value is provided.
        """
        args = ['--conf',
                os.path.join(self.fixtures_path, 'plugin_warning.ini'),
                'test', 'foo']
        jenkins_jobs = entry.JenkinsJobs(args)
        jenkins_jobs.jjb_config.get_plugin_config(
            'old_plugin', 'setting', True)
        jenkins_jobs.jjb_config.get_plugin_config(
            'old_plugin_no_conf', 'setting', True)
        jenkins_jobs.jjb_config.get_plugin_config(
            'new_plugin', 'setting')
        self.assertIn(
            'using a [old_plugin] section in your config file is deprecated',
            self.logger.output)
        self.assertNotIn(
            'using a [old_plugin_no_conf] secton in your config file is '
            'deprecated',
            self.logger.output)
        self.assertNotIn(
            'using a [new_plugin] section in your config file is deprecated',
            self.logger.output)

    def test_config_options_not_replaced_by_cli_defaults(self):
        """
        Run test mode and check config settings from conf file retained
        when none of the global CLI options are set.
        """
        config_file = os.path.join(self.fixtures_path,
                                   'settings_from_config.ini')
        args = ['--conf', config_file, 'test', 'dummy.yaml']
        jenkins_jobs = entry.JenkinsJobs(args)
        jjb_config = jenkins_jobs.jjb_config
        self.assertEqual(jjb_config.jenkins['user'], "jenkins_user")
        self.assertEqual(jjb_config.jenkins['password'], "jenkins_password")
        self.assertEqual(jjb_config.builder['ignore_cache'], True)
        self.assertEqual(jjb_config.builder['flush_cache'], True)
        self.assertEqual(jjb_config.builder['update'], "all")
        self.assertEqual(
            jjb_config.yamlparser['allow_empty_variables'], True)

    def test_config_options_overriden_by_cli(self):
        """
        Run test mode and check config settings from conf file retained
        when none of the global CLI options are set.
        """
        args = ['--user', 'myuser', '--password', 'mypassword',
                '--ignore-cache', '--flush-cache', '--allow-empty-variables',
                'test', 'dummy.yaml']
        jenkins_jobs = entry.JenkinsJobs(args)
        jjb_config = jenkins_jobs.jjb_config
        self.assertEqual(jjb_config.jenkins['user'], "myuser")
        self.assertEqual(jjb_config.jenkins['password'], "mypassword")
        self.assertEqual(jjb_config.builder['ignore_cache'], True)
        self.assertEqual(jjb_config.builder['flush_cache'], True)
        self.assertEqual(
            jjb_config.yamlparser['allow_empty_variables'], True)

    @mock.patch('jenkins_jobs.cli.subcommand.update.JenkinsManager')
    def test_update_timeout_not_set(self, jenkins_mock):
        """Check that timeout is left unset

        Test that the Jenkins object has the timeout set on it only when
        provided via the config option.
        """

        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')
        args = ['--conf', self.default_config_file, 'update', path]

        jenkins_mock.return_value.update_jobs.return_value = ([], 0)
        jenkins_mock.return_value.update_views.return_value = ([], 0)
        self.execute_jenkins_jobs_with_args(args)

        # validate that the JJBConfig used to initialize builder.Jenkins
        # contains the expected timeout value.

        jjb_config = jenkins_mock.call_args[0][0]
        self.assertEqual(jjb_config.jenkins['timeout'],
                         builder._DEFAULT_TIMEOUT)

    @mock.patch('jenkins_jobs.cli.subcommand.update.JenkinsManager')
    def test_update_timeout_set(self, jenkins_mock):
        """Check that timeout is set correctly

        Test that the Jenkins object has the timeout set on it only when
        provided via the config option.
        """

        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')
        config_file = os.path.join(self.fixtures_path,
                                   'non-default-timeout.ini')
        args = ['--conf', config_file, 'update', path]

        jenkins_mock.return_value.update_jobs.return_value = ([], 0)
        jenkins_mock.return_value.update_views.return_value = ([], 0)
        self.execute_jenkins_jobs_with_args(args)

        # validate that the JJBConfig used to initialize builder.Jenkins
        # contains the expected timeout value.

        jjb_config = jenkins_mock.call_args[0][0]
        self.assertEqual(jjb_config.jenkins['timeout'], 0.2)
