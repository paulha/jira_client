import re
from gojira import init_jira, jql_issue_gen
from jirafields import make_field_lookup
from utility_funcs.search import get_server_info
def strip_non_ascii(string):
    """Returns the string without non ASCII characters, L & R trim of spaces"""
    stripped = (c for c in string if ord(c) < 128 and c >=' ' and c<='~')
    return ''.join(stripped).strip(" \t\n\r").replace("  ", " ")

def remove_version_and_platform(text):
    """Remove the leading version and platform name"""
    return re.sub(r"\[.*\]\[.*\]\s", "", text)

def escape_chars(text):
    return re.sub(r"([:\[\]-])", "\\\\\\\\\\1", text)

def get_query(query_name, queries, group_name, params=None, log=None):
    if group_name not in queries:
        log.logger.fatal( "Query section for %s is missing: %s", group_name, queries)
        exit(-1)

    items=queries[group_name]
    # -- Make sure search query is defined
    if query_name not in items:
        log.logger.fatal( "Search query for %s.search is missing: %s", query_name, queries)
        exit(-1)

    query = items[query_name]
    if params is not None:
        query = query.format_map(params)
    return query


class Jira:

    # def __init__(self, server_alias, config_path, log=logging.getLogger("root")):
    def __init__(self, server_alias, config_path, log=None):

        self.server_alias = server_alias
        self.log = log

        # -- Get JIRA login configuration and authentication info
        try:
            self.jira_config = get_server_info(server_alias, config_path)  # possible FileNotFoundError
        except FileNotFoundError as f:
            self.log.fatal("Can't open JIRA authentication configuration file: %s" % f)
            raise FileNotFoundError("Can't find Jira configuration file", config_path)

        self.log.info("Using JIRA server %s, '%s'", server_alias, self.jira_config['host'])
        self.jira_client = init_jira(self.jira_config)
        self.jira_field_lookup = make_field_lookup(self.jira_client)

    def escape_chars(text):
        """Escape special characters in Jira search:

        Characters "[ ] + - & | ! ( ) { } ^ ~ * ? \ :" are special in jira searches
        """
        return re.sub(r"([\[\]\+\-\&\|\!\(\)\{\}\^\~\*\?\\\:])", "\\\\\\\\\\1", text)

    def get_field_name(self, name):
        return self.jira_field_lookup.reverse(name)

    def do_query(self, query, quiet=False):
        if not quiet:
            self.log.info("Reading from the Jira server %s using query '%s'", self.jira_config['host'], query)
        return jql_issue_gen(query, self.jira_client)


