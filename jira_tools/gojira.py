from jira.client import JIRA
import itertools
import yaml
import logger as log

CONFIG_FILE = 'config.yaml'


def chunker(iterable, n, fillvalue=None):
    "Return n at a time, no padding at end of list"
    
    # only need 2n items to cause x/n to cycle between 0 & 1,
    # marking a group
    r = range(n*2)
    rc = itertools.cycle(r)
    l = lambda x: rc.next() / n

    # ...and then strip off the group label
    return (i[1] for i in itertools.groupby(iterable, l))


# set up jira connection
def init_jira():
    """Load Configuration"""
    # Read File
    try:
        stream = open(CONFIG_FILE, 'r')
        config = yaml.load(stream)
    except:
        log.logger.info( "Cannot load configuration file." )
        exit(0)

    # Check Options
    try:
        config['connection']['server']
        config['user']['username']
        config['user']['password']
    except:
        log.logger.info( "Cannot load configuration options." )
        exit(0)

    if config['connection']['verify'] is False:
        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # Connect to JIRA
    try:
        auth = (config['user']['username'], config['user']['password'])
        jira = JIRA(config['connection'], basic_auth=auth)
    except Exception as e:
        log.logger.info( e )
        log.logger.info( "Failed to connect to JIRA." )
        exit(0)

    return jira


# TODO: add a no_increment_start option to handle queries that reduce the
#       count of the result set
def jql_issue_gen(query, jira, show_status=False, count_change_ok=False):
    if not query:
        raise Exception('no query provided')

    if show_status:
        log.logger.info( "JQL:", query )

    seen = 0
    startAt = 0
    total = None
    while 1:
        issues = jira.search_issues(query, startAt=startAt)

        if len(issues) == 0:
            if show_status:
                log.logger.info( "loaded all %d issues"%total )
            break

        if total is None:
            total = issues.total
        elif total != issues.total and not count_change_ok:
            raise Exception('Total changed while running %d != %d'%(total, issues.total))

        for i in issues:
            yield i

        seen += len(issues)
        if show_status:
            log.logger.info( "loaded %d issues starting at %d, %d/%d"%(len(issues), startAt, seen, total) )
        startAt += len(issues)


def issue_keys_issue_gen(issue_key_list, jira, show_status=False, group_len=20):
    if not issue_key_list:
        raise Exception('no issues provided')

    jql = "key in ( {} )"

    key_groups = chunker(issue_key_list, group_len)
    jqls = (jql.format(" , ".join(key_group)) for key_group in key_groups)

    jql_gens = (jql_issue_gen(j, jira, show_staus=show_status) for j in jqls)
    return itertools.chain.from_iterable(jql_gens)
