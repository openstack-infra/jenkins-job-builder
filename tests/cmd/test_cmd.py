import os
import ConfigParser
import cStringIO
import codecs
import mock
import testtools
from jenkins_jobs import cmd


# Testing the cmd module can sometimes result in the CacheStorage class
# attempting to create the cache directory multiple times as the tests
# are run in parallel.  Stub out the CacheStorage to ensure that each
# test can safely create the cache directory without risk of interference.
@mock.patch('jenkins_jobs.builder.CacheStorage', mock.MagicMock)
class CmdTests(testtools.TestCase):

    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    parser = cmd.create_parser()

    def test_with_empty_args(self):
        """
        User passes no args, should fail with SystemExit
        """
        with mock.patch('sys.stderr'):
            self.assertRaises(SystemExit, self.parser.parse_args, [])

    def test_non_existing_config_dir(self):
        """
        Run test mode and pass a non-existing configuration directory
        """
        args = self.parser.parse_args(['test', 'foo'])
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        self.assertRaises(IOError, cmd.execute, args, config)

    def test_non_existing_config_file(self):
        """
        Run test mode and pass a non-existing configuration file
        """
        args = self.parser.parse_args(['test', 'non-existing.yaml'])
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        self.assertRaises(IOError, cmd.execute, args, config)

    def test_non_existing_job(self):
        """
        Run test mode and pass a non-existing job name
        (probably better to fail here)
        """
        args = self.parser.parse_args(['test',
                                       os.path.join(self.fixtures_path,
                                                    'cmd-001.yaml'),
                                       'invalid'])
        args.output_dir = mock.MagicMock()
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        cmd.execute(args, config)   # probably better to fail here

    def test_valid_job(self):
        """
        Run test mode and pass a valid job name
        """
        args = self.parser.parse_args(['test',
                                       os.path.join(self.fixtures_path,
                                                    'cmd-001.yaml'),
                                       'foo-job'])
        args.output_dir = mock.MagicMock()
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        cmd.execute(args, config)   # probably better to fail here

    def test_console_output(self):
        """
        Run test mode and verify that resulting XML gets sent to the console.
        """

        console_out = cStringIO.StringIO()
        with mock.patch('sys.stdout', console_out):
            cmd.main(['test', os.path.join(self.fixtures_path,
                      'cmd-001.yaml')])
        xml_content = u"%s" % codecs.open(os.path.join(self.fixtures_path,
                                                       'cmd-001.xml'),
                                          'r',
                                          'utf-8').read()
        self.assertEqual(console_out.getvalue(), xml_content)

    def test_config_with_test(self):
        """
        Run test mode and pass a config file
        """
        args = self.parser.parse_args(['--conf',
                                       os.path.join(self.fixtures_path,
                                                    'cmd-001.conf'),
                                       'test',
                                       os.path.join(self.fixtures_path,
                                                    'cmd-001.yaml'),
                                       'foo-job'])
        config = cmd.setup_config_settings(args)
        self.assertEqual(config.get('jenkins', 'url'),
                         "http://test-jenkins.with.non.default.url:8080/")

    @mock.patch('jenkins_jobs.cmd.Builder.update_job')
    @mock.patch('jenkins_jobs.cmd.os.path.isdir')
    @mock.patch('jenkins_jobs.cmd.os.walk')
    def test_recursive_path_option(self, os_walk_mock, isdir_mock,
                                   update_job_mock):
        """
        Test handling of recursive path option
        """

        os_walk_mock.return_value = [
            ('/jjb_configs', ('dir1', 'dir2', 'dir3'), ()),
            ('/jjb_configs/dir1', ('bar',), ()),
            ('/jjb_configs/dir2', ('baz',), ()),
            ('/jjb_configs/dir3', (), ()),
            ('/jjb_configs/dir1/bar', (), ()),
            ('/jjb_configs/dir2/baz', (), ()),
        ]
        isdir_mock.return_value = True
        paths = [path for path, _, _ in os_walk_mock.return_value]

        args = self.parser.parse_args(['test', '-r', '/jjb_configs'])
        args.output_dir = mock.MagicMock()
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        cmd.execute(args, config)   # probably better to fail here

        update_job_mock.assert_called_with(paths, [], output=args.output_dir)

        args = self.parser.parse_args(['test', '/jjb_configs'])
        config.set('job_builder', 'recursive', 'True')
        cmd.execute(args, config)   # probably better to fail here

        update_job_mock.assert_called_with(paths, [], output=args.output_dir)
