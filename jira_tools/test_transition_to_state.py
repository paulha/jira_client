from unittest import TestCase
from nose.tools import with_setup
from os.path import expanduser, pathsep, dirname, realpath
import sys
from utility_funcs.search import get_server_info, search_for_profile
import utility_funcs.logger_yaml as log
from jira_class import Jira
from jira.resources import Issue, Status

from navigate import *

TEST_HOST = 'jira-t3'
LOG_CONFIG_FILE = 'logging.yaml'+pathsep+dirname(realpath(sys.argv[0]))+'/logging.yaml'
CONFIG_FILE = dirname(realpath(sys.argv[0]))+'/config.yaml'+pathsep+'~/.jira/config.yaml'
QUERIES_FILE = dirname(realpath(sys.argv[0]))+'/queries.yaml'+pathsep+'~/.jira/queries.yaml'
SCENARIO_FILE = 'scenarios.yaml'+pathsep+dirname(realpath(sys.argv[0]))+'/scenarios.yaml'

log_file = log.logging.getLogger("file")


class TestTransition_to_state(TestCase):
    def check_transition_pairs(self, item: Issue, tuples_list: list):
        for tuple in tuples_list:
            log.logger.info("==> Now testing %s", tuple)
            start, end = tuple
            item = transition_to_state(self.jira, item, State(start, []), log)
            self.assertEqual(start, item.fields.status.name,
                             "Initial status of item should be %s" % start)

            item = transition_to_state(self.jira, item, State(end, []), log)
            self.assertEqual(end, item.fields.status.name,
                             "Completion status of item should be %s" % end)


class E_FeatureTestTransition_to_state(TestTransition_to_state):
    jira = None
    feature = None

    @classmethod
    def setUpClass(cls):
        log.setup_logging(LOG_CONFIG_FILE,
                          override={'handlers': {'info_file_handler': {'filename': 'TestTransition_to_state.log'}}})
        cls.jira = Jira(TEST_HOST, CONFIG_FILE, log.logger)
        log.logger.info("E-Feature Test starting...")

        # -- Create a common Parent Feature...
        new_feature_dict = {
            'project': {'key': 'AREQ'},
            'summary': 'This is a Nosetest Feature, may be deleted',
            'description': 'This Feature was created for intgration testing',
            'issuetype': {'name': 'Feature'},
            'assignee': {'name': 'pfhanchx'},
            'components': [{'name': 'Unknown'}],
            cls.jira.get_field_name('Android Version(s)'): [{'value': 'O-MR2'}],
            cls.jira.get_field_name('Platform/Program'): [{'value': 'Icelake-U SDC'}],
            cls.jira.get_field_name('Classification'): [{'value': 'Functional'}],
            cls.jira.get_field_name('Profile/s'): [{'value': 'Other'}],
        }
        cls.feature = cls.jira.jira_client.create_issue(fields=new_feature_dict)
        pass

    def setUp(self):
        new_e_feature_dict = {
            'project': {'key': self.feature.fields.project.key},
            'parent': {'key': self.feature.key},
            'summary': 'This E-Feature was created for intgration testing',
            'issuetype': {'name': 'E-Feature'},
            self.jira.get_field_name('Android Version(s)'): [{'value': 'O-MR2'}],
            self.jira.get_field_name('Platform/Program'): [{'value': 'Icelake-U SDC'}],
            # and_vers_key: [{'value': scenario['tversion']}],
            # platprog_key: [{'value': scenario['tplatform']}],
            # 'assignee': {'name': sibling.fields.assignee.name},
            # validation_lead: {'name': val_lead.name if val_lead is not None else ""}
        }
        self.e_feature = self.jira.jira_client.create_issue(fields=new_e_feature_dict)
        pass

    def tearDown(self):
        self.e_feature.delete()
        pass

    @classmethod
    def tearDownClass(cls):
        cls.feature.delete()
        log.logger.info("E-Feature Tests completed...")
        pass
    
    def test_01_starts_at_Open(self):
        self.assertEqual(E_Feature_Open.name, self.e_feature.fields.status.name, "Initial status of a E-Feature should be Open")

    def test_02_move_to_Open(self):
        transition_to_state(self.jira, self.e_feature, E_Feature_Open, log)
        self.assertEqual(E_Feature_Open.name, self.e_feature.fields.status.name, "Initial status of a E-Feature should be Open")

    def test_03_move_to_In_Progress(self):
        self.e_feature = transition_to_state(self.jira, self.e_feature, E_Feature_In_Progress, log)
        self.assertEqual(E_Feature_In_Progress.name, self.e_feature.fields.status.name, "E-Feature should be In Progress")

    def test_04_move_to_Blocked(self):
        self.e_feature = transition_to_state(self.jira, self.e_feature, E_Feature_Blocked, log)
        self.assertEqual(E_Feature_Blocked.name, self.e_feature.fields.status.name, "E-Feature should be Blocked")

    def test_05_move_to_Merged(self):
        self.e_feature = transition_to_state(self.jira, self.e_feature, E_Feature_Merge, log)
        self.assertEqual(E_Feature_Merge.name, self.e_feature.fields.status.name, "E-Feature should be Merged")

    def test_06_move_to_Rejected(self):
        self.e_feature = transition_to_state(self.jira, self.e_feature, E_Feature_Rejected, log)
        self.assertEqual(E_Feature_Rejected.name, self.e_feature.fields.status.name, "Feature should be Rejected")

    def test_07_move_to_Closed(self):
        # Note: Need to set 'Actual Release' for this to succeed:
        update_fields = {
            self.jira.get_field_name("Actual Release"): {'value': '2017ww01'}
        }
        self.e_feature.update(notify=False, fields=update_fields)
        self.e_feature = transition_to_state(self.jira, self.e_feature, E_Feature_Close, log)
        self.assertEqual(E_Feature_Close.name, self.e_feature.fields.status.name, "Feature should be Closed")
    
    def test_08_check_multiple_transitions(self):
        # -- This is needed to ensure that item can be set to Closed.
        update_fields = {
            self.jira.get_field_name("Actual Release"): {'value': '2017ww01'}
        }
        self.e_feature.update(notify=False, fields=update_fields)

        self.check_transition_pairs(self.e_feature, E_Feature_Targets.keys())


