import re
from utility_funcs.search import get_server_info
from gojira import init_jira, jql_issue_gen
from jirafields import make_field_lookup


def get_query(query_name, queries, group_name, params=None, log=None):
    if group_name not in queries:
        log.logger.fatal("Query section for %s is missing: %s", group_name, queries)
        exit(-1)

    query_set_name = group_name
    if params is not None and 'query_set' in params and params['query_set'] is not None:
        query_set_name = params['query_set']

    if query_set_name not in queries:
        log.logger.fatal("Query Set '%s' cannot be found in available queries '%s'",
                         query_set_name, queries)
        exit(-1)
    items = queries[query_set_name]

    # -- Make sure search query is defined
    if query_name not in items:
        log.logger.fatal("Search query for %s.search is missing: %s", query_name, queries)
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

    def get_field_name(self, name):
        return self.jira_field_lookup.reverse(name)

    def do_query(self, query, quiet=False):
        if not quiet:
            self.log.info("Reading from the Jira server %s using query '%s'", self.jira_config['host'], query)
        return jql_issue_gen(query, self.jira_client)

    def get_item(self, item=None, key=None, preq_summary=None, areq_summary=None, log=None):
        expected = None
        if item is not None:
            key = getattr(item.fields, 'parent').key
            query = "key='%s'" % key
        elif key is not None:
            query = "key='%s'" % key
        elif preq_summary is not None:
            query = 'project=PREQ AND summary ~ "%s"' % Jira.escape_chars(Jira.remove_version_and_platform(Jira.strip_non_ascii(preq_summary)))
            expected = preq_summary
        elif areq_summary is not None:
            query = 'project=AREQ AND summary ~ "%s"' % Jira.escape_chars(Jira.remove_version_and_platform(Jira.strip_non_ascii(areq_summary)))
            expected = areq_summary
        else:
            raise ValueError("Nothing to search for")

        # -- TODO: Ah! Just because it finds *something* doesn't mean it's a proper match...
        if log is not None:
            log.logger.debug("self.do_query('%s', quiet=True)", query)
        try:
            results = [i for i in self.do_query(query, quiet=True)]
        except Exception as e:
            if log is not None:
                log.logger.warning("Exception from do_query(): %s", e)

        if log is not None:
            log.logger.debug("Result of do_query() are %s", results)
        for result in results:
            log.logger.debug("Found %s: %s",
                             result.key if result is not None else None,
                             result.fields.summary if result is not None else None)
            if expected is None:
                return result
            else:
                if re.sub(r"] \[", "][", Jira.strip_non_ascii(result.fields.summary)) == Jira.strip_non_ascii(expected):
                    log.logger.debug("Found match: %s: %s", result.key, result.fields.summary)
                    return result
        return None

    def create_ucis(self, summary, source_feature, scenario, log=None):
        """Create UCIS from source"""

        # -- FIXME: NEED TO COPY GLOBAL ID TO MAINTAIN TRACEABILITY

        # Utility function for copying *_on fields (see below)
        def _define_update(update_list, field, entry):
            update_list[field] = [{'value': x.value} for x in getattr(entry.fields, field)] \
                if getattr(entry.fields, field) is not None else []

        and_vers_key = self.get_field_name('Android Version(s)')
        platprog_key = self.get_field_name('Platform/Program')
        exists_on = self.get_field_name('Exists On')
        verified_on = self.get_field_name('Verified On')
        failed_on = self.get_field_name('Failed On')
        blocked_on = self.get_field_name('Blocked On')
        tested_on = self.get_field_name('Tested On')
        classification = self.get_field_name('Classification')
        global_id = self.get_field_name('Global ID')

        # -- Creating an E-Feature (sub-type of Feature) causes appropriate fields of the parent Feature
        #    to be copied into the E-Feature *automatically*.
        new_e_feature_dict = {  # TODO: getattrib()!
            'project': {'key': source_feature.fields.project.key},
            'summary': summary,
            'description': source_feature.fields.description,
            'issuetype': {'name': 'UCIS'},
            # 'assignee': {'name': target_assign},
            and_vers_key: [{'value': scenario['tversion']}],
            platprog_key: [{'value': scenario['tplatform']}],
            exists_on: [{'value': scenario['exists_on']}]
        }

        # -- Having created the issue, now other fields of the E-Feature can be updated:
        update_fields = {
            # -- This field does not exist in AREQ!
            # global_id: getattr(source_feature.fields, global_id),
            'priority': {'name': 'P1-Stopper'},
            'labels': [x for x in getattr(source_feature.fields, 'labels')],
            'components': [{'id': x.id} for x in getattr(source_feature.fields, 'components')],
            classification: [{'id': x.id} for x in getattr(source_feature.fields, classification)]
        }
        # _define_update(update_fields, exists_on, source_feature)
        _define_update(update_fields, verified_on, source_feature)
        _define_update(update_fields, failed_on, source_feature)
        _define_update(update_fields, blocked_on, source_feature)
        _define_update(update_fields, tested_on, source_feature)

        log.logger.debug("Creating UCIS clone of UCIS %s -- %s" % (source_feature.key, new_e_feature_dict))

        # return None

        # -- Create the e-feature and update the stuff you can't set directly
        created_ucis = self.jira_client.create_issue(fields=new_e_feature_dict)
        created_ucis.update(notify=False, fields=update_fields)

        # -- Add a comment noting the creation of this feature.
        self.jira_client.add_comment(created_ucis,
                                     """This UCIS was created by {command}.

                                     Source UCIS in Jira is %s.
                                     Source Platform: '{splatform}' Version '{sversion}'

                                     %s""".format_map(scenario)
                                     % (source_feature.key,
                                        scenario['comment'] if scenario['comment'] is not None else ""))
        return created_ucis

    def clone_e_feature_from_e_feature(self, summary, parent_feature, sibling_feature, scenario, log=None):
        """Create e-feature from parent, overlaying sibling data if present"""

        # -- FIXME: NEED TO COPY GLOBAL ID TO MAINTAIN TRACEABILITY

        # Utility function for copying *_on fields (see below)
        def _define_update(update_list, field, entry):
            update_list[field] = [{'value': x.value} for x in getattr(entry.fields, field)] \
                if getattr(entry.fields, field) is not None else []

        and_vers_key = self.get_field_name('Android Version(s)')
        platprog_key = self.get_field_name('Platform/Program')
        exists_on = self.get_field_name('Exists On')
        verified_on = self.get_field_name('Verified On')
        failed_on = self.get_field_name('Failed On')
        blocked_on = self.get_field_name('Blocked On')
        tested_on = self.get_field_name('Tested On')
        classification = self.get_field_name('Classification')
        validation_lead = self.get_field_name('Validation Lead')
        global_id = self.get_field_name('Global ID')

        # -- Creating an E-Feature (sub-type of Feature) causes appropriate fields of the parent Feature
        #    to be copied into the E-Feature *automatically*.
        if True:
            pass

        val_lead = getattr(sibling_feature.fields, validation_lead)
        new_e_feature_dict = {
            'project': {
                'key': sibling_feature.fields.project.key if sibling_feature is not None else parent_feature.fields.project.key},
            'parent':  {'key': parent_feature.key},
            'summary': summary,
            'issuetype': {'name': 'E-Feature'},
            and_vers_key: [{'value': scenario['tversion']}],
            platprog_key: [{'value': scenario['tplatform']}],
            'assignee': {'name': sibling_feature.fields.assignee.name},
            validation_lead: {'name': val_lead.name if val_lead is not None else "" }
        }

        if 'exists_on' in scenario:
            new_e_feature_dict['exists_on'] = [{'value': scenario['exists_on']}]

        # -- Having created the issue, now other fields of the E-Feature can be updated:
        update_fields = {
            # -- This field does not exist in AREQ!
            # global_id: getattr(sibling_feature.fields, global_id),
            'summary': summary,
            'priority': {'name': sibling_feature.fields.priority.name if sibling_feature is not None else 'P1-Stopper'},
            'labels': [x for x in getattr(parent_feature.fields, 'labels')],
        }
        _define_update(update_fields, verified_on, sibling_feature if sibling_feature is not None else parent_feature)
        _define_update(update_fields, failed_on, sibling_feature if sibling_feature is not None else parent_feature)
        _define_update(update_fields, blocked_on, sibling_feature if sibling_feature is not None else parent_feature)
        _define_update(update_fields, tested_on, sibling_feature if sibling_feature is not None else parent_feature)

        log.logger.debug("Creating E-Feature clone of Feature %s -- %s" % (parent_feature.key, new_e_feature_dict))

        # return None

        # -- Create the e-feature and update the stuff you can't set directly
        created_e_feature = self.jira_client.create_issue(fields=new_e_feature_dict)
        created_e_feature.update(notify=False, fields=update_fields)

        # -- Add a comment noting the creation of this feature.
        self.jira_client.add_comment(created_e_feature,
                                     """This E-Feature was created by {command}.

                                     Parent Feature is %s. Source sibling is %s
                                     Source Platform: '{splatform}' Version '{sversion}'

                                     %s""".format_map(scenario)
                                     % (parent_feature.key, sibling_feature.key if sibling_feature is not None else "",
                                        scenario['comment'] if scenario['comment'] is not None else ""))
        return created_e_feature

    def clone_e_feature_from_parent(self, summary, parent_feature, scenario, log=None, sibling=None):
        """Create e-feature from parent, overlaying sibling data if present"""

        # -- FIXME: NEED TO COPY GLOBAL ID TO MAINTAIN TRACEABILITY

        # Utility function for copying *_on fields (see below)
        def _define_update(update_list, field, entry):
            update_list[field] = [{'value': x.value} for x in getattr(entry.fields, field)] \
                if getattr(entry.fields, field) is not None else []

        and_vers_key = self.get_field_name('Android Version(s)')
        platprog_key = self.get_field_name('Platform/Program')
        exists_on = self.get_field_name('Exists On')
        verified_on = self.get_field_name('Verified On')
        failed_on = self.get_field_name('Failed On')
        blocked_on = self.get_field_name('Blocked On')
        tested_on = self.get_field_name('Tested On')
        classification = self.get_field_name('Classification')
        global_id = self.get_field_name('Global ID')

        # -- Creating an E-Feature (sub-type of Feature) causes appropriate fields of the parent Feature
        #    to be copied into the E-Feature *automatically*.
        new_e_feature_dict = {
            'project': {
                'key': sibling.fields.project.key if sibling is not None else parent_feature.fields.project.key},
            'parent': {'key': parent_feature.key},
            'summary': summary,
            'issuetype': {'name': 'E-Feature'},
            and_vers_key: [{'value': scenario['tversion']}],
            platprog_key: [{'value': scenario['tplatform']}],
        }

        if 'exists_on' in scenario:
            new_e_feature_dict['exists_on'] = [{'value': scenario['exists_on']}]

        # -- Having created the issue, now other fields of the E-Feature can be updated:
        update_fields = {
            # -- This field does not exist in AREQ!
            # global_id: getattr(parent_feature.fields, global_id),
            'summary': summary,
            'priority': {'name': 'P1-Stopper'},
            'labels': [x for x in getattr(parent_feature.fields, 'labels')],
        }
        _define_update(update_fields, verified_on, sibling if sibling is not None else parent_feature)
        _define_update(update_fields, failed_on, sibling if sibling is not None else parent_feature)
        _define_update(update_fields, blocked_on, sibling if sibling is not None else parent_feature)
        _define_update(update_fields, tested_on, sibling if sibling is not None else parent_feature)

        log.logger.debug("Creating E-Feature clone of Feature %s -- %s" % (parent_feature.key, new_e_feature_dict))

        # return None

        # -- Create the e-feature and update the stuff you can't set directly
        created_e_feature = self.jira_client.create_issue(fields=new_e_feature_dict)
        created_e_feature.update(notify=False, fields=update_fields)

        # -- Add a comment noting the creation of this feature.
        self.jira_client.add_comment(created_e_feature,
                                     """This E-Feature was created by {command}.

                                     Parent Feature is %s. Source sibling is %s
                                     Source Platform: '{splatform}' Version '{sversion}'

                                     %s""".format_map(scenario)
                                     % (parent_feature.key, sibling.key if sibling is not None else "",
                                        scenario['comment'] if scenario['comment'] is not None else ""))
        return created_e_feature

    # -- Static utility functions...
    @staticmethod
    def escape_chars(text: str):
        """Escape special characters in Jira search:

        Characters "[ ] + - & | ! ( ) { } ^ ~ * ? \ :" are special in jira searches
        """
        if True:
            # -- Some characters need a single "\" in front of them
            text = re.sub(r"([\'\"])", "\\\\\\1", text)
            # -- Others need two...
            result = re.sub(r"([\[\]+\-&|!(){\}^~*?\\:\'\"])", "\\\\\\\\\\1", text)
        else:
            result = re.sub(r"([\[\]+\-&|!(){\}^~*?\\:\'\"])", "\\\\\\\\\\1", text)
        return result
        # return re.sub(r"([\[\]+\-&|!(){\}^~*?\\:\'\"])", "\\\\\\\\\\1", text)

    @staticmethod
    def strip_non_ascii(_str):
        """Returns the string without non ASCII characters, L & R trim of spaces"""
        stripped = (c for c in _str if ord(c) < 127 and c >= ' ' and c <= '~')
        return ''.join(stripped).strip(" \t\n\r").replace("  ", " ")

    @staticmethod
    def remove_version_and_platform(txt):
        """Remove the leading version and platform name"""
        return re.sub(r"^(\[[^\]]*\])?\s*(\[[^\]]*\])?\s*(\[[^\]]*\]?)?\s*", "", txt)

    def create_issue_link(self, type, inwardIssue, outwardIssue, comment=None):
        return self.jira_client.create_issue_link(type, inwardIssue, outwardIssue, comment)