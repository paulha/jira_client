import sys
from os.path import expanduser, pathsep, dirname, realpath
from jira_class import Jira, get_query
from navigate import *
from jira.exceptions import JIRAError


def update_fields_and_link(jira, source_preq, target_preq, update, update_count, scenario={}, log=None):

    # FIXME: AREQ-25918 -- Priority should match the priority of the original...
    def _update_value(update_fields, source, target, field_name, tag_name,
                     scenario=None,
                     override_name="", overwrite_name="", inhibit_name=""):
        """OVERRIDE means 'use this value', OVERWRITE means 'replace the value in target'"""
        this_source_field = getattr(source.fields, field_name, None)
        this_target_field = getattr(target.fields, field_name, None)
        source_value = scenario[override_name] \
                    if override_name in scenario\
                    else getattr(this_source_field, tag_name) \
                    if this_source_field is not None \
                    else None
        target_value = getattr(this_target_field, tag_name) \
                    if this_target_field is not None \
                    else None
        source_str = source_value.__str__() if source_value is not None else ""
        target_str = target_value.__str__() if target_value is not None else ""

        # -- If overwrite is unspecified OR target is None OR overwrite flag is True
        if overwrite_name not in scenario or this_target_field is None or scenario[overwrite_name]:
            if inhibit_name \
                    and source_str not in (scenario[inhibit_name] if inhibit_name in scenario else []):
                if source_value is not None and target_str != source_str:
                    update_fields[field_name] = {tag_name: source_value}

    # read existing values, update only if not set...
    updated = False
    classification = jira.get_field_name("Classification")

    update_fields = {}
    assignee_fields = {}
    lead_fields = {}

    _update_value(update_fields, source_preq, target_preq,
                  'priority', 'name',
                  scenario, 'PRIORITY_OVERRIDE', 'PRIORITY_OVERWRITE')
    # (changed from name to key...)
    _update_value(update_fields, source_preq, target_preq,
                  'assignee', 'key',
                  scenario, 'ASSIGNEE_OVERRIDE', 'ASSIGNEE_OVERWRITE')
    # (changed from name to key...)
    _update_value(update_fields, source_preq, target_preq,
                  jira.get_field_name("Validation Lead"), 'key',
                  scenario, 'VALIDATION_LEAD_OVERRIDE', 'VALIDATION_LEAD_OVERWRITE')
    _update_value(update_fields, source_preq, target_preq,
                  jira.get_field_name("Planned Release"), 'value',
                  scenario, 'PLANNED_RELEASE_OVERRIDE', 'PLANNED_RELEASE_OVERWRITE')

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
            log.logger.info("Updating %s with %s", target_preq.key, {**update_fields, **assignee_fields, **lead_fields})
            target_preq.update(notify=False, fields=update_fields)

            try:
                target_preq.update(notify=False, fields=assignee_fields)
            except JIRAError as e:
                log.logger.error("Jira error %s", e)

            try:
                target_preq.update(notify=False, fields=lead_fields)
            except JIRAError as e:
                log.logger.error("Jira error %s", e)

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


def set_translated_status(jira, source, translation_table, default, target, log=None, scenario=None):
    translation = None
    if 'STATUS_OVERRIDE' in scenario and scenario['STATUS_OVERRIDE']:
        name = normalize(scenario['STATUS_OVERRIDE'])
    else:
        name = normalize(source.fields.status.name)
    if name in translation_table:
        translation = translation_table[name]
    else:
        translation = translation_table[default.name]
        log.logger.error("Could not find translation for %s %s on %s, set to %s instead",
                         source.fields.issuetype, source.fields.status.name, target.key,
                         translation['state'].name)

    status_changed = transition_to_state(jira, target, translation['state'], log)
    if status_changed and translation is not None and translation['comment']:
        jira.jira_client.add_comment(target, translation['comment'])

    return status_changed


