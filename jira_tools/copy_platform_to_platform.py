from jira_class import Jira
import re

def strip_non_ascii(string):
    """Returns the string without non ASCII characters, L & R trim of spaces"""
    stripped = (c for c in string if ord(c) < 128 and c >=' ' and c<='~')
    return ''.join(stripped).strip(" \t\n\r").replace("  ", " ")

def remove_version_and_platform(text):
    """Remove the leading version and platform name"""
    return re.sub(r"\[.*\]\[.*\]\s", "", text)

def escape_chars(text):
    return re.sub(r"([\[\]-])", "\\\\\\\\\\1", text)

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

def get_item(jira, item=None, key=None, preq_summary=None, areq_summary=None):
    if item is not None:
        key = getattr(item.fields, 'parent').key
        query = "key='%s'"%key
    elif key is not None:
        query = "key='%s'" % key
    elif preq_summary is not None:
        query = 'project=PREQ AND summary ~ "%s"' % preq_summary
    elif areq_summary is not None:
        query = 'project=AREQ AND summary ~ "%s"' % areq_summary
    else:
        raise ValueError("Nothing to search for")

    parent = [i for i in jira.do_query(query, quiet=True)]
    return parent[0] if len(parent) > 0 else None

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
    areq_source_e_feature_query = get_query('areq_source_e_feature', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
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

    # -- Let's see if we can find some PREQ duplicates...
    table = {}
    for item in jira.do_query(preq_source_query):
        key = strip_non_ascii(remove_version_and_platform(item.fields.summary))
        if key in table:
            table[key].append(item)
        else:
            table[key] = []
            table[key].append(item)
    duplicates = [this_list for key, this_list in table.items()
                    if len(this_list) > 1]
    if len(duplicates) > 0:
        log.logger.warning("")
        log.logger.warning("%d PREQ duplications were found! %s", len(duplicates), duplicates)
        log.logger.warning("")
    else:
        log.logger.warning("")
        log.logger.warning("No PREQ duplicates noticed in the input set...")
        log.logger.warning("")

    # -- Let's see if we can find some duplicates...
    table = {}
    for item in jira.do_query(areq_source_e_feature_query):
        key = strip_non_ascii(remove_version_and_platform(item.fields.summary))
        if key in table:
            table[key].append(item)
        else:
            table[key] = []
            table[key].append(item)
    duplicates = [this_list for key, this_list in table.items()
                    if len(this_list) > 1]
    if len(duplicates) > 0:
        log.logger.warning("")
        log.logger.warning("%d AREQ duplications were found! %s", len(duplicates), duplicates)
        log.logger.warning("")
    else:
        log.logger.warning("")
        log.logger.warning("No AREQ duplicates noticed in the input set...")
        log.logger.warning("")

    # -- Copy source preqs to target:
    # (Get the list of already existing PREQs for this platform and version!)
    for source_preq in jira.do_query(preq_source_query):
        # # -- Remove old version and platform, prepend new version and platform
        source_preq_scanned += 1
        log.logger.debug("Search for: '%s'", source_preq.fields.summary)
        target_summary = remove_version_and_platform(source_preq.fields.summary)
        target_summary = target_summary_format % target_summary
        existing_preq = get_item(jira, preq_summary=escape_chars(target_summary))
        if existing_preq is not None:
            # -- This is good, PREQ is already there so nothing to do.
            log.logger.info("Found existing PREQ: '%s'", existing_preq.fields.summary)
            pass
        else:
            # -- This PREQ is missing, so use preq as template to create a new UCIS for the platform:
            log.logger.debug("Need to create new PREQ for: '%s'", target_summary)
            if update:
                # -- Create a new UCIS(!) PREQ
                result = create_ucis(jira, target_summary, source_preq, scenario, log)
                log.logger.info("Created a new PREQ %s for %s", result.key, target_summary)
                update_count += 1
                ucis_created += 1
            else:
                log.logger.warning("PREQ is missing for: '%s'", target_summary)
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

        if False:
            # -- Look to see if there is an existing Feature that we can attache the new E-Feature to:
            # NOTE: =============================================================
            # NOTE: Having found the parent feature above, why look it up again?
            # NOTE: Just reuse the feature we have!!!
            # NOTE: =============================================================
            target_summary = strip_non_ascii(remove_version_and_platform(getattr(parent_feature.fields, 'summary')))
            query = target_feature_query % escape_chars(target_summary)
            result = [feature for feature in jira.do_query(query, quiet=True)]

            if len(result) == 0:
                # -- No feature exists, we must create it
                log.logger.warning("No feature exists for '%s'", target_summary)

            elif len(result) == 1:
                # -- Good, exactly one possible parent!
                feature = result[0]
                log.logger.debug("Found one possible parent feature %s", feature.key)
            else:
                # -- NOT GOOD: multiple possible parent features. How to choose?
                log.logger.warning("Found multiple possible parent features: %s", [r.key for r in result])
                log.logger.warning("For summary                            : '%s'", target_summary)
                warnings_issued += 1
                result2 = [feature for feature in result
                           if feature.fields.summary.strip() == target_summary.strip()]
                if len(result2) == 1:
                    feature = result2[0]
                    log.logger.info("Continuing-- Reduced multiple %s to a single match: %s: %s",
                                    [r.key for r in result], feature.key, feature.fields.summary)
                else:
                    log.logger.fatal("Can't decide between results: %s", [r.key for r in result2])
                    # todo: If one has subtasks and the other doesn't!
                    continue
                    # NOTE: ========================== END =============================

        # -- OK, at this point we can create the E-Feature record, if it's not going to be a duplicate...
        target_summary = remove_version_and_platform(source_e_feature.fields.summary).strip()
        target_summary = target_summary_format % target_summary
        existing_feature = get_item(jira, areq_summary=escape_chars(target_summary))

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
                log.logger.info("E-Feature is missing for Feature %s: '%s'", parent_feature.key, target_summary)
                # -- Create a new E-Feature(!) PREQ

        if scenario['createmax'] and update_count>=scenario['createmax']:
            break


    log.logger.info("-----------------------------------------------------------------")
    log.logger.info("%s UCIS source entries were considered. ", source_preq_scanned)
    log.logger.info("%s target UCIS entries were created. ", ucis_created)
    log.logger.info("%s UCIS source entries were considered. ", source_areq_scanned)
    log.logger.info("%s target E-Features entries were created. ", e_features_created)
    log.logger.info("%s warnings were issued. ", warnings_issued)
    log.logger.info("")

    # if verify:
    #     log.logger.info("%s E-Feature comparison failure(s). ", verify_failures)
    #
    # if update:
    #     log.logger.info("%s new E-Feature(s) were created, %s update failures. ", update_count, update_failures)

    log.logger.info("%s processing error(s). ", processing_errors)


