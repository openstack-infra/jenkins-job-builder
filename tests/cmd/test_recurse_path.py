import os

from tests.base import mock
import testtools

from jenkins_jobs import utils


def fake_os_walk(paths):
    """Helper function for mocking os.walk() where must test that manipulation
    of the returned dirs variable works as expected
    """
    paths_dict = dict(paths)

    def os_walk(top, topdown=True):
        dirs, nondirs = paths_dict[top]
        yield top, dirs, nondirs
        for name in dirs:
            # hard code use of '/' to ensure the test data can be defined as
            # simple strings otherwise tests using this helper will break on
            # platforms where os.path.sep is different.
            new_path = "/".join([top, name])
            for x in os_walk(new_path, topdown):
                yield x
    return os_walk


# Testing the utils module can sometimes result in the JobCache class
# attempting to create the cache directory multiple times as the tests
# are run in parallel.  Stub out the JobCache to ensure that each
# test can safely create the object without effect.
@mock.patch('jenkins_jobs.builder.JobCache', mock.MagicMock)
class CmdRecursePath(testtools.TestCase):

    @mock.patch('jenkins_jobs.utils.os.walk')
    def test_recursive_path_option_exclude_pattern(self, oswalk_mock):
        """
        Test paths returned by the recursive processing when using pattern
        excludes.

        testing paths
            /jjb_configs/dir1/test1/
            /jjb_configs/dir1/file
            /jjb_configs/dir2/test2/
            /jjb_configs/dir3/bar/
            /jjb_configs/test3/bar/
            /jjb_configs/test3/baz/
        """

        os_walk_paths = [
            ('/jjb_configs', (['dir1', 'dir2', 'dir3', 'test3'], ())),
            ('/jjb_configs/dir1', (['test1'], ('file'))),
            ('/jjb_configs/dir2', (['test2'], ())),
            ('/jjb_configs/dir3', (['bar'], ())),
            ('/jjb_configs/dir3/bar', ([], ())),
            ('/jjb_configs/test3/bar', None),
            ('/jjb_configs/test3/baz', None)
        ]

        paths = [k for k, v in os_walk_paths if v is not None]

        oswalk_mock.side_effect = fake_os_walk(os_walk_paths)
        self.assertEqual(paths, utils.recurse_path('/jjb_configs', ['test*']))

    @mock.patch('jenkins_jobs.utils.os.walk')
    def test_recursive_path_option_exclude_absolute(self, oswalk_mock):
        """
        Test paths returned by the recursive processing when using absolute
        excludes.

        testing paths
            /jjb_configs/dir1/test1/
            /jjb_configs/dir1/file
            /jjb_configs/dir2/test2/
            /jjb_configs/dir3/bar/
            /jjb_configs/test3/bar/
            /jjb_configs/test3/baz/
        """

        os_walk_paths = [
            ('/jjb_configs', (['dir1', 'dir2', 'dir3', 'test3'], ())),
            ('/jjb_configs/dir1', None),
            ('/jjb_configs/dir2', (['test2'], ())),
            ('/jjb_configs/dir3', (['bar'], ())),
            ('/jjb_configs/test3', (['bar', 'baz'], ())),
            ('/jjb_configs/dir2/test2', ([], ())),
            ('/jjb_configs/dir3/bar', ([], ())),
            ('/jjb_configs/test3/bar', ([], ())),
            ('/jjb_configs/test3/baz', ([], ()))
        ]

        paths = [k for k, v in os_walk_paths if v is not None]

        oswalk_mock.side_effect = fake_os_walk(os_walk_paths)

        self.assertEqual(paths, utils.recurse_path('/jjb_configs',
                                                   ['/jjb_configs/dir1']))

    @mock.patch('jenkins_jobs.utils.os.walk')
    def test_recursive_path_option_exclude_relative(self, oswalk_mock):
        """
        Test paths returned by the recursive processing when using relative
        excludes.

        testing paths
            ./jjb_configs/dir1/test/
            ./jjb_configs/dir1/file
            ./jjb_configs/dir2/test/
            ./jjb_configs/dir3/bar/
            ./jjb_configs/test3/bar/
            ./jjb_configs/test3/baz/
        """

        os_walk_paths = [
            ('jjb_configs', (['dir1', 'dir2', 'dir3', 'test3'], ())),
            ('jjb_configs/dir1', (['test'], ('file'))),
            ('jjb_configs/dir2', (['test2'], ())),
            ('jjb_configs/dir3', (['bar'], ())),
            ('jjb_configs/test3', (['bar', 'baz'], ())),
            ('jjb_configs/dir1/test', ([], ())),
            ('jjb_configs/dir2/test2', ([], ())),
            ('jjb_configs/dir3/bar', ([], ())),
            ('jjb_configs/test3/bar', None),
            ('jjb_configs/test3/baz', ([], ()))
        ]

        rel_os_walk_paths = [
            (os.path.abspath(
                os.path.join(os.path.curdir, k)), v) for k, v in os_walk_paths]

        paths = [k for k, v in rel_os_walk_paths if v is not None]

        oswalk_mock.side_effect = fake_os_walk(rel_os_walk_paths)

        self.assertEqual(paths, utils.recurse_path('jjb_configs',
                                                   ['jjb_configs/test3/bar']))
