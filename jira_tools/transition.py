import sys
from os.path import pathsep, dirname, realpath
from utility_funcs import strip_non_ascii
import utility_funcs.logger_yaml as log

from otc_tool import Jira
import json

# from navigate import State, StateMachine
from navigate import *

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

def main():
    ucis_machine = StateMachine(state_map=UCIS_map)
    feature_machine = StateMachine(state_map=Feature_map)
    e_feature_machine = StateMachine(state_map=E_Feature_map)

    logger = log.logging.getLogger("root")
    logger.setLevel(log.logging.getLevelName("INFO"))

    jira = Jira(ACTIVE_ENVIRONMENT[JIRA][HOST], JIRA_CONFIG_FILE, logger)

    feature = jira.jira_client.issue("AREQ-26032")
    goal = Feature_New

    StateMachine.transition_to_state(jira, feature, goal, log)


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
