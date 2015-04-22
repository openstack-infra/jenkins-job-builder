import testtools as tt
import pkg_resources
from testtools.content import text_content
from testscenarios.testcase import TestWithScenarios
from six.moves import configparser, StringIO

from jenkins_jobs import cmd
from jenkins_jobs.registry import ModuleRegistry


class ModuleRegistryPluginInfoTestsWithScenarios(TestWithScenarios,
                                                 tt.TestCase):
    scenarios = [
        ('s1', dict(v1='1.0.0', op='__gt__', v2='0.8.0')),
        ('s2', dict(v1='1.0.1alpha', op='__gt__', v2='1.0.0')),
        ('s3', dict(v1='1.0', op='__eq__', v2='1.0.0')),
        ('s4', dict(v1='1.0', op='__eq__', v2='1.0')),
        ('s5', dict(v1='1.0', op='__lt__', v2='1.8.0')),
        ('s6', dict(v1='1.0.1alpha', op='__lt__', v2='1.0.1')),
        ('s7', dict(v1='1.0alpha', op='__lt__', v2='1.0.0')),
        ('s8', dict(v1='1.0-alpha', op='__lt__', v2='1.0.0')),
        ('s9', dict(v1='1.1-alpha', op='__gt__', v2='1.0')),
        ('s10', dict(v1='1.0-SNAPSHOT', op='__lt__', v2='1.0')),
        ('s11', dict(v1='1.0.preview', op='__lt__', v2='1.0')),
        ('s12', dict(v1='1.1-SNAPSHOT', op='__gt__', v2='1.0')),
        ('s13', dict(v1='1.0a-SNAPSHOT', op='__lt__', v2='1.0a')),
    ]

    def setUp(self):
        super(ModuleRegistryPluginInfoTestsWithScenarios, self).setUp()

        config = configparser.ConfigParser()
        config.readfp(StringIO(cmd.DEFAULT_CONF))

        plugin_info = [{'shortName': "HerpDerpPlugin",
                        'longName': "Blah Blah Blah Plugin"
                        }]
        plugin_info.append({'shortName': "JankyPlugin1",
                            'longName': "Not A Real Plugin",
                            'version': self.v1
                            })

        self.addDetail("plugin_info", text_content(str(plugin_info)))
        self.registry = ModuleRegistry(config, plugin_info)

    def tearDown(self):
        super(ModuleRegistryPluginInfoTestsWithScenarios, self).tearDown()

    def test_get_plugin_info_dict(self):
        """
        The goal of this test is to validate that the plugin_info returned by
        ModuleRegistry.get_plugin_info is a dictionary whose key 'shortName' is
        the same value as the string argument passed to
        ModuleRegistry.get_plugin_info.
        """
        plugin_name = "JankyPlugin1"
        plugin_info = self.registry.get_plugin_info(plugin_name)

        self.assertIsInstance(plugin_info, dict)
        self.assertEqual(plugin_info['shortName'], plugin_name)

    def test_get_plugin_info_dict_using_longName(self):
        """
        The goal of this test is to validate that the plugin_info returned by
        ModuleRegistry.get_plugin_info is a dictionary whose key 'longName' is
        the same value as the string argument passed to
        ModuleRegistry.get_plugin_info.
        """
        plugin_name = "Blah Blah Blah Plugin"
        plugin_info = self.registry.get_plugin_info(plugin_name)

        self.assertIsInstance(plugin_info, dict)
        self.assertEqual(plugin_info['longName'], plugin_name)

    def test_get_plugin_info_dict_no_plugin(self):
        """
        The goal of this test case is to validate the behavior of
        ModuleRegistry.get_plugin_info when the given plugin cannot be found in
        ModuleRegistry's internal representation of the plugins_info.
        """
        plugin_name = "PluginDoesNotExist"
        plugin_info = self.registry.get_plugin_info(plugin_name)

        self.assertIsInstance(plugin_info, dict)
        self.assertEqual(plugin_info, {})

    def test_get_plugin_info_dict_no_version(self):
        """
        The goal of this test case is to validate the behavior of
        ModuleRegistry.get_plugin_info when the given plugin shortName returns
        plugin_info dict that has no version string. In a sane world where
        plugin frameworks like Jenkins' are sane this should never happen, but
        I am including this test and the corresponding default behavior
        because, well, it's Jenkins.
        """
        plugin_name = "HerpDerpPlugin"
        plugin_info = self.registry.get_plugin_info(plugin_name)

        self.assertIsInstance(plugin_info, dict)
        self.assertEqual(plugin_info['shortName'], plugin_name)
        self.assertEqual(plugin_info['version'], '0')

    def test_plugin_version_comparison(self):
        """
        The goal of this test case is to validate that valid tuple versions are
        ordinally correct. That is, for each given scenario, v1.op(v2)==True
        where 'op' is the equality operator defined for the scenario.
        """
        plugin_name = "JankyPlugin1"
        plugin_info = self.registry.get_plugin_info(plugin_name)
        v1 = plugin_info.get("version")

        op = getattr(pkg_resources.parse_version(v1), self.op)
        test = op(pkg_resources.parse_version(self.v2))

        self.assertTrue(test,
                        msg="Unexpectedly found {0} {2} {1} == False "
                            "when comparing versions!"
                            .format(v1, self.v2, self.op))
