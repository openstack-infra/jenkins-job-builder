# Joint copyright:
#  - Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# The goal of these tests is to check that given a particular set of flags to
# Jenkins Job Builder's command line tools it will result in a particular set
# of actions by the JJB library, usually through interaction with the
# python-jenkins library.

import difflib
import filecmp
import io
import os
import shutil
import tempfile
import yaml

import jenkins
from six.moves import StringIO
import testtools

from jenkins_jobs.cli import entry
from tests.base import mock
from tests.cmd.test_cmd import CmdTestsBase


@mock.patch('jenkins_jobs.builder.JenkinsManager.get_plugins_info',
            mock.MagicMock)
class TestTests(CmdTestsBase):

    def test_non_existing_job(self):
        """
        Run test mode and pass a non-existing job name
        (probably better to fail here)
        """
        args = ['--conf', self.default_config_file, 'test',
                os.path.join(self.fixtures_path,
                             'cmd-001.yaml'),
                'invalid']
        self.execute_jenkins_jobs_with_args(args)

    def test_valid_job(self):
        """
        Run test mode and pass a valid job name
        """
        args = ['--conf', self.default_config_file, 'test',
                os.path.join(self.fixtures_path,
                             'cmd-001.yaml'),
                'foo-job']
        console_out = io.BytesIO()
        with mock.patch('sys.stdout', console_out):
            self.execute_jenkins_jobs_with_args(args)

    def test_console_output(self):
        """
        Run test mode and verify that resulting XML gets sent to the console.
        """

        console_out = io.BytesIO()
        with mock.patch('sys.stdout', console_out):
            args = ['--conf', self.default_config_file, 'test',
                    os.path.join(self.fixtures_path, 'cmd-001.yaml')]
            self.execute_jenkins_jobs_with_args(args)
        xml_content = io.open(os.path.join(self.fixtures_path, 'cmd-001.xml'),
                              'r', encoding='utf-8').read()
        self.assertEqual(console_out.getvalue().decode('utf-8'), xml_content)

    def test_output_dir(self):
        """
        Run test mode with output to directory and verify that output files are
        generated.
        """
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        args = ['test', os.path.join(self.fixtures_path, 'cmd-001.yaml'),
                '-o', tmpdir]
        self.execute_jenkins_jobs_with_args(args)
        self.expectThat(os.path.join(tmpdir, 'foo-job'),
                        testtools.matchers.FileExists())

    def test_output_dir_config_xml(self):
        """
        Run test mode with output to directory in "config.xml" mode and verify
        that output files are generated.
        """
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        args = ['test', os.path.join(self.fixtures_path, 'cmd-001.yaml'),
                '-o', tmpdir, '--config-xml']
        self.execute_jenkins_jobs_with_args(args)
        self.expectThat(os.path.join(tmpdir, 'foo-job', 'config.xml'),
                        testtools.matchers.FileExists())

    def test_stream_input_output_no_encoding_exceed_recursion(self):
        """
        Test that we don't have issues processing large number of jobs and
        outputting the result if the encoding is not set.
        """
        console_out = io.BytesIO()

        input_file = os.path.join(self.fixtures_path,
                                  'large-number-of-jobs-001.yaml')
        with io.open(input_file, 'r') as f:
            with mock.patch('sys.stdout', console_out):
                console_out.encoding = None
                with mock.patch('sys.stdin', f):
                    args = ['test']
                    self.execute_jenkins_jobs_with_args(args)

    def test_stream_input_output_utf8_encoding(self):
        """
        Run test mode simulating using pipes for input and output using
        utf-8 encoding
        """
        console_out = io.BytesIO()

        input_file = os.path.join(self.fixtures_path, 'cmd-001.yaml')
        with io.open(input_file, 'r') as f:
            with mock.patch('sys.stdout', console_out):
                with mock.patch('sys.stdin', f):
                    args = ['--conf', self.default_config_file, 'test']
                    self.execute_jenkins_jobs_with_args(args)

        xml_content = io.open(os.path.join(self.fixtures_path, 'cmd-001.xml'),
                              'r', encoding='utf-8').read()
        value = console_out.getvalue().decode('utf-8')
        self.assertEqual(value, xml_content)

    def test_stream_input_output_ascii_encoding(self):
        """
        Run test mode simulating using pipes for input and output using
        ascii encoding with unicode input
        """
        console_out = io.BytesIO()
        console_out.encoding = 'ascii'

        input_file = os.path.join(self.fixtures_path, 'cmd-001.yaml')
        with io.open(input_file, 'r') as f:
            with mock.patch('sys.stdout', console_out):
                with mock.patch('sys.stdin', f):
                    args = ['--conf', self.default_config_file, 'test']
                    self.execute_jenkins_jobs_with_args(args)

        xml_content = io.open(os.path.join(self.fixtures_path, 'cmd-001.xml'),
                              'r', encoding='utf-8').read()
        value = console_out.getvalue().decode('ascii')
        self.assertEqual(value, xml_content)

    def test_stream_output_ascii_encoding_invalid_char(self):
        """
        Run test mode simulating using pipes for input and output using
        ascii encoding for output with include containing a character
        that cannot be converted.
        """
        console_out = io.BytesIO()
        console_out.encoding = 'ascii'

        input_file = os.path.join(self.fixtures_path, 'unicode001.yaml')
        with io.open(input_file, 'r', encoding='utf-8') as f:
            with mock.patch('sys.stdout', console_out):
                with mock.patch('sys.stdin', f):
                    args = ['--conf', self.default_config_file, 'test']
                    jenkins_jobs = entry.JenkinsJobs(args)
                    e = self.assertRaises(UnicodeError, jenkins_jobs.execute)
        self.assertIn("'ascii' codec can't encode character", str(e))

    @mock.patch(
        'jenkins_jobs.cli.subcommand.update.XmlJobGenerator.generateXML')
    @mock.patch('jenkins_jobs.cli.subcommand.update.ModuleRegistry')
    def test_plugins_info_stub_option(self, registry_mock, generateXML_mock):
        """
        Test handling of plugins_info stub option.
        """
        plugins_info_stub_yaml_file = os.path.join(self.fixtures_path,
                                                   'plugins-info.yaml')
        args = ['--conf',
                os.path.join(self.fixtures_path, 'cmd-001.conf'),
                'test',
                '-p',
                plugins_info_stub_yaml_file,
                os.path.join(self.fixtures_path, 'cmd-001.yaml')]

        self.execute_jenkins_jobs_with_args(args)

        with io.open(plugins_info_stub_yaml_file,
                     'r', encoding='utf-8') as yaml_file:
            plugins_info_list = yaml.load(yaml_file)

        registry_mock.assert_called_with(mock.ANY,
                                         plugins_info_list)

    @mock.patch(
        'jenkins_jobs.cli.subcommand.update.XmlJobGenerator.generateXML')
    @mock.patch('jenkins_jobs.cli.subcommand.update.ModuleRegistry')
    def test_bogus_plugins_info_stub_option(self, registry_mock,
                                            generateXML_mock):
        """
        Verify that a JenkinsJobException is raised if the plugins_info stub
        file does not yield a list as its top-level object.
        """
        plugins_info_stub_yaml_file = os.path.join(self.fixtures_path,
                                                   'bogus-plugins-info.yaml')
        args = ['--conf',
                os.path.join(self.fixtures_path, 'cmd-001.conf'),
                'test',
                '-p',
                plugins_info_stub_yaml_file,
                os.path.join(self.fixtures_path, 'cmd-001.yaml')]

        stderr = StringIO()
        with mock.patch('sys.stderr', stderr):
            self.assertRaises(SystemExit, entry.JenkinsJobs, args)
        self.assertIn("must contain a Yaml list",
                      stderr.getvalue())


