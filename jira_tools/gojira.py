from os.path import expanduser, pathsep
from jira.client import JIRA
import itertools
import yaml
import Logger as log

from utility_funcs.search import get_server_info

CONFIG_FILE = './config.yaml'+pathsep+'~/.jira/config.yaml'


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
    """
    Load Configuration from config.yaml
    
    Configuration may be held in either ~/.jira/config.yaml or ./config.yaml
    """
    """
    try:
        # First, try to open config file in current directory
        config_file = CONFIG_FILE
        stream = open(config_file, 'r')
    except:
        log.logger.warning( "Could not open configuration file %s."%(config_file) )
        try:
            # Check to see if it's in user's ~/.jira
            config_file = expanduser('~/.jira/' + CONFIG_FILE)
            stream = open(config_file, 'r')
        except:
            log.logger.error("Could not open configuration file %s." % (config_file))
            exit(0)

    # Read the configuration
    log.logger.info( "found config %s"%(config_file))
    try:
        config = yaml.load(stream)
    except:
        log.logger.info( "Cannot load configuration file." )
        exit(0)

    # Check Options
    try:
        if 'servers' in config:
            # Read from the servers subsection
            section = config['servers']['jira-t3']
            auth = (section['username'], section['password'])
            host = section['host']
            server = {'server': host}

            verify = None
            if 'verify' in section:
                verify = section['verify']
                server['verify'] = verify

        else:
            config['connection']['server']
            config['user']['username']
            config['user']['password']
            auth = (config['user']['username'], config['user']['password'])
            host = config['connection']['server']
            server = {'server': host}

            verify = None
            if 'verify' in config['connection']:
                verify = config['connection']['verify']
                server['verify'] = verify

    except:
        log.logger.error( "Missing configuration options.", extra=section  )
        exit(0)
    """
    config = get_server_info('jira-t3', CONFIG_FILE)    # possible FileNotFoundError
    # todo: The shifting around that's going on above needs to be done....

    verified = "verified"
    if verify is None:
        verified = "unverified"
        # -- Following code is supposed to ignore a certificate error, but it doesn't. :-(
        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # Connect to JIRA
    try:
        log.logger.info( "Connecting to %s using %s connection.", host, verified)
        jira = JIRA(server, basic_auth=auth)
    except Exception as e:
        log.logger.fatal( e, exc_info=True )
        log.logger.fatal( "Failed to connect to JIRA." )
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
