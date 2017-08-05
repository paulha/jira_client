from otc_tool import init_jira, jql_issue_gen, make_field_lookup

class Jira:

    def __init__(self, server_alias, config_path, log=log.logging.getLogger("root")):
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

    def get_field_name(self, name):
        return self.jira_field_lookup.reverse(name)

    def do_query(self, query):
        self.log.info("Reading E-Features from the Jira server %s using query '%s'", JIRA_SERVER, query)
        return jql_issue_gen(query, self.jira_client)