class TestJenkinsGetPluginInfoError(CmdTestsBase):
    """ This test class is used for testing the 'test' subcommand when we want
    to validate its behavior without mocking
    jenkins_jobs.builder.JenkinsManager.get_plugins_info
    """

    @mock.patch('jenkins.Jenkins.get_plugins')
    def test_console_output_jenkins_connection_failure_warning(
            self, get_plugins_mock):
        """
        Run test mode and verify that failed Jenkins connection attempt
        exception does not bubble out of cmd.main. Ideally, we would also test
        that an appropriate message is logged to stderr but it's somewhat
        difficult to figure out how to actually enable stderr in this test
        suite.
        """

        get_plugins_mock.side_effect = \
            jenkins.JenkinsException("Connection refused")
        with mock.patch('sys.stdout'):
            try:
                args = ['--conf', self.default_config_file, 'test',
                        os.path.join(self.fixtures_path, 'cmd-001.yaml')]
                self.execute_jenkins_jobs_with_args(args)
            except jenkins.JenkinsException:
                self.fail("jenkins.JenkinsException propagated to main")
            except Exception:
                pass  # only care about jenkins.JenkinsException for now

    @mock.patch('jenkins.Jenkins.get_plugins')
    def test_skip_plugin_retrieval_if_no_config_provided(
            self, get_plugins_mock):
        """
        Verify that retrieval of information from Jenkins instance about its
        plugins will be skipped when run if no config file provided.
        """
        with mock.patch('sys.stdout', new_callable=io.BytesIO):
            args = ['--conf', self.default_config_file, 'test',
                    os.path.join(self.fixtures_path, 'cmd-001.yaml')]
            entry.JenkinsJobs(args)
        self.assertFalse(get_plugins_mock.called)

    @mock.patch('jenkins.Jenkins.get_plugins_info')
    def test_skip_plugin_retrieval_if_disabled(self, get_plugins_mock):
        """
        Verify that retrieval of information from Jenkins instance about its
        plugins will be skipped when run if a config file provided and disables
        querying through a config option.
        """
        with mock.patch('sys.stdout', new_callable=io.BytesIO):
            args = ['--conf',
                    os.path.join(self.fixtures_path,
                                 'disable-query-plugins.conf'),
                    'test',
                    os.path.join(self.fixtures_path, 'cmd-001.yaml')]
            entry.JenkinsJobs(args)
        self.assertFalse(get_plugins_mock.called)


