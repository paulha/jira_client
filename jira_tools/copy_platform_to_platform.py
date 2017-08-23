from jira_class import Jira, get_query


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
                item_key = Jira.remove_version_and_platform(Jira.strip_non_ascii(item.fields.summary)).upper()
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
            item_key = Jira.remove_version_and_platform(Jira.strip_non_ascii(key)).upper()
            if item_key not in target:
                log.logger.error("Could not find source %s %s in target: %s", item_kind, value.key, key)

        # -- Target should not have stuff in it that's not from the source!:
        for key, value in target.items():
            item_key = Jira.remove_version_and_platform(Jira.strip_non_ascii(key)).upper()
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
            target_summary = Jira.remove_version_and_platform(source_preq.fields.summary)
            target_summary = target_summary_format % target_summary
            existing_preq = jira.get_item(preq_summary=target_summary)
            if existing_preq is not None:
                # -- This is good, PREQ is already there so nothing to do.
                log.logger.info("Found existing UCIS: %s '%s'", existing_preq.key, existing_preq.fields.summary)
                pass
            else:
                # -- This PREQ is missing, so use preq as template to create a new UCIS for the platform:
                log.logger.debug("Need to create new UCIS for: '%s'", target_summary)
                if update:
                    # -- Create a new UCIS(!) PREQ
                    result = jira.create_ucis(target_summary, source_preq, scenario, log)
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
            parent_feature = jira.get_item(key=lookup)
        except Exception as e:
            parent_feature = None   # This should never happen!
            log.logger.fatal("%s: Could not find parent %s of E-Feature %s, looked for '%s'. continuing", e, source_e_feature.fields.parent.key, source_e_feature.key, lookup)
            # -- Note: Well, if we couldn't find the parent, we can't continue
            warnings_issued += 1
            continue

        # -- OK, at this point we can create the E-Feature record, if it's not going to be a duplicate...
        target_summary = Jira.remove_version_and_platform(source_e_feature.fields.summary).strip()
        target_summary = target_summary_format % target_summary
        existing_feature = jira.get_item(areq_summary=target_summary)

        if existing_feature is not None:
            # -- This E-Feature already exists, don't touch it!
            log.logger.info("The targeted E-Feature '%s' already exists! %s: %s",
                            target_summary, existing_feature.key, existing_feature.fields.summary)
            continue
        else:
            if update:
                log.logger.info("Creating a new E-Feature for Feature %s: %s", parent_feature.key, target_summary)
                jira.clone_e_feature_from_parent(target_summary, parent_feature, scenario, sibling=source_e_feature, log=log)
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


