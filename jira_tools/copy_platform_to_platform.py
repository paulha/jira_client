from jira_class import Jira, strip_non_ascii, remove_version_and_platform, escape_chars, get_query
import re

# def strip_non_ascii(string):
#     """Returns the string without non ASCII characters, L & R trim of spaces"""
#     stripped = (c for c in string if ord(c) < 128 and c >=' ' and c<='~')
#     return ''.join(stripped).strip(" \t\n\r").replace("  ", " ")
#
# def remove_version_and_platform(text):
#     """Remove the leading version and platform name"""
#     return re.sub(r"\[.*\]\[.*\]\s", "", text)
#
# def escape_chars(text):
#     return re.sub(r"([:\[\]-])", "\\\\\\\\\\1", text)
#
# def get_query(query_name, queries, group_name, params=None, log=None):
#     if group_name not in queries:
#         log.logger.fatal( "Query section for %s is missing: %s", group_name, queries)
#         exit(-1)
#
#     items=queries[group_name]
#     # -- Make sure search query is defined
#     if query_name not in items:
#         log.logger.fatal( "Search query for %s.search is missing: %s", query_name, queries)
#         exit(-1)
#
#     query = items[query_name]
#     if params is not None:
#         query = query.format_map(params)
#     return query

def get_item(jira, item=None, key=None, preq_summary=None, areq_summary=None, log=None):
    expected = None
    if item is not None:
        key = getattr(item.fields, 'parent').key
        query = "key='%s'"%key
    elif key is not None:
        query = "key='%s'" % key
    elif preq_summary is not None:
        query = 'project=PREQ AND summary ~ "%s"' % escape_chars(preq_summary)
        expected = preq_summary
    elif areq_summary is not None:
        query = 'project=AREQ AND summary ~ "%s"' % escape_chars(areq_summary)
        expected = areq_summary
    else:
        raise ValueError("Nothing to search for")

    # -- TODO: Ah! Just because it finds *something* doesn't mean it's a proper match...
    results = [i for i in jira.do_query(query, quiet=True)]
    for result in results:
        if expected is None:
            return result
        else:
            if strip_non_ascii(result.fields.summary).upper() == strip_non_ascii(expected).upper():
                return result
    return None

