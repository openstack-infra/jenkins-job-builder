import os
from six.moves import configparser, StringIO
import testtools
from jenkins_jobs import cmd
from tests.base import mock


class CmdTestsBase(testtools.TestCase):

    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    parser = cmd.create_parser()

    def setUp(self):
        super(CmdTestsBase, self).setUp()

        # Testing the cmd module can sometimes result in the CacheStorage class
        # attempting to create the cache directory multiple times as the tests
        # are run in parallel.  Stub out the CacheStorage to ensure that each
        # test can safely create the cache directory without risk of
        # interference.
        cache_patch = mock.patch('jenkins_jobs.builder.CacheStorage',
                                 autospec=True)
        self.cache_mock = cache_patch.start()
        self.addCleanup(cache_patch.stop)

        self.config = configparser.ConfigParser()
        self.config.readfp(StringIO(cmd.DEFAULT_CONF))


class CmdTests(CmdTestsBase):

    def test_with_empty_args(self):
        """
        User passes no args, should fail with SystemExit
        """
        with mock.patch('sys.stderr'):
            self.assertRaises(SystemExit, cmd.main, [])