def set_ucis_status(jira, source_preq, target_preq, log=None, scenario=None):
    e_feature_translation = {
        UCIS_In_Progress.name: {'state': UCIS_In_Progress, 'comment': "Status set to Start Progress"},
        UCIS_Reject.name: {'state': UCIS_Rejected, 'comment': "Status set to Rejected"},
        UCIS_Open.name: {'state': UCIS_Open, 'comment': "Status set to Open"},
        UCIS_Blocked.name: {'state': UCIS_Blocked, 'comment': "Status set to Blocked"},
        UCIS_Merged.name: {'state': UCIS_Merged, 'comment': "Status set to Merged"},
        UCIS_Close.name: {'state': UCIS_Merged,
                           'comment': "Re-opened and set to Merged since this was closed under O-MR0 "
                                      "and need to track re-validation against O-MR1."},
    }
    return set_translated_status(jira, source_preq, e_feature_translation, UCIS_Open, target_preq, log, scenario)


def set_e_feature_status(jira, source_e_feature, target_e_feature, log=None, scenario=None):
    e_feature_translation = {
        E_Feature_Open.name: {'state': E_Feature_Open, 'comment': "Status set to Open"},
        E_Feature_Close.name: {'state': E_Feature_Merge, 'comment': "Status set to Closed"},
        E_Feature_Rejected.name: {'state': E_Feature_Rejected, 'comment': "Status set to Rejected"},
        E_Feature_Start_Progress.name: {'state': E_Feature_Start_Progress,
                                        'comment': "Status set to Start Progress"},
        E_Feature_In_Progress.name: {'state': E_Feature_In_Progress,
                                     'comment': "Status set to In Progress"},

        E_Feature_Blocked.name: {'state': E_Feature_Blocked, 'comment': "Status set to Blocked"},
        E_Feature_Merge.name: {'state': E_Feature_Merge,
                               'comment': "Status set to Merged"},
        E_Feature_Reopen.name: {'state': E_Feature_Reopen, 'comment': "Status set to Re-Opened"},
    }
    return set_translated_status(jira, source_e_feature, e_feature_translation, E_Feature_Open, target_e_feature, log, scenario)


