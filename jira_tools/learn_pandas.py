from os.path import expanduser, pathsep, dirname, realpath
import sys
from utility_funcs.search import get_server_info, search_for_profile
import utility_funcs.logger_yaml as log

LOG_CONFIG_FILE = 'logging.yaml'+pathsep+dirname(realpath(sys.argv[0]))+'/logging.yaml'
CONFIG_FILE = dirname(realpath(sys.argv[0]))+'/config.yaml'+pathsep+'~/.jira/config.yaml'
QUERIES_FILE = dirname(realpath(sys.argv[0]))+'/queries.yaml'+pathsep+'~/.jira/queries.yaml'
SCENARIO_FILE = 'scenarios.yaml'+pathsep+dirname(realpath(sys.argv[0]))+'/scenarios.yaml'

log_file = log.logging.getLogger("file")
log.setup_logging(LOG_CONFIG_FILE, override={'handlers': {'info_file_handler': {'filename': 'jupyter.log'}}})

from jira_class import Jira, get_query
from navigate import *
from jira.exceptions import JIRAError
jira = Jira('jira-t3', CONFIG_FILE, log.logger)

import pandas as pd


def readout(jira, item, limit_to={}):
    result = {}
    for field in vars(item):
        if field.startswith("__") \
                or field.startswith("TimeTracking") \
                or getattr(item, field) is None:
            continue
        value = getattr(item, field)
        name = field
        try:
            name = jira.jira_field_lookup[field]
        except:
            pass
        if name.startswith("Time")\
                or limit_to != {} and name not in limit_to:
            continue
        result[name] = value

    return result

issue = jira.issue("AREQ-1234")

result = readout(jira, issue.fields) #, ['parent', 'key', 'issuetype'])
log.logger.info("%s", result)
df = pd.DataFrame()
for name in result:
    df[name] = ""+result[name]
log.logger.info("%s", df.head())
