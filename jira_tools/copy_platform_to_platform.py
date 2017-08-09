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

def copy_platform_to_platform(parser, scenario, config, queries, search, log=None):
    """
    """

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

    features_scanned = 0
    warnings_issued = 0
    verify_failures = 0
    update_failures = 0
    processing_errors = 0

    # -- Copy source preqs to target:
    # (Get the list of already existing PREQs for this platform and version!)
    for preq in jira.do_query(preq_source_query):
        # # -- Remove old version and platform, prepend new version and platform
        log.logger.info("Search for: '%s'", preq.fields.summary)
        target_summary = remove_version_and_platform(preq.fields.summary)
        target_summary = target_summary_format % target_summary
        existing_preq = get_item(jira, preq_summary=escape_chars(target_summary))
        if existing_preq is not None:
            # -- This is good, PREQ is already there so nothing to do.
            log.logger.debug("Found existing PREQ: '%s'", existing_preq.fields.summary)
            pass
        else:
            # -- This PREQ is missing, so use preq as template to create a new UCIS for the platform:
            log.logger.info("Need to create new PREQ for: '%s'", target_summary)
            if update:
                log.logger.info("Creating a new PREQ for %s", target_summary)
            else:
                log.logger.info("PREQ is missing for: '%s'", target_summary)
                # -- Create a new UCIS(!) PREQ
        pass

    # -- copy source e-features to output
    for e_feature in jira.do_query(areq_source_e_feature_query):
        # -- The parent for this one should already be in source_features
        lookup = e_feature.fields.parent.key
        try:
            source_feature = get_item(jira, key=lookup)
        except Exception as e:
            source_feature = None   # This should never happen!
            log.logger.fatal("%s: Could not find parent %s of E-Feature %s, looked for '%s'. continuing", e, e_feature.fields.parent.key, e_feature.key, lookup)
            # -- Note: Well, if we couldn't find the parent, we can't continue
            continue

        # -- Look to see if there is an existing Feature that we can attache the new E-Feature to:
        # NOTE: =============================================================
        # NOTE: Having found the parent feature above, why look it up again?
        # NOTE: Just reuse the feature we have!!!
        # NOTE: =============================================================
        target_summary = strip_non_ascii(remove_version_and_platform(getattr(source_feature.fields,'summary')))
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
        # NOTE: ========================== END +=============================

        # -- OK, at this point we can create the E-Feature record, if it's not going to be a duplicate...
        target_summary = remove_version_and_platform(e_feature.fields.summary).strip()
        target_summary = target_summary_format % target_summary
        existing_areq = get_item(jira, areq_summary=escape_chars(target_summary))

        if existing_areq is not None:
            # -- This E-Feature already exists, don't touch it!
            log.logger.debug("The targeted E-Feature already exists! %s", existing_areq.key)
            continue
        else:
            if update:
                log.logger.info("Creating a new E-Feature for Feature %s: %s", feature.key, target_summary)
            else:
                log.logger.info("E-Feature is missing for Feature %s: '%s'", feature.key, target_summary)
                # -- Create a new E-Feature(!) PREQ


    log.logger.info("-----------------------------------------------------------------")
    log.logger.info("%s source entries were considered. ", features_scanned)
    log.logger.info("%s warnings were issued. ", warnings_issued)
    log.logger.info("")

    # if verify:
    #     log.logger.info("%s E-Feature comparison failure(s). ", verify_failures)
    #
    # if update:
    #     log.logger.info("%s new E-Feature(s) were created, %s update failures. ", update_count, update_failures)

    log.logger.info("%s processing error(s). ", processing_errors)