def copy_platform_to_platform(parser, scenario, config, queries, search, log=None):
    """Copy platform to platform, based on the UCIS and E-Feature entries of the source platform"""

    #
    # -- Some sleight of hand here... Original code iterates the results of a JQL query.
    #    If xls_source, this will read in an XLS file, look for a column named "Key" and
    #    read those key values from Jira as source items.
    #
    if 'xls_source' in scenario:
        import pandas as pd
        source_file = realpath(dirname(realpath(sys.argv[0])) + '/../' + scenario['xls_source'])
        data_frame = pd.read_excel(source_file, sheetname=0)
        def preq_item_list(jira):
            for key in data_frame['Key']:
                if key.upper().startswith('PREQ'):
                    yield jira.issue(key)

        def areq_e_feature_list(jira):
            for key in data_frame['Key']:
                if key.upper().startswith('AREQ'):
                    yield jira.issue(key)
    else:
        preq_source_query = get_query('preq_source_query', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
        if preq_source_query is not None:
            def preq_item_list(jira):
                return jira.do_query(preq_source_query)

        areq_source_e_feature_query = get_query('areq_source_e_feature', queries, copy_platform_to_platform.__name__,
                                                params=scenario, log=log)
        if areq_source_e_feature_query is not None:
            def areq_e_feature_list(jira):
                return jira.do_query(areq_source_e_feature_query)

    preq_target_query = get_query('preq_target_query', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
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
    preq_count = 0
    areq_count = 0

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
        for source_preq in preq_item_list(jira):
            preq_count += 1
            updated = False
            # # -- Remove old version and platform, prepend new version and platform
            source_preq_scanned += 1
            log.logger.debug("Search for: '%s'", source_preq.fields.summary)
            target_summary = Jira.remove_version_and_platform(source_preq.fields.summary)
            target_summary = target_summary_format % target_summary
            existing_preq = jira.get_item(preq_summary=target_summary, log=log)
            if existing_preq is not None:
                # -- This is good, PREQ is already there so nothing to do.
                log.logger.info("%s Found existing UCIS: %s '%s'",
                                preq_count, existing_preq.key, existing_preq.fields.summary)
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
                        updated = True

                #
                # Note that because of where it is, it only affects PREQs, and we want both...
                #
                if 'UPDATE_FIELDS' in scenario and scenario['UPDATE_FIELDS']:
                    count = update_fields_and_link(jira, source_preq, existing_preq, update, 0, scenario, log)
                    if count != 0:
                        updated = True

                if update and 'UPDATE_STATUS' in scenario and scenario['UPDATE_STATUS']:
                    if set_e_feature_status(jira, source_preq, existing_preq, log, scenario):
                        updated = True

                # ===================================================================================================
                pass
            else:
                # -- This Target PREQ is missing, so use Source preq as template to create a new UCIS for the platform:
                log.logger.debug("Need to create new UCIS for: '%s'", target_summary)
                if update and ('CREATE_MISSING_UCIS' not in scenario or scenario['CREATE_MISSING_UCIS']):
                    # -- Create a new UCIS(!) PREQ
                    result = jira.create_ucis(target_summary, source_preq, scenario, log)
                    log.logger.info("%s Created a new UCIS %s for %s", areq_count, result.key, target_summary)

                    updated = True
                    ucis_created += 1

                    if update and 'UPDATE_STATUS' in scenario and scenario['UPDATE_STATUS']:
                        if set_ucis_status(jira, source_preq, result, log, scenario):
                           updated = True

                    if 'UPDATE_FIELDS' in scenario and scenario['UPDATE_FIELDS']:
                        count = update_fields_and_link(jira, source_preq, result, update, 0, scenario, log)
                        if count != 0:
                            updated = True

                else:
                    log.logger.warning("Target UCIS is missing, sourced from %s: '%s'", source_preq.key, target_summary)
                    warnings_issued += 1

            if updated:
                update_count += 1

            if scenario['createmax'] and update_count>=scenario['createmax']:
                break
            pass

    update_count = 0

    # -- copy source e-features to output
    #    This keeps having an exception because the total number of items seems to be changing...
    if 'copy_areq' not in scenario or scenario['copy_areq']:    # e.g., copy_areq is undefined or copy_areq = True
        # features = [feature for feature in areq_e_feature_list(jira)]
        # for source_e_feature in features:
        for source_e_feature in areq_e_feature_list(jira):
            areq_count += 1
            updated = False
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
                log.logger.info("%s The targeted E-Feature '%s' already exists! %s, %s: %s",
                                areq_count, target_summary, source_e_feature.key, existing_feature.key, existing_feature.fields.summary)
                if 'UPDATE_FIELDS' in scenario and scenario['UPDATE_FIELDS']:
                    count = update_fields_and_link(jira, source_e_feature, existing_feature, update, 0, scenario, log)
                    if count != 0:
                        updated = True

                if update and 'UPDATE_STATUS' in scenario and scenario['UPDATE_STATUS']:
                    if set_e_feature_status(jira, source_e_feature, existing_feature, log, scenario):
                        updated = True
            else:
                if update:
                    log.logger.info("%s Creating a new E-Feature for Feature %s: %s",
                                    areq_count, parent_feature.key, target_summary)
                    if 'clone_from_sibling' in scenario and scenario['clone_from_sibling']:
                        created_e_feature = jira.clone_e_feature_from_e_feature(target_summary, parent_feature, source_e_feature, scenario, log=log)
                    else:
                        created_e_feature = jira.clone_e_feature_from_parent(target_summary, parent_feature, scenario, sibling=source_e_feature, log=log)
                    updated = True
                    e_features_created += 1

                    if 'UPDATE_FIELDS' in scenario and scenario['UPDATE_FIELDS']:
                        count = update_fields_and_link(jira, source_e_feature, created_e_feature, update,
                                                              0, scenario, log)
                        if count != 0:
                            updated = True

                    if update and 'UPDATE_STATUS' in scenario and scenario['UPDATE_STATUS']:
                        if set_e_feature_status(jira, source_e_feature, created_e_feature, log, scenario):
                            updated = True

                else:
                    log.logger.info("%s Target E-Feature is missing for Source E-Feature %s, Feature %s: '%s'",
                                    areq_count, source_e_feature.key, parent_feature.key, target_summary)
                    # -- Create a new E-Feature(!) PREQ

            if updated:
                update_count += 1

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


