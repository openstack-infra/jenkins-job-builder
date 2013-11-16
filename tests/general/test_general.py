import os
from testtools import TestCase
from testscenarios.testcase import TestWithScenarios
from jenkins_jobs.modules import general
from tests.base import get_scenarios, BaseTestCase


class TestCaseModuleGeneral(TestWithScenarios, TestCase, BaseTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    scenarios = get_scenarios(fixtures_path)
    klass = general.General