class FeatureTestTransition_to_state(TestTransition_to_state):
    jira = None

    @classmethod
    def setUpClass(cls):
        log.setup_logging(LOG_CONFIG_FILE,
                          override={'handlers': {'info_file_handler': {'filename': 'TestTransition_to_state.log'}}})
        cls.jira = Jira(TEST_HOST, CONFIG_FILE, log.logger)
        log.logger.info("Feature Test starting...")
        pass

    def setUp(self):
        new_e_feature_dict = {
            'project': {'key': 'AREQ'},
            'summary': 'This is a Nosetest Feature, may be deleted',
            'description': 'This Feature was created for intgration testing',
            'issuetype': {'name': 'Feature'},
            'assignee': {'name': 'pfhanchx'},
            self.jira.get_field_name('Android Version(s)'): [{'value': 'O-MR2'}],
            self.jira.get_field_name('Platform/Program'): [{'value': 'Icelake-U SDC'}],
            self.jira.get_field_name('Classification'): [{'value': 'Functional'}],
            'components': [{'name': 'Unknown'}],
            self.jira.get_field_name('Profile/s'): [{'value': 'Other'}],
        }
        self.feature = self.jira.jira_client.create_issue(fields=new_e_feature_dict)
        pass

    def tearDown(self):
        self.feature.delete()
        pass

    @classmethod
    def tearDownClass(cls):
        log.logger.info("Feature Tests completed...")
        pass

    def test_01_starts_at_New(self):
        self.assertEqual(Feature_New.name, self.feature.fields.status.name, "Initial status of a Feature should be New")

    def test_02_move_to_New(self):
        transition_to_state(self.jira, self.feature, Feature_New, log)
        self.assertEqual(Feature_New.name, self.feature.fields.status.name, "Initial status of a Feature should be New")

    def test_03_move_to_In_Review(self):
        self.feature = transition_to_state(self.jira, self.feature, Feature_In_Review, log)
        self.assertEqual(Feature_In_Review.name, self.feature.fields.status.name, "Feature should be In Review")

    def test_04_move_to_Blocked(self):
        self.feature = transition_to_state(self.jira, self.feature, Feature_Blocked, log)
        self.assertEqual(Feature_Blocked.name, self.feature.fields.status.name, "Feature should be Blocked")

    def test_05_move_to_Deprecated(self):
        self.feature = transition_to_state(self.jira, self.feature, Feature_Deprecated, log)
        self.assertEqual(Feature_Deprecated.name, self.feature.fields.status.name, "Feature should be Deprecated")

    def test_06_move_to_Rejected(self):
        self.feature = transition_to_state(self.jira, self.feature, Feature_Rejected, log)
        self.assertEqual(Feature_Rejected.name, self.feature.fields.status.name, "Feature should be Rejected")

    def test_07_move_to_Closed(self):
        # Note: Need to set 'Actual Release' for this to succeed:
        # update_fields = {
        #     self.jira.get_field_name("Actual Release"): {'value': '2017ww01'}
        # }
        # self.feature.update(notify=False, fields=update_fields)
        self.feature = transition_to_state(self.jira, self.feature, Feature_Candidate, log)
        self.assertEqual(Feature_Candidate.name, self.feature.fields.status.name, "Feature should be Candidate")

    def test_08_check_multiple_transitions(self):
        self.check_transition_pairs(self.feature, Feature_Targets.keys())


