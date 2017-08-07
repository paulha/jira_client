from jira_class import Jira

def strip_non_ascii(string):
    """Returns the string without non ASCII characters, L & R trim of spaces"""
    stripped = (c for c in string if ord(c) < 128 and c >=' ' and c<='~')
    return ''.join(stripped).strip(" \t\n\r").replace("  ", " ")

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
    areq_source_features_query = get_query('areq_source_features', queries, copy_platform_to_platform.__name__, params=scenario, log=log)

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

    # source_preq_query = 'project = "{jproject}" AND "Platform/Program" = "{jplatform}" AND "Android Version(s)"' \
    #                     ' in ({jversion}) AND type = UCIS' \
    #                     .format_map({'jproject': project, 'jplatform': platform, 'jversion': version})
    # target_preq_query = 'project = "{jproject}" AND "Platform/Program" = "{jplatform}" AND "Android Version(s)"' \
    #                     ' in ({jversion}) AND type = UCIS' \
    #                     .format_map({'jproject': project, 'jplatform': platform, 'jversion': version})
    # source_areq_query = 'project = "{jproject}" AND "Platform/Program" = "{jplatform}" AND "Android Version(s)"' \
    #                     ' in ({jversion}) AND type = UCIS' \
    #                     .format_map({'jproject': project, 'jplatform': platform, 'jversion': version})
    # target_areq_query = 'project = "{jproject}" AND "Platform/Program" = "{jplatform}" AND "Android Version(s)"' \
    #                     ' in ({jversion}) AND type = UCIS' \
    #                     .format_map({'jproject': project, 'jplatform': platform, 'jversion': version})

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
    # TODO: This runs quite slowly... It would be faster to load all possible candidates and reference
    # TODO: them as needed!
    areq_source_features = {getattr(e_feature.fields, 'parent').key: get_item(jira, e_feature)
                       for e_feature in areq_source_e_feature}
    log.logger.info("Found %s AREQ Features entries", len(areq_source_features))

    # -- Be able to look up any existing E-Features for the target project
    # existing_target_e_featuress = {strip_non_ascii(getattr(e_feature.fields, 'summary')):
    #                               {'matched': False, 'data': e_feature} for e_feature in jira.do_query(target_e_feature_query)}

    # -- todo: Get any existing target features to look up by summary
    # existing_target_featuress = {strip_non_ascii(getattr(e_feature.fields, 'summary')):
    #                             {'matched': False, 'data': e_feature} for e_feature in jira.do_query(target_e_feature_query)}

    # -- Copy input preqs to target:
    for preq in preq_source:
        # # -- Remove old version and platform, prepend new version and platform
        # #target_summary = transform_summary(preq)
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
        try:
            source_feature = areq_source_features[getattr(e_feature.fields, 'parent').key]
        except:
            source_feature = None   # This should never happen!
            log.logger.warning("Could not find parent %s of E-Feature %s", e_feature.fields.parent.key. e_feature.key)

        target_summary = strip_non_ascii(transform_summary(source_feature))
        if target_summary in existing_target_featuress:
            # -- The feature already exists on the target.
            target_feature = existing_target_featuress[target_summary]
        else:
            # -- Create a new target feature
            target_feature = create_target_feature(jira, target_summary, source_feature)
            # -- Read the created preq to validate it?


        # -- Check to make sure the target e-feature did not already exist...
        target_summary = strip_non_ascii(transform_summary(e_feature))
        if target_summary in existing_target_e_featuress:
            # -- Handle (do nothing?)
            pass
        else:
            # https://community.atlassian.com/t5/JIRA-questions/How-to-create-subtasks-with-jira-python/qaq-p/227017
            jira.jira_client.create_issue()
        # -- Read the created preq to validate it?

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


