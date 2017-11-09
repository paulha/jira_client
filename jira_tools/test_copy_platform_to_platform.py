from unittest import TestCase
from nose.tools import with_setup
from jira_class import Jira
from jira.resources import Issue, Status

from os.path import expanduser, pathsep, dirname, realpath
import sys
from utility_funcs.search import get_server_info, search_for_profile
import utility_funcs.logger_yaml as log

TEST_HOST = 'jira-t3'
LOG_CONFIG_FILE = 'logging.yaml' + pathsep + dirname(realpath(sys.argv[0])) + '/logging.yaml'
CONFIG_FILE = dirname(realpath(sys.argv[0])) + '/config.yaml' + pathsep + '~/.jira/config.yaml'
QUERIES_FILE = dirname(realpath(sys.argv[0])) + '/queries.yaml' + pathsep + '~/.jira/queries.yaml'
SCENARIO_FILE = 'scenarios.yaml' + pathsep + dirname(realpath(sys.argv[0])) + '/scenarios.yaml'

log_file = log.logging.getLogger("file")


class MyUpdateCase(TestCase):
    jira = None

    @classmethod
    def setUpClass(cls):
        log.setup_logging(LOG_CONFIG_FILE,
                          override={'handlers': {'info_file_handler': {'filename': 'Test_Update.log'}}})
        cls.jira = Jira(TEST_HOST, CONFIG_FILE, log.logger)
        log.logger.info("UCIS Test starting...")
        pass

    def setUp(self):
        new_ucis_dict = {
            'project': {'key': 'PREQ'},
            'summary': 'This is a Nosetest UCIS, may be deleted',
            'description': 'This UCIS was created for intgration testing',
            'issuetype': {'name': 'UCIS'},
            'assignee': {'name': 'pfhanchx'},
            self.jira.get_field_name('Android Version(s)'): [{'value': 'O-MR2'}],
            self.jira.get_field_name('Platform/Program'): [{'value': 'Icelake-U SDC'}],
            self.jira.get_field_name('Global ID'): '12345678',
            self.jira.get_field_name("Feature ID"): '12345678'
        }
        self.source_ucis = self.jira.jira_client.create_issue(fields=new_ucis_dict)
        new_ucis_dict['assignee'] = {'name': 'sys_pmdev'}
        self.target_ucis = self.jira.jira_client.create_issue(fields=new_ucis_dict)
        pass

    def tearDown(self):
        self.source_ucis.delete()
        self.target_ucis.delete()
        pass

    @classmethod
    def tearDownClass(cls):
        log.logger.info("UCIS Tests completed...")
        pass

    def test_01_no_assignment(self):
        """Should copy input to output if nothing is specified"""
        scenario = {
            # 'ASSIGNEE_OVERRIDE': 'assignee_override',
            # 'ASSIGNEE_OVERWRITE': 'assignee_overwrite',
            # 'ASSIGNEE_INHIBIT': ['inhibit_list'],
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {'assignee': {'name': 'pfhanchx'}})

    def test_02_assignee_overwrite_true(self):
        """Source copies to target if overwrite is True"""
        scenario = {
            # 'ASSIGNEE_OVERRIDE': 'assignee_override',
            'ASSIGNEE_OVERWRITE': True,
            # 'ASSIGNEE_INHIBIT': ['inhibit_list']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {'assignee': {'name': 'pfhanchx'}})

    def test_03_assignee_overwrite_false(self):
        """Assignment is inhibited if overwrite is False"""
        scenario = {
            # 'ASSIGNEE_OVERRIDE': 'assignee_override',
            'ASSIGNEE_OVERWRITE': False,
            # 'ASSIGNEE_INHIBIT': ['inhibit_list']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {})

    def test_04_assignee_overwrite_text(self):
        "If overwrite is a text value, same as True"
        scenario = {
            # 'ASSIGNEE_OVERRIDE': 'assignee_override',
            'ASSIGNEE_OVERWRITE': 'Textual Value',
            # 'ASSIGNEE_INHIBIT': ['inhibit_list']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {'assignee': {'name': 'pfhanchx'}})

    def test_05_assignee_override(self):
        """If override is specified, override value should replace original..."""
        scenario = {
            'ASSIGNEE_OVERRIDE': 'assignee_override',
            # 'ASSIGNEE_OVERWRITE': 'assignee_overwrite',
            # 'ASSIGNEE_INHIBIT': ['inhibit_list']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {'assignee': {'name': 'assignee_override'}})

    def test_06_assignee_override_false(self):
        """Override always inserts the given value..."""
        scenario = {
            'ASSIGNEE_OVERRIDE': False,
            # 'ASSIGNEE_OVERWRITE': 'assignee_overwrite',
            # 'ASSIGNEE_INHIBIT': ['inhibit_list']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {'assignee': {'name': False}})

    def test_07_assignee_inhibit_matches(self):
        """If inhibit is specified, output should be suppressed if source matches..."""
        scenario = {
            # 'ASSIGNEE_OVERRIDE': 'assignee_override',
            # 'ASSIGNEE_OVERWRITE': 'assignee_overwrite',
            'ASSIGNEE_INHIBIT': ['pfhanchx']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {})

    def test_08_assignee_inhibit_mismatches(self):
        """If inhibit is specified, output should be suppressed if source matches..."""
        scenario = {
            # 'ASSIGNEE_OVERRIDE': 'assignee_override',
            # 'ASSIGNEE_OVERWRITE': 'assignee_overwrite',
            'ASSIGNEE_INHIBIT': ['sys_pmdev']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {'assignee': {'name': 'pfhanchx'}})


class MyUpdateCaseWhenTargetIsNone(TestCase):
    jira = None

    @classmethod
    def setUpClass(cls):
        log.setup_logging(LOG_CONFIG_FILE,
                          override={'handlers': {'info_file_handler': {'filename': 'Test_Update.log'}}})
        cls.jira = Jira(TEST_HOST, CONFIG_FILE, log.logger)
        log.logger.info("UCIS Test starting...")
        pass

    def setUp(self):
        new_ucis_dict = {
            'project': {'key': 'PREQ'},
            'summary': 'This is a Nosetest UCIS, may be deleted',
            'description': 'This UCIS was created for intgration testing',
            'issuetype': {'name': 'UCIS'},
            'assignee': {'name': 'pfhanchx'},
            self.jira.get_field_name('Android Version(s)'): [{'value': 'O-MR2'}],
            self.jira.get_field_name('Platform/Program'): [{'value': 'Icelake-U SDC'}],
            self.jira.get_field_name('Global ID'): '12345678',
            self.jira.get_field_name("Feature ID"): '12345678'
        }
        self.source_ucis = self.jira.jira_client.create_issue(fields=new_ucis_dict)
        new_ucis_dict['assignee'] = {'name': 'sys_pmdev'}
        self.target_ucis = None
        pass

    def tearDown(self):
        self.source_ucis.delete()
        pass

    @classmethod
    def tearDownClass(cls):
        log.logger.info("UCIS Tests completed...")
        pass

    def test_01_no_assignment(self):
        """Should copy input to output if nothing is specified"""
        scenario = {
            # 'ASSIGNEE_OVERRIDE': 'assignee_override',
            # 'ASSIGNEE_OVERWRITE': 'assignee_overwrite',
            # 'ASSIGNEE_INHIBIT': ['inhibit_list'],
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {'assignee': {'name': 'pfhanchx'}})

    def test_02_assignee_overwrite_true(self):
        """Source copies to target if overwrite is True"""
        scenario = {
            # 'ASSIGNEE_OVERRIDE': 'assignee_override',
            'ASSIGNEE_OVERWRITE': True,
            # 'ASSIGNEE_INHIBIT': ['inhibit_list']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {'assignee': {'name': 'pfhanchx'}})

    def test_03_assignee_overwrite_false(self):
        """Assignment is inhibited if overwrite is False"""
        scenario = {
            # 'ASSIGNEE_OVERRIDE': 'assignee_override',
            'ASSIGNEE_OVERWRITE': False,
            # 'ASSIGNEE_INHIBIT': ['inhibit_list']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {})

    def test_04_assignee_overwrite_text(self):
        "If overwrite is a text value, same as True"
        scenario = {
            # 'ASSIGNEE_OVERRIDE': 'assignee_override',
            'ASSIGNEE_OVERWRITE': 'Textual Value',
            # 'ASSIGNEE_INHIBIT': ['inhibit_list']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {'assignee': {'name': 'pfhanchx'}})

    def test_05_assignee_override(self):
        """If override is specified, override value should replace original..."""
        scenario = {
            'ASSIGNEE_OVERRIDE': 'assignee_override',
            # 'ASSIGNEE_OVERWRITE': 'assignee_overwrite',
            # 'ASSIGNEE_INHIBIT': ['inhibit_list']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {'assignee': {'name': 'assignee_override'}})

    def test_06_assignee_override_false(self):
        """Override always inserts the given value..."""
        scenario = {
            'ASSIGNEE_OVERRIDE': False,
            # 'ASSIGNEE_OVERWRITE': 'assignee_overwrite',
            # 'ASSIGNEE_INHIBIT': ['inhibit_list']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {'assignee': {'name': False}})

    def test_07_assignee_inhibit_matches(self):
        """If inhibit is specified, output should be suppressed if source matches..."""
        scenario = {
            # 'ASSIGNEE_OVERRIDE': 'assignee_override',
            # 'ASSIGNEE_OVERWRITE': 'assignee_overwrite',
            'ASSIGNEE_INHIBIT': ['pfhanchx']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {})

    def test_08_assignee_inhibit_mismatches(self):
        """If inhibit is specified, output should be suppressed if source matches..."""
        scenario = {
            # 'ASSIGNEE_OVERRIDE': 'assignee_override',
            # 'ASSIGNEE_OVERWRITE': 'assignee_overwrite',
            'ASSIGNEE_INHIBIT': ['sys_pmdev']
        }
        update_fields = {}
        self.jira.update_value(update_fields, self.source_ucis, self.target_ucis, 'assignee', 'name',
                               scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE', 'ASSIGNEE_INHIBIT')
        self.assertEqual(update_fields, {'assignee': {'name': 'pfhanchx'}})


if __name__ == '__main__':
    unittest.main()
