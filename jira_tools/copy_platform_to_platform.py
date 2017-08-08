from jira_class import Jira

def strip_non_ascii(string):
    """Returns the string without non ASCII characters, L & R trim of spaces"""
    stripped = (c for c in string if ord(c) < 128 and c >=' ' and c<='~')
    return ''.join(stripped).strip(" \t\n\r").replace("  ", " ")

def remove_version_and_platform(text):
    """Remove the leading version and platform name"""
    return text.replace("\[.*\]\[.*\]\s", "")

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

def get_item(jira, item):
    key = getattr(item.fields, 'parent').key
    query = "key='%s'"%key
    parent = [i for i in jira.do_query(query)]
    return parent[0] if len(parent) > 0 else None

def copy_platform_to_platform(parser, scenario, config, queries, search, log=None):
    """
    """

    preq_source_query = get_query('preq_source_query', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    areq_source_e_feature_query = get_query('areq_source_e_feature', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    # areq_source_features_query = get_query('areq_source_features', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    all_areq_source_features_query = get_query('all_areq_source_features', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    areq_target_e_feature_query = get_query('areq_target_e_feature', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    areq_target_features_query = get_query('areq_target_features', queries, copy_platform_to_platform.__name__, params=scenario, log=log)

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

    # -- The Jira records
    # -- Read the PREQs to copy to the target project
    preq_source = [feature for feature in jira.do_query(preq_source_query)]
    log.logger.info("Found %s PREQ entries", len(preq_source))

    # -- Be able to look up any existing PREQs for the target project
    # existing_target_preqs = {strip_non_ascii(getattr(e_feature.fields, 'summary')):
    #                         {'matched': False, 'data': e_feature} for e_feature in jira.do_query(target_preq_query)}

    # -- Read the E-Features to copy to the target project
    areq_source_e_feature = [feature for feature in jira.do_query(areq_source_e_feature_query)]
    log.logger.info("Found %s AREQ E-Features entries", len(areq_source_e_feature))

    # -- Get the parent Feature for each E-feature:
    #   This runs quite slowly... It would be faster to load all possible candidates and reference
    #   them as needed... Unfortunately, the data is not very orderly. You'd have to read *all*
    #   Features to guarantee that you have one in the lookup. For now, stay with the slow but
    #   sure way...
    #
    areq_source_features = {getattr(e_feature.fields, 'parent').key: get_item(jira, e_feature)
                            for e_feature in areq_source_e_feature}
    log.logger.info("Found %s AREQ Features entries", len(areq_source_features))


    # all_areq_source_features = {item.key: item for item in jira.do_query(all_areq_source_features_query)}
    # log.logger.info("In Dictionary, have %s AREQ Features entries (ALL)", len(all_areq_source_features))

    # -- Be able to look up any existing E-Features for the target project
    # existing_target_e_features = {strip_non_ascii(getattr(e_feature.fields, 'summary')):
    #                              {'matched': False, 'data': e_feature} for e_feature in jira.do_query(target_e_feature_query)}

    # -- todo: Get any existing target features to look up by summary
    existing_target_e_features = {strip_non_ascii(remove_version_and_platform(getattr(e_feature.fields, 'summary'))):
                                       e_feature for e_feature in jira.do_query(areq_target_e_feature_query)}
    log.logger.info("Found %s existing AREQ E-Features", len(existing_target_e_features))

    # -- This can be really big, as it isnt' qualified by either platform or version!
    existing_target_features = {strip_non_ascii(remove_version_and_platform(getattr(feature.fields, 'summary'))):
                                feature for feature in jira.do_query(areq_target_features_query)}
    log.logger.info("Found %s existing AREQ Features", len(existing_target_features))

    # -- Copy input preqs to target:
    for preq in preq_source:
        # # -- Remove old version and platform, prepend new version and platform
        # #target_summary = remove_version_and_platform(preq)
        # log.logger.debug("Handle %s", preq.key)
        # if target_summary in existing_target_preqs:
        #     # -- handle "This preq already exists"
        #     pass
        # else:
        #     # -- Create a new PREQ, maybe add it to the existing targets, for completeness?
        #     pass
        # # -- Read the created preq to validate it?
        pass

    # -- copy e-features to output
    for e_feature in areq_source_e_feature:
        # -- The parent for this one should already be in source_features
        lookup = getattr(e_feature.fields, 'parent').key
        try:
            source_feature = areq_source_features[lookup]
        except:
            source_feature = None   # This should never happen!
            log.logger.warning("Could not find parent %s of E-Feature %s, looked for '%s'. continuing", e_feature.fields.parent.key, e_feature.key, lookup)
            continue

        # -- Note: Well, if we couldn't find the parent, we can't do this:
        target_summary = strip_non_ascii(remove_version_and_platform(getattr(source_feature.fields,'summary')))
        if target_summary in existing_target_features:
            # -- The feature already exists on the target.
            target_feature = existing_target_features[target_summary]
            log.logger.info("This feature already exists %s", target_summary)
        else:
            # -- Create a new target feature
            log.logger.info("Create a new feature before creating E-Feature %s", target_summary)
            # target_feature = create_target_feature(jira, target_summary, source_feature)

        # -- Check to make sure the target e-feature did not already exist...
        target_summary = strip_non_ascii(remove_version_and_platform(getattr(e_feature.fields, 'summary')))
        if target_summary in existing_target_e_features:
            # -- Handle (do nothing?)
            log.logger.info("This E-Feature already exists %s", existing_target_e_features[target_summary].key)
            pass
        else:
            # https://community.atlassian.com/t5/JIRA-questions/How-to-create-subtasks-with-jira-python/qaq-p/227017
            # jira.jira_client.create_issue()
            log.logger.info("Create a new E-Feature under %s", target_feature.key)
            # create the e-feature

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


