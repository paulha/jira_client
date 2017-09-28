import sys
from os.path import pathsep, dirname, realpath
from utility_funcs import strip_non_ascii
import utility_funcs.logger_yaml as log

from otc_tool import Jira
import json

from navigate import State, StateMachine

JIRA = 'jira'
JAMA = 'jama'
HOST = 'host'
PROJECT = 'project'
PLATFORM = 'platform'
VERSION = 'version'
WORKSPACE = 'workspace'
QUERY = 'query'
PREFIX = 'prefix'

non_aaag_query = 'project = "{jproject}" AND "Platform/Program" = "{jplatform}" '\
                 'AND summary !~ "\\\\[AaaG\\\\]"' \
                 'AND "Android Version(s)" in ({jversion}) AND type = UCIS order by key'  # order by summary'
aaag_query = 'project = "{jproject}" AND "Platform/Program" = "{jplatform}" '\
             'AND summary ~ "\\\\[AaaG\\\\]"' \
             'AND "Android Version(s)" in ({jversion}) AND type = UCIS order by key'  # order by summary'


PRODUCTION =    { JIRA: {HOST: 'jira01', PROJECT: 'PREQ', PLATFORM: 'Icelake-U SDC', VERSION: 'O',
                         QUERY: non_aaag_query, PREFIX: None},
                  JAMA: {HOST: 'jama-production', PROJECT: '5_555', PLATFORM: 'Icelake-U SDC [O]', VERSION: 'O', WORKSPACE: '5_555-WS-17'}}
PRODUCTION_AAAG =    \
                { JIRA: {HOST: 'jira01', PROJECT: 'PREQ', PLATFORM: 'Icelake-U SDC', VERSION: 'O',
                         QUERY: aaag_query, PREFIX: ' [AaaG]'},
                  JAMA: {HOST: 'jama-production', PROJECT: '5_555', PLATFORM: 'Icelake-U SDC [O][AaaG]', VERSION: 'O', WORKSPACE: '5_555-WS-17'}}
PRODUCTION2=    { JIRA: {HOST: 'jira01', PROJECT: 'PREQ', PLATFORM: 'Icelake-U SDC', VERSION: 'O-MR1',
                         QUERY: non_aaag_query, PREFIX: None},
                  JAMA: {HOST: 'jama-production', PROJECT: '5_555', PLATFORM: 'Icelake-U SDC [O-MR1]', VERSION: 'O', WORKSPACE: '5_555-WS-22'}}
SANDBOX =       { JIRA: {HOST: 'jira-t3', PROJECT: 'PREQ', PLATFORM: 'Icelake-U SDC', VERSION: 'O',
                         QUERY: non_aaag_query, PREFIX: None},
                  JAMA: {HOST: 'jama-test', PROJECT: '5_555', PLATFORM: 'Icelake-U SDC', VERSION: 'O', WORKSPACE: '5_555-WS-17'}}
EVALUATION =    { JIRA: {HOST: 'jira-stg', PROJECT: 'PREQ', PLATFORM: 'Icelake-U SDC', VERSION: 'O',
                         QUERY: non_aaag_query, PREFIX: None},
                  JAMA: {HOST: 'jama-eval', PROJECT: 'SI_SOL', PLATFORM: 'Solution', VERSION: 'O', WORKSPACE: None}}
DEFAULT = PRODUCTION

# -- NOTE: Use this to set execution environment
ACTIVE_ENVIRONMENT = PRODUCTION     # _AAAG

LOG_CONFIG_FILE = 'logging.yaml'+pathsep+dirname(realpath(sys.argv[0]))+'/logging.yaml'
log.setup_logging("logging.yaml", override={'handlers': {'info_file_handler': {'filename': 'audit_jama_jira_matchup.log'}}})
log.logger.setLevel(log.logging.getLevelName("INFO"))
log.logger.disabled = False

# ======================================================================================================
#
#   Set up Jira
#
# ======================================================================================================
JIRA_CONFIG_FILE = dirname(realpath(sys.argv[0])) + '/config.yaml' + pathsep + '~/.jira/config.yaml'

Feature_Rejected = State('Rejected', ["Rejected", "Reject"])
Feature_In_Review = State('In Review', ['In Review'])
Feature_Blocked = State('Blocked', ['Blocked'])
Feature_New = State('New', ['New'])
Feature_Rejected = State('Rejected', ['Reject', 'Rejected'])
Feature_Candidate = State('Candidate', ['Candidate'])
Feature_Deprecated = State('Deprecated', ['Deprecated'])

Feature_map = {
    'New': [Feature_In_Review, Feature_Blocked, Feature_Rejected],
    'Rejected': [Feature_In_Review, Feature_New, Feature_Blocked],
    'Blocked': [Feature_Blocked,Feature_In_Review, Feature_Rejected],
    'In Review': [Feature_Candidate, Feature_Blocked, Feature_New, Feature_Rejected],
    'Candidate': [Feature_In_Review, Feature_Deprecated],
    'Deprecated': [Feature_Candidate]
}


Feature_Transitions = {
    'New' : {"Rejected": "141", "In Review": "151", "Blocked": "131"},
    'Rejected': {"In Review": "91", "New": "181", "Blocked": "131"},
    'Blocked': {"New": "171", "In Review": "191", "Reject": "201"},
    'In Review': {"Reject": "51", "Candidate": "61", "New": "161", "Blocked": "131"},
    'Candidate': {"In Review": "101", "Deprecated": "111"},
    'Deprecated': {"Candidate": "121"}
}