class MatchesDirMissingFilesMismatch(object):
    def __init__(self, left_directory, right_directory):
        self.left_directory = left_directory
        self.right_directory = right_directory

    def describe(self):
        return "{0} and {1} contain different files".format(
            self.left_directory,
            self.right_directory)

    def get_details(self):
        return {}


class MatchesDirFileContentsMismatch(object):
    def __init__(self, left_file, right_file):
        self.left_file = left_file
        self.right_file = right_file

    def describe(self):
        left_contents = open(self.left_file).readlines()
        right_contents = open(self.right_file).readlines()

        return "{0} is not equal to {1}:\n{2}".format(
            difflib.unified_diff(left_contents, right_contents,
                                 fromfile=self.left_file,
                                 tofile=self.right_file),
            self.left_file,
            self.right_file)

    def get_details(self):
        return {}


class MatchesDir(object):
    def __init__(self, directory):
        self.__directory = directory
        self.__files = self.__get_files(directory)

    def __get_files(self, directory):
        for root, _, files in os.walk(directory):
            return files

    def __str__(self,):
        return "MatchesDir({0})".format(self.__dirname)

    def match(self, other_directory):
        other_files = self.__get_files(other_directory)

        self.__files.sort()
        other_files.sort()

        if self.__files != other_files:
            return MatchesDirMissingFilesMismatch(self.__directory,
                                                  other_directory)

        for i, file in enumerate(self.__files):
            my_file = os.path.join(self.__directory, file)
            other_file = os.path.join(other_directory, other_files[i])
            if not filecmp.cmp(my_file, other_file):
                return MatchesDirFileContentsMismatch(my_file, other_file)

        return None


@mock.patch('jenkins_jobs.builder.JenkinsManager.get_plugins_info',
            mock.MagicMock)
class TestTestsMultiPath(CmdTestsBase):

    def setUp(self):
        super(TestTestsMultiPath, self).setUp()

        path_list = [os.path.join(self.fixtures_path,
                                  'multi-path/yamldirs/', p)
                     for p in ['dir1', 'dir2']]
        self.multipath = os.pathsep.join(path_list)
        self.output_dir = tempfile.mkdtemp()

    def check_dirs_match(self, expected_dir):
        try:
            self.assertThat(self.output_dir, MatchesDir(expected_dir))
        except testtools.matchers.MismatchError:
            raise
        else:
            shutil.rmtree(self.output_dir)

    def test_multi_path(self):
        """
        Run test mode and pass multiple paths.
        """
        args = ['--conf', self.default_config_file, 'test',
                '-o', self.output_dir, self.multipath]

        self.execute_jenkins_jobs_with_args(args)
        self.check_dirs_match(os.path.join(self.fixtures_path,
                                           'multi-path/output_simple'))

    def test_recursive_multi_path_command_line(self):
        """
        Run test mode and pass multiple paths with recursive path option.
        """
        args = ['--conf', self.default_config_file, 'test',
                '-o', self.output_dir, '-r', self.multipath]

        self.execute_jenkins_jobs_with_args(args)
        self.check_dirs_match(os.path.join(self.fixtures_path,
                                           'multi-path/output_recursive'))

    def test_recursive_multi_path_config_file(self):
        # test recursive set in configuration file
        args = ['--conf', os.path.join(self.fixtures_path,
                                       'multi-path/builder-recursive.ini'),
                'test', '-o', self.output_dir, self.multipath]
        self.execute_jenkins_jobs_with_args(args)
        self.check_dirs_match(os.path.join(self.fixtures_path,
                                           'multi-path/output_recursive'))

    def test_recursive_multi_path_with_excludes(self):
        """
        Run test mode and pass multiple paths with recursive path option.
        """
        exclude_path = os.path.join(self.fixtures_path,
                                    'multi-path/yamldirs/dir2/dir1')
        args = ['--conf', self.default_config_file, 'test',
                '-x', exclude_path,
                '-o', self.output_dir,
                '-r', self.multipath]

        self.execute_jenkins_jobs_with_args(args)
        self.check_dirs_match(
            os.path.join(self.fixtures_path,
                         'multi-path/output_recursive_with_excludes'))
