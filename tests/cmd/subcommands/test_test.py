import os
import io
import codecs
import mock
from jenkins_jobs import cmd
from tests.cmd.test_cmd import CmdTestsBase


os_walk_return_values = {
    '/jjb_projects': [
        ('/jjb_projects', ('dir1', 'dir2', 'dir3'), ()),
        ('/jjb_projects/dir1', ('bar',), ()),
        ('/jjb_projects/dir2', ('baz',), ()),
        ('/jjb_projects/dir3', (), ()),
        ('/jjb_projects/dir1/bar', (), ()),
        ('/jjb_projects/dir2/baz', (), ()),
    ],
    '/jjb_templates': [
        ('/jjb_templates', ('dir1', 'dir2', 'dir3'), ()),
        ('/jjb_templates/dir1', ('bar',), ()),
        ('/jjb_templates/dir2', ('baz',), ()),
        ('/jjb_templates/dir3', (), ()),
        ('/jjb_templates/dir1/bar', (), ()),
        ('/jjb_templates/dir2/baz', (), ()),
    ],
    '/jjb_macros': [
        ('/jjb_macros', ('dir1', 'dir2', 'dir3'), ()),
        ('/jjb_macros/dir1', ('bar',), ()),
        ('/jjb_macros/dir2', ('baz',), ()),
        ('/jjb_macros/dir3', (), ()),
        ('/jjb_macros/dir1/bar', (), ()),
        ('/jjb_macros/dir2/baz', (), ()),
    ],
}


def os_walk_side_effects(path_name, topdown):
    return os_walk_return_values[path_name]


class TestTests(CmdTestsBase):

    def test_non_existing_config_dir(self):
        """
        Run test mode and pass a non-existing configuration directory
        """
        args = self.parser.parse_args(['test', 'foo'])
        self.assertRaises(IOError, cmd.execute, args, self.config)

    def test_non_existing_config_file(self):
        """
        Run test mode and pass a non-existing configuration file
        """
        args = self.parser.parse_args(['test', 'non-existing.yaml'])
        self.assertRaises(IOError, cmd.execute, args, self.config)

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
        cmd.execute(args, self.config)   # probably better to fail here

    def test_valid_job(self):
        """
        Run test mode and pass a valid job name
        """
        args = self.parser.parse_args(['test',
                                       os.path.join(self.fixtures_path,
                                                    'cmd-001.yaml'),
                                       'foo-job'])
        args.output_dir = mock.MagicMock()
        cmd.execute(args, self.config)   # probably better to fail here

    @mock.patch('jenkins_jobs.cmd.Builder.update_job')
    def test_multi_path(self, update_job_mock):
        """
        Run test mode and pass multiple paths.
        """
        path_list = list(os_walk_return_values.keys())
        multipath = os.pathsep.join(path_list)

        args = self.parser.parse_args(['test', multipath])
        args.output_dir = mock.MagicMock()

        cmd.execute(args, self.config)
        self.assertEqual(args.path, path_list)
        update_job_mock.assert_called_with(path_list, [],
                                           output=args.output_dir)

    @mock.patch('jenkins_jobs.cmd.Builder.update_job')
    @mock.patch('jenkins_jobs.cmd.os.path.isdir')
    @mock.patch('jenkins_jobs.cmd.os.walk')
    def test_recursive_multi_path(self, os_walk_mock, isdir_mock,
                                  update_job_mock):
        """
        Run test mode and pass multiple paths with recursive path option.
        """

        os_walk_mock.side_effect = os_walk_side_effects
        isdir_mock.return_value = True

        path_list = os_walk_return_values.keys()
        paths = []
        for path in path_list:
            paths.extend([p for p, _, _ in
                          os_walk_return_values[path]])

        multipath = os.pathsep.join(path_list)

        args = self.parser.parse_args(['test', '-r', multipath])
        args.output_dir = mock.MagicMock()

        cmd.execute(args, self.config)

        update_job_mock.assert_called_with(paths, [], output=args.output_dir)

        args = self.parser.parse_args(['test', multipath])
        self.config.set('job_builder', 'recursive', 'True')
        cmd.execute(args, self.config)

        update_job_mock.assert_called_with(paths, [], output=args.output_dir)

    def test_console_output(self):
        """
        Run test mode and verify that resulting XML gets sent to the console.
        """

        console_out = io.BytesIO()
        with mock.patch('sys.stdout', console_out):
            cmd.main(['test', os.path.join(self.fixtures_path,
                      'cmd-001.yaml')])
        xml_content = codecs.open(os.path.join(self.fixtures_path,
                                               'cmd-001.xml'),
                                  'r', 'utf-8').read()
        self.assertEqual(console_out.getvalue().decode('utf-8'), xml_content)

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