E_Feature_Open = State('Open', ['Open'])
E_Feature_Close = State('Close', ['Close'])
E_Feature_Reject = State('Reject', ['Reject'])
E_Feature_Start_Progress = State('Start Progress', ['Start Progress'])
E_Feature_In_Progress = State('In Progress', ['In Progress'])
E_Feature_Blocked = State('Blocked', ['Blocked'])
E_Feature_Merge = State('Merge', ['Merge'])
E_Feature_Reopen = State('Reopen', ['Reopen'])
E_Feature_Update_From_Parent = State("Update From Parent", ["Update From Parent"])

E_Feature_map = {
    # -- NOTE: That transition values depend on the starting state, even when the end state is the same!
    'Open': [E_Feature_Update_From_Parent, E_Feature_Start_Progress, E_Feature_Reject],
    'Reject': [E_Feature_Open, E_Feature_Update_From_Parent],
    # -- note: Update From Parent (sometimes!) leaves you in 'Start Progress'
    'Start Progress': [E_Feature_Blocked, E_Feature_Update_From_Parent, E_Feature_Merge, E_Feature_Reject],
    'Blocked': [E_Feature_Blocked, E_Feature_Update_From_Parent, E_Feature_In_Progress, E_Feature_Reject],
    'In Progress': [E_Feature_Blocked, E_Feature_Update_From_Parent, E_Feature_Merge, E_Feature_Reject],
    'Merge': [E_Feature_Close, E_Feature_Update_From_Parent, E_Feature_Reject, E_Feature_Reopen],
    # -- note: this is the same as Start Progress
    'Reopen': [E_Feature_Blocked, E_Feature_Update_From_Parent, E_Feature_Merge, E_Feature_Reject],
    'Close': [E_Feature_Update_From_Parent, E_Feature_Reject],
}

E_Feature_Transitions = {
    # -- NOTE: That transition values depend on the starting state, even when the end state is the same!
    'Open': {"Update From Parent": "831", "Start Progress": "1021", "Reject": "1001"},
    'Reject': {"Open": "921", "Update from Parent": "991"},
    # -- note: Update From Parent (sometimes!) leaves you in 'Start Progress'
    'Start Progress': {"Blocked": "411", "Update From Parent": "771", "Merge": "871", "Reject": "1001"},
    'Blocked': {"Merge": "671", "Update From Parent": "821", "In Progress": "1011", "Reject": "1001"},
    'In Progress': {"Blocked": "411", "Update From Parent": "771", "Merge": "871", "Reject": "1001"},
    'Merge': {"Close": "121", "Update From Parent": "791", "Reject": "1001", "Reopen": "441"},
    # -- note: this is the same as Start Progress
    'Reopen': {"Blocked": "411", "Update From Parent": "771", "Merge": "871", "Reject": "1001"},
    'Close': {"Update From Parent": "801", "Reject": "1001"}
}

UCUS_Open = State('Open', ['Open', "Reopen"])
UCIS_Start_Progress = State('Start Progress', ['Start Progress'])
UCIS_Rejected = State('Rejected', ['Rejected', "To Rejected"])
UCIS_Blocked = State('Blocked', ['Blocked', "To Blocked"])
UCIS_Merged = State('Merged', ['Merged', "To Merged"])
UCIS_Close = State('Close', ["Edit Closed Issues", "Close Issue"])
UCIS_Edit_Closed_Issue = State("Edit Closed Issues", ["Edit Closed Issues"])

UCIS_map = {
    'Open': [UCIS_Start_Progress, UCIS_Rejected],
    'Start Progress': [UCIS_Blocked, UCIS_Rejected, UCIS_Merged],
    'Rejected': [UCUS_Open],
    'Blocked': [UCIS_Rejected, UCIS_Start_Progress, UCIS_Merged],
    'Merged': [UCUS_Open, UCIS_Close, UCIS_Rejected],
    'Close': [UCIS_Edit_Closed_Issue, E_Feature_Reject]
}

UCIS_Transitions = {
    'Open': {"Start Progress": "11", "To Rejected": "51"},
    'Start Progress': {"To Blocked": "71", "To Rejected": "51", "To Merged": "41"},
    'Rejected': {"To Open": "61"},
    'Blocked': {"To Rejected": "51", "Start Progress": "11", "To Merged": "41"},
    'Merged': {"Reopen": "91", "Close Issue": "31", "Rejected": "81"},
    'Close': {"Edit Closed Issues": "101", "Rejected": "81"}
}

def main():
    ucis_machine = StateMachine(state_map=UCIS_map)
    feature_machine = StateMachine(state_map=Feature_map)
    e_feature_machine = StateMachine(state_map=E_Feature_map)

    logger = log.logging.getLogger("root")
    logger.setLevel(log.logging.getLevelName("INFO"))

    jira = Jira(ACTIVE_ENVIRONMENT[JIRA][HOST], JIRA_CONFIG_FILE, logger)

    feature = jira.jira_client.issue("AREQ-26032")
    goal = Feature_New

    feature_machine.transition_to_state(jira, feature, goal, log)


    # feature_transitions = jira.jira_client.transitions(feature)
    # print(json.dumps({next['name']: next['id'] for next in feature_transitions}))

    # e_feature = jira.jira_client.issue("AREQ-26033")
    #
    # ucis = jira.jira_client.issue("PREQ-27213")
    # print(json.dumps({next['name']: next['id'] for next in jira.jira_client.transitions(ucis)}))
    # print(jira.jira_client.transition_issue(issue,21))
    # print([(next['id'], next['name']) for next in jira.jira_client.transitions(issue)])



if __name__ == '__main__':
    main()