class UCISTestTransition_to_state(TestTransition_to_state):
    jira = None

    @classmethod
    def setUpClass(cls):
        log.setup_logging(LOG_CONFIG_FILE,
                          override={'handlers': {'info_file_handler': {'filename': 'TestTransition_to_state.log'}}})
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
        self.ucis = self.jira.jira_client.create_issue(fields=new_ucis_dict)
        pass

    def tearDown(self):
        self.ucis.delete()
        pass

    @classmethod
    def tearDownClass(cls):
        log.logger.info("UCIS Tests completed...")
        pass

    def test_01_starts_at_Open(self):
        self.assertEqual(UCIS_Open.name, self.ucis.fields.status.name, "Initial status of a UCIS should be Open")

    def test_02_move_to_Open(self):
        transition_to_state(self.jira, self.ucis, UCIS_Open, log)
        self.assertEqual(UCIS_Open.name, self.ucis.fields.status.name, "Initial status of a UCIS should be Open")

    def test_03_move_to_In_Progress(self):
        self.ucis = transition_to_state(self.jira, self.ucis, UCIS_In_Progress, log)
        self.assertEqual(UCIS_In_Progress.name, self.ucis.fields.status.name, "UCIS should be In Progress")

    def test_04_move_to_Blocked(self):
        self.ucis = transition_to_state(self.jira, self.ucis, UCIS_Blocked, log)
        self.assertEqual(UCIS_Blocked.name, self.ucis.fields.status.name, "UCIS should be Blocked")

    def test_05_move_to_Merged(self):
        self.ucis = transition_to_state(self.jira, self.ucis, UCIS_Merged, log)
        self.assertEqual(UCIS_Merged.name, self.ucis.fields.status.name, "UCIS should be Merged")

    def test_06_move_to_Rejected(self):
        self.ucis = transition_to_state(self.jira, self.ucis, UCIS_Reject, log)
        self.assertEqual(UCIS_Reject.name, self.ucis.fields.status.name, "UCIS should be Rejected")

    def test_07_move_to_Closed(self):
        # Note: Need to set 'Actual Release' for this to succeed:
        update_fields = {
            self.jira.get_field_name("Actual Release"): {'value': '2017ww01'}
        }
        self.ucis.update(notify=False, fields=update_fields)
        self.ucis = transition_to_state(self.jira, self.ucis, UCIS_Close, log)
        self.assertEqual(UCIS_Close.name, self.ucis.fields.status.name, "UCIS should be Closed")

    def test_08_check_multiple_transitions(self):
        # -- This is needed to ensure that item can be set to Closed.
        update_fields = {
            self.jira.get_field_name("Actual Release"): {'value': '2017ww01'}
        }
        self.ucis.update(notify=False, fields=update_fields)

        self.check_transition_pairs(self.ucis, UCIS_Targets.keys())

