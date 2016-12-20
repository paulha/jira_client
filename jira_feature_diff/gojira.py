from jira.client import JIRA
import yaml

# TODO: do this properly
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


CONFIG_FILE = 'config.yaml'


# set up jira connection
def init_jira():
    """Load Configuration"""
    # Read File
    try:
        stream = open(CONFIG_FILE, 'r')
        config = yaml.load(stream)
    except:
        print "Cannot load configuration file."
        exit(0)

    # Check Options
    try:
        config['connection']['server']
        config['user']['username']
        config['user']['password']
    except:
        print "Cannot load configuration options."
        exit(0)

    # Connect to JIRA
    try:
        auth = (config['user']['username'], config['user']['password'])
        jira = JIRA(config['connection'], basic_auth=auth)
    except Exception as e:
        print e
        print "Failed to connect to JIRA."
        exit(0)

    return jira

def jql_issue_gen(query, jira, show_status=False):
    if not query:
        raise Exception('no query provided')

    if show_status:
        print "JQL:", query

    seen = 0
    startAt = 0
    total = None
    while 1:
        issues = jira.search_issues(query, startAt=startAt)

        if len(issues) == 0:
            if show_status:
                print "loaded all %d issues"%total
            break

        if total is None:
            total = issues.total
        elif total != issues.total:
            raise Exception('Total changed while running %d != %d'%(total, issues.total))

        for i in issues:
            yield i

        seen += len(issues)
        if show_status:
            print "loaded %d issues starting at %d, %d/%d"%(len(issues), startAt, seen, total)
        startAt += len(issues)
