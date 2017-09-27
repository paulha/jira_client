from jira_class import Jira, get_query


def update_fields_and_link(jira, source_preq, target_preq, update, update_count, log=None):
    # read existing values, update only if not set...
    updated = False
    validation_lead = jira.get_field_name("Validation Lead")
    classification = jira.get_field_name("Classification")

    update_fields = {}
    # if source_preq.fields.status is not None:
    #     if True or (target_preq.fields.status is not None
    #             and source_preq.fields.status.name != target_preq.fields.status.name) \
    #             or target_preq.fields.status is None:
    #         transitions = jira.jira_client.transitions(target_preq)
    #         # update_fields['status'] = {'name': source_preq.fields.status.name}
    #         pass

    if target_preq.fields.priority is None and source_preq.fields.priority is not None:
        update_fields['priority'] = {'name': source_preq.fields.priority.name}
    if target_preq.fields.assignee is None and source_preq.fields.assignee is not None:
        update_fields['assignee'] = {'name': source_preq.fields.assignee.name}
    if getattr(target_preq.fields, validation_lead) is None \
            and getattr(source_preq.fields, validation_lead) is not None:
        update_fields[validation_lead] = {'name': getattr(source_preq.fields, validation_lead).name}

    if target_preq.fields.issuetype.name not in ['E-Feature']:
        # -- (Can't add classification to E-Feature)
        classification_value = getattr(target_preq.fields, classification)
        classification_value = [v.value for v in classification_value]
        if classification_value is None or \
                        'Unassigned' in classification_value or \
                        'None' in classification_value:
            # -- Unconditional set:
            update_fields[classification] = [{'value': 'Functional Use Case'}]
        else:
            # -- Seems wrong to not catch this condition...
            #    FIXME: This is likely the wrong way to check this...
            if ['Functional Use Case'] != classification_value:
                log.logger.warning("Item %s Classification was alreaady set to %s",
                                   target_preq.key, getattr(target_preq.fields, classification))
                log.logger.warning("And is being overwritten")
                update_fields[classification] = [{'value': 'Functional Use Case'}]

    if len(update_fields) > 0:
        if update:
            # -- only update if we're going to change something...
            log.logger.info("Updating %s with %s", target_preq.key, update_fields)
            target_preq.update(notify=False, fields=update_fields)
            updated = True
        else:
            log.logger.info("NO UPDATE; SHOULD update %s with %s", target_preq.key, update_fields)

    # -- Check to see if there's a link between this issue and its source
    is_related_to_source = [link.outwardIssue
                            for link in target_preq.fields.issuelinks
                            if hasattr(link, "outwardIssue") and link.type.name == "Related Feature"]

    if not is_related_to_source:
        if update:
            jira.create_issue_link("Related Feature", target_preq, source_preq,
                                   comment={"body": "Related Feature link added from %s to %s"
                                            % (target_preq.key, source_preq.key)})
            log.logger.info("Create 'Related Feature' link: %s --> %s", target_preq.key, source_preq.key)
            updated = True
        else:
            log.logger.warning("Link from %s --> %s is MISSING", target_preq.key, source_preq.key)

    if updated:
        update_count += 1

    return update_count


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
    verify_copy = scenario['verify_copy'] if 'verify_copy' in scenario else True;

    log.logger.info("Verify is %s and Update is %s", verify, update)
    log.logger.info("=================================================================")

    # -- Get and format it:
    jira = Jira(scenario['name'], search, log=log.logger)

    global_id = jira.get_field_name("Global ID")
    feature_id = jira.get_field_name("Feature ID")

    source_preq_scanned = 0
    source_areq_scanned = 0
    ucis_created = 0
    e_features_created = 0
    warnings_issued = 0
    verify_failures = 0
    update_failures = 0
    processing_errors = 0

    update_count = 0

    def compare_items(item_kind, source_name, source_query, target_name, target_query, log=None):
        def read_items(query, log=None):
            """Read items into summary based dictionary, warning on duplicates

            There's a strange thing happening: Some values (e.g., objects)
            are being returned from the query more than once, making it look
            like there are duplications when there are not. Made the duplication
            detecting logic smarter than it was before... :-("""
            dictionary = {}
            for item in jira.do_query(query):
                item_key = Jira.remove_version_and_platform(Jira.strip_non_ascii(item.fields.summary))
                if item_key not in dictionary:
                    dictionary[item_key] = [item]
                else:
                    # So, what we have now is a POTENTIAL duplicate. figure out if it really is.
                    if item.key != dictionary[item_key][0].key:
                        # Yep, it's not the same item key...
                        dictionary[item_key].append(item)
                        log.logger.debug("Item key '%s' : '%s' creates a duplicate entry with key '%s': '%s'",
                                           item.key, item.fields.summary,
                                           dictionary[item_key][0].key, dictionary[item_key][0].fields.summary)
                    pass

            return dictionary

        def scan_dups(source_dict, printit):
            for k, v in source_dict.items():
                if len(v) > 1:
                    keys = []
                    for item in v:
                        keys.append(item.key)
                    printit(keys, k)
            return

        source = read_items(source_query, log)
        scan_dups(source, lambda x, y: log.logger.error("Duplicate %s summaries: %s '%s'", source_name, x, y))
        log.logger.info( "Source has %d items in dictionary", len(source))
        target = read_items(target_query, log)
        scan_dups(target, lambda x, y: log.logger.error("Duplicate %s summaries: %s '%s'", target_name, x, y))
        log.logger.info( "Target has %d items in dictionary", len(target))

        # -- Everything in source should be copied to target:
        not_in_target = [{'source': value[0].key, 'summary': key}
                         for key, value in source.items()
                         if Jira.remove_version_and_platform(Jira.strip_non_ascii(key)) not in target]
        if len(not_in_target) > 0:
            log.logger.error("")
            log.logger.error("Could not find %s %s (source) %s summary items in target: ",
                             len(not_in_target), source_name, item_kind)
            log.logger.error("")
            for item in not_in_target:
                log.logger.error("Source '%s', summary text: '%s'", item['source'], item['summary'])
            log.logger.error("--")

        # # -- Target should not have stuff in it that's not from the source!:
        not_in_source = [{'target': value[0].key, 'summary': Jira.remove_version_and_platform(Jira.strip_non_ascii(key))}
                         for key, value in target.items()
                         if Jira.remove_version_and_platform(Jira.strip_non_ascii(key)) not in source]
        if len(not_in_source) > 0:
            log.logger.error("")
            log.logger.error("Could not find %s %s (target) %s summary items in source: ",
                             len(not_in_source), target_name, item_kind)
            log.logger.error("")
            for item in not_in_source:
                log.logger.error("%s Target '%s', summary text: '%s'", item_kind, item['target'], item['summary'])
            log.logger.error("--")

        return

    # -- Copy source preqs to target:
    # (Get the list of already existing PREQs for this platform and version!)
    if 'copy_preq' not in scenario or scenario['copy_preq']:    # e.g., copy_preq is undefined or copy_preq = True
        for source_preq in jira.do_query(preq_source_query):
            # # -- Remove old version and platform, prepend new version and platform
            source_preq_scanned += 1
            log.logger.debug("Search for: '%s'", source_preq.fields.summary)
            target_summary = Jira.remove_version_and_platform(source_preq.fields.summary)
            target_summary = target_summary_format % target_summary
            existing_preq = jira.get_item(preq_summary=target_summary, log=log)
            if existing_preq is not None:
                # -- This is good, PREQ is already there so nothing to do.
                log.logger.info("Found existing UCIS: %s '%s'", existing_preq.key, existing_preq.fields.summary)
                # -- Note: Patch the GID entry of this item...
                if 'FIX_GID' in scenario and scenario['FIX_GID']:
                    update_fields = {}
                    if getattr(existing_preq.fields, global_id) is None or not getattr(existing_preq.fields, global_id):
                        # -- Patch the GID entry of this item...
                        log.logger.info("GID of %s is empty, should be %s from %s",
                                        existing_preq.key, getattr(source_preq.fields, global_id), source_preq.key)
                        update_fields[global_id] = getattr(source_preq.fields, global_id)

                    if getattr(existing_preq.fields, feature_id) is None or not getattr(existing_preq.fields, feature_id):
                        # -- Patch the Feature ID entry of this item...
                        log.logger.info("Feature ID of %s is empty, should be %s from %s",
                                        existing_preq.key, getattr(source_preq.fields, feature_id), source_preq.key)
                        update_fields[feature_id] = getattr(source_preq.fields, feature_id)

                    if update and update_fields:
                        existing_preq.update(notify=False, fields=update_fields)
                        update_count += 1

                # ===================================================================================================
                # TODO: AREQ-25319
                # -- AREQ-25319: Copy the priority, assignee, and validation lead from source_preq
                #                Set "Classification" to "Functional Use Case".
                #                Set [AaaG] item to original (existing_preq to source_preq, here)
                #
                # Note that because of where it is, it only affects PREQs, and we want both...
                #
                if 'UPDATE_FIELDS' in scenario and scenario['UPDATE_FIELDS']:
                    update_count = update_fields_and_link(jira, source_preq, existing_preq, update, update_count, log)

                # ===================================================================================================
                pass
            else:
                # -- This Target PREQ is missing, so use Source preq as template to create a new UCIS for the platform:
                log.logger.debug("Need to create new UCIS for: '%s'", target_summary)
                if update and ('CREATE_MISSING_UCIS' not in scenario or scenario['CREATE_MISSING_UCIS']):
                    # -- Create a new UCIS(!) PREQ
                    result = jira.create_ucis(target_summary, source_preq, scenario, log)
                    log.logger.info("Created a new UCIS %s for %s", result.key, target_summary)
                    update_count += 1
                    ucis_created += 1

                    if 'UPDATE_FIELDS' in scenario and scenario['UPDATE_FIELDS']:
                        update_count = update_fields_and_link(jira, source_preq, result, update, update_count, log)

                else:
                    log.logger.warning("Target UCIS is missing, sourced from %s: '%s'", source_preq.key, target_summary)
                    warnings_issued += 1

            if scenario['createmax'] and update_count>=scenario['createmax']:
                break
            pass

    update_count = 0

    # -- copy source e-features to output
    #    This keeps having an exception because the total number of items seems to be changing...
    if 'copy_areq' not in scenario or scenario['copy_areq']:    # e.g., copy_areq is undefined or copy_areq = True
        features = [feature for feature in jira.do_query(areq_source_e_feature_query)]
        for source_e_feature in features:
            # -- The parent for this one should already be in source_features
            source_areq_scanned += 1
            lookup = source_e_feature.fields.parent.key
            try:
                parent_feature = jira.get_item(key=lookup, log=log)
            except Exception as e:
                parent_feature = None   # This should never happen!
                log.logger.fatal("%s: Could not find parent %s of E-Feature %s, looked for '%s'. continuing", e, source_e_feature.fields.parent.key, source_e_feature.key, lookup)
                # -- Note: Well, if we couldn't find the parent, we can't continue
                warnings_issued += 1
                continue

            # -- OK, at this point we can create the E-Feature record, if it's not going to be a duplicate...
            target_summary = Jira.remove_version_and_platform(source_e_feature.fields.summary).strip()
            target_summary = target_summary_format % target_summary
            existing_feature = jira.get_item(areq_summary=target_summary, log=log)

            if existing_feature is not None:
                # -- This E-Feature already exists, don't touch it!
                log.logger.info("The targeted E-Feature '%s' already exists! %s: %s",
                                target_summary, existing_feature.key, existing_feature.fields.summary)
                if 'UPDATE_FIELDS' in scenario and scenario['UPDATE_FIELDS']:
                    update_count = update_fields_and_link(jira, source_e_feature, existing_feature, update, update_count, log)
            else:
                if update:
                    log.logger.info("Creating a new E-Feature for Feature %s: %s", parent_feature.key, target_summary)
                    if 'clone_from_sibling' in scenario and scenario['clone_from_sibling']:
                        created_e_feature = jira.clone_e_feature_from_e_feature(target_summary, parent_feature, source_e_feature, scenario, log=log)
                    else:
                        created_e_feature = jira.clone_e_feature_from_parent(target_summary, parent_feature, scenario, sibling=source_e_feature, log=log)

                    if 'UPDATE_FIELDS' in scenario and scenario['UPDATE_FIELDS']:
                        update_count = update_fields_and_link(jira, source_e_feature, created_e_feature, update,
                                                              update_count, log)
                    e_features_created += 1
                    update_count += 1
                else:
                    log.logger.info("Target E-Feature is missing for Source E-Feature %s, Feature %s: '%s'",
                                    source_e_feature.key, parent_feature.key, target_summary)
                    # -- Create a new E-Feature(!) PREQ

            if scenario['createmax'] and update_count>=scenario['createmax']:
                break

    # -- TODO: Need to account for source and target version and platform
    if verify_copy:
        compare_items("UCIS", scenario['splatform'], preq_source_query, scenario['tplatform'], preq_target_query, log=log)
        compare_items("E-Feature", scenario['splatform'], areq_source_e_feature_query, scenario['tplatform'], areq_target_e_feature_query, log=log)
    else:
        log.logger.warning("Not checking that copy was complete or that duplicates were created.")

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