def create_ucis(jira, summary, source_feature, scenario, log=None):
    """Create UCIS from source"""

    # Utility function for copying *_on fields (see below)
    def _define_update(update_list, field, entry):
        update_list[field] = [{'value': x.value} for x in getattr(entry.fields, field)] \
            if getattr(entry.fields, field) is not None else []

    and_vers_key = jira.get_field_name('Android Version(s)')
    platprog_key = jira.get_field_name('Platform/Program')
    exists_on = jira.get_field_name('Exists On')
    verified_on = jira.get_field_name('Verified On')
    failed_on = jira.get_field_name('Failed On')
    blocked_on = jira.get_field_name('Blocked On')
    tested_on = jira.get_field_name('Tested On')
    classification = jira.get_field_name('Classification')

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
        exists_on:    [{'value': scenario['exists_on']}]
    }

    # -- Having created the issue, now other fields of the E-Feature can be updated:
    update_fields = {
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
    created_ucis = jira.jira_client.create_issue(fields=new_e_feature_dict)
    created_ucis.update(notify=False, fields=update_fields)

    # -- Add a comment noting the creation of this feature.
    jira.jira_client.add_comment(created_ucis,
                                 """This UCIS was created by {command}.
            
                                 Source UCIS in Jira is %s.
                                 Source Platform: '{splatform}' Version '{sversion}'
            
                                 %s""".format_map(scenario)
                                 % (source_feature.key,
                                    scenario['comment'] if scenario['comment'] is not None else ""))
    return created_ucis


def clone_e_feature_from_parent(jira, summary, parent_feature, scenario, log=None, sibling=None):
    """Create e-feature from parent, overlaying sibling data if present"""

    # Utility function for copying *_on fields (see below)
    def _define_update(update_list, field, entry):
        update_list[field] = [{'value': x.value} for x in getattr(entry.fields, field)] \
            if getattr(entry.fields, field) is not None else []

    and_vers_key = jira.get_field_name('Android Version(s)')
    platprog_key = jira.get_field_name('Platform/Program')
    exists_on = jira.get_field_name('Exists On')
    verified_on = jira.get_field_name('Verified On')
    failed_on = jira.get_field_name('Failed On')
    blocked_on = jira.get_field_name('Blocked On')
    tested_on = jira.get_field_name('Tested On')
    classification = jira.get_field_name('Classification')

    # -- Creating an E-Feature (sub-type of Feature) causes appropriate fields of the parent Feature
    #    to be copied into the E-Feature *automatically*.
    new_e_feature_dict = {  # TODO: getattrib()!
        'project': {'key': sibling.fields.project.key if sibling is not None else parent_feature.fields.project.key},
        'parent': {'key': parent_feature.key},
        'summary': summary,
        'issuetype': {'name': 'E-Feature'},
        and_vers_key: [{'value': scenario['tversion']}],
        platprog_key: [{'value': scenario['tplatform']}],
        exists_on: [{'value': scenario['exists_on']}]
    }

    # -- Having created the issue, now other fields of the E-Feature can be updated:
    update_fields = {
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
    created_e_feature = jira.jira_client.create_issue(fields=new_e_feature_dict)
    created_e_feature.update(notify=False, fields=update_fields)

    # -- Add a comment noting the creation of this feature.
    jira.jira_client.add_comment(created_e_feature,
                                 """This E-Feature was created by {command}.
                
                                 Parent Feature is %s. Source sibling is %s
                                 Source Platform: '{splatform}' Version '{sversion}'
                
                                 %s""".format_map(scenario)
                                 % (parent_feature.key, sibling.key if sibling is not None else "",
                                    scenario['comment'] if scenario['comment'] is not None else ""))
    return created_e_feature


def copy_platform_to_platform(parser, scenario, config, queries, search, log=None):
    """Copy platform to platform, based on the UCIS and E-Feature entries of the source platform"""

    preq_source_query = get_query('preq_source_query', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    preq_target_query = get_query('preq_target_query', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    areq_source_e_feature_query = get_query('areq_source_e_feature', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    areq_target_e_feature_query = get_query('areq_target_e_feature', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    target_feature_query = get_query('target_feature_query', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    target_summary_format = get_query('target_summary_format', queries, copy_platform_to_platform.__name__, params=scenario, log=log)

    log.logger.info("Examining source platform {splatform}, source android version {sversion}, target android version {tversion}".format_map(scenario))

    verify = scenario['verify']
    update = scenario['update']
    log.logger.info("Verify is %s and Update is %s", verify, update)
    log.logger.info("=================================================================")

    # -- Get and format it:
    jira = Jira(scenario['name'], search, log=log.logger)

    source_preq_scanned = 0
    source_areq_scanned = 0
    ucis_created = 0
    e_features_created = 0
    warnings_issued = 0
    verify_failures = 0
    update_failures = 0
    processing_errors = 0

    update_count = 0

    def compare_items(item_kind, source_query, target_query, log=None):
        def read_items(query, log=None):
            """Read items into summary based dictionary, warning on duplicates"""
            dictionary = {}
            for item in jira.do_query(query):
                item_key = remove_version_and_platform(strip_non_ascii(item.fields.summary)).upper()
                if item_key not in dictionary:
                    dictionary[item_key] = item
                else:
                    log.logger.warning("Item %s key '%s' creates a duplicate entry with %s", item.key, item_key, dictionary[item_key])
            return dictionary

        source = read_items(source_query, log)
        log.logger.info( "Source has %d items in dictionary", len(source))
        target = read_items(target_query, log)
        log.logger.info( "Target has %d items in dictionary", len(target))

        # -- Everything in source should be copied to target:
        for key, value in source.items():
            item_key = remove_version_and_platform(strip_non_ascii(key)).upper()
            if item_key not in target:
                log.logger.error("Could not find source %s %s in target: %s", item_kind, value.key, key)

        # -- Target should not have stuff in it that's not from the source!:
        for key, value in target.items():
            item_key = remove_version_and_platform(strip_non_ascii(key)).upper()
            if item_key not in source:
                log.logger.error("%s %s in target was not in original source: %s", item_kind, value.key, key)

        return

    # -- Copy source preqs to target:
    # (Get the list of already existing PREQs for this platform and version!)
    if True:
        for source_preq in jira.do_query(preq_source_query):
            # # -- Remove old version and platform, prepend new version and platform
            source_preq_scanned += 1
            log.logger.debug("Search for: '%s'", source_preq.fields.summary)
            target_summary = remove_version_and_platform(source_preq.fields.summary)
            target_summary = target_summary_format % target_summary
            existing_preq = get_item(jira, preq_summary=target_summary)
            if existing_preq is not None:
                # -- This is good, PREQ is already there so nothing to do.
                log.logger.info("Found existing UCIS: %s '%s'", existing_preq.key, existing_preq.fields.summary)
                pass
            else:
                # -- This PREQ is missing, so use preq as template to create a new UCIS for the platform:
                log.logger.debug("Need to create new UCIS for: '%s'", target_summary)
                if update:
                    # -- Create a new UCIS(!) PREQ
                    result = create_ucis(jira, target_summary, source_preq, scenario, log)
                    log.logger.info("Created a new UCIS %s for %s", result.key, target_summary)
                    update_count += 1
                    ucis_created += 1
                else:
                    log.logger.warning("Target UCIS is missing, sourced from %s: '%s'", source_preq.key, target_summary)
                    warnings_issued += 1

            if scenario['createmax'] and update_count>=scenario['createmax']:
                break
            pass

    update_count = 0

    # -- copy source e-features to output
    for source_e_feature in jira.do_query(areq_source_e_feature_query):
        # -- The parent for this one should already be in source_features
        source_areq_scanned += 1
        lookup = source_e_feature.fields.parent.key
        try:
            parent_feature = get_item(jira, key=lookup)
        except Exception as e:
            parent_feature = None   # This should never happen!
            log.logger.fatal("%s: Could not find parent %s of E-Feature %s, looked for '%s'. continuing", e, source_e_feature.fields.parent.key, source_e_feature.key, lookup)
            # -- Note: Well, if we couldn't find the parent, we can't continue
            warnings_issued += 1
            continue

        # -- OK, at this point we can create the E-Feature record, if it's not going to be a duplicate...
        target_summary = remove_version_and_platform(source_e_feature.fields.summary).strip()
        target_summary = target_summary_format % target_summary
        existing_feature = get_item(jira, areq_summary=target_summary)

        if existing_feature is not None:
            # -- This E-Feature already exists, don't touch it!
            log.logger.info("The targeted E-Feature '%s' already exists! %s: %s",
                            target_summary, existing_feature.key, existing_feature.fields.summary)
            continue
        else:
            if update:
                log.logger.info("Creating a new E-Feature for Feature %s: %s", parent_feature.key, target_summary)
                clone_e_feature_from_parent(jira, target_summary, parent_feature, scenario, sibling=source_e_feature, log=log)
                e_features_created += 1
                update_count += 1
            else:
                log.logger.info("Target E-Feature is missing for Source E-Feature %s, Feature %s: '%s'",
                                source_e_feature.key, parent_feature.key, target_summary)
                # -- Create a new E-Feature(!) PREQ

        if scenario['createmax'] and update_count>=scenario['createmax']:
            break


    compare_items("UCIS", preq_source_query, preq_target_query, log=log)
    compare_items("E-Feature", areq_source_e_feature_query, areq_target_e_feature_query, log=log)

    log.logger.info("-----------------------------------------------------------------")
    log.logger.info("%s UCIS source entries were considered. ", source_preq_scanned)
    log.logger.info("%s target UCIS entries were created. ", ucis_created)
    log.logger.info("%s E-Feature source entries were considered. ", source_areq_scanned)
    log.logger.info("%s target E-Features entries were created. ", e_features_created)
    log.logger.info("%s warnings were issued. ", warnings_issued)
    log.logger.info("")

    # if verify:
    #     log.logger.info("%s E-Feature comparison failure(s). ", verify_failures)
    #
    # if update:
    #     log.logger.info("%s new E-Feature(s) were created, %s update failures. ", update_count, update_failures)

    log.logger.info("%s processing error(s). ", processing_errors)


