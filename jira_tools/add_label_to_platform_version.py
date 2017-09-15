from jira_class import Jira, get_query


def update_labels(jira, scenario, source_preq, new_label, update, update_count, log=None):
    updated = False
    labels = jira.get_field_name("Labels")

    update_fields = {}
    # -- (Can't add classification to E-Feature)
    labels_value_was = getattr(source_preq.fields, labels)
    labels_value_new = [new_label].__add__([v for v in labels_value_was if v != new_label])
    if labels_value_was != labels_value_new:
        update_fields = {labels: labels_value_new}
        if update:
            # -- only update if we're going to change something...
            log.logger.info("Updating %s with %s, was %s", source_preq.key, update_fields, getattr(source_preq.fields, labels))
            source_preq.update(notify=False, fields=update_fields)
            jira.jira_client.add_comment(source_preq,
                                         """This Label ('%s') was updated by {command}.

                                         %s""".format_map(scenario)
                                         % (new_label,
                                            scenario['comment'] if scenario['comment'] is not None else ""))
            updated = True
        else:
            log.logger.info("NO LABEL UPDATE; SHOULD update %s with %s, was %s", source_preq.key, update_fields, getattr(source_preq.fields, labels))

    if updated:
        update_count += 1

    return update_count


def add_label_to_platform_version(parser, scenario, config, queries, search, log=None):
    """Copy platform to platform, based on the UCIS and E-Feature entries of the source platform"""

    preq_source_query = get_query('preq_source_query', queries, add_label_to_platform_version.__name__, params=scenario, log=log)
    areq_source_e_feature_query = get_query('areq_source_e_feature', queries, add_label_to_platform_version.__name__, params=scenario, log=log)

    log.logger.info("Labeling source platform {splatform}, source android version {sversion} with {label}".format_map(scenario))

    verify = scenario['verify']
    update = scenario['update']
    label = scenario['label']

    log.logger.info("Verify is %s and Update is %s", verify, update)
    log.logger.info("=================================================================")

    # -- Get and format it:
    jira = Jira(scenario['name'], search, log=log.logger)

    source_preq_scanned = 0
    source_areq_scanned = 0

    update_count = 0
    added_count = 0

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
                log.logger.error("Target '%s', summary text: '%s'", item['target'], item['summary'])
            log.logger.error("--")

        # for key, value in target.items():
        #     item_key = Jira.remove_version_and_platform(Jira.strip_non_ascii(key))
        #     if item_key not in source:
        #         log.logger.error("%s %s in target was not in original source: %s", item_kind, value[0].key, key)

        return

    # -- Label preqs:
    if 'label_preq' not in scenario or scenario['label_preq']:    # e.g., copy_preq is undefined or copy_preq = True
        for source_preq in jira.do_query(preq_source_query):
            updated = False
            source_preq_scanned += 1

            log.logger.info("Source: %s '%s'", source_preq.key, source_preq.fields.summary)

            if 'UPDATE_FIELDS' in scenario and scenario['UPDATE_FIELDS']:
                updated = update_labels(jira, scenario, source_preq, label, update, 0, log)

            if updated:
                update_count += 1

            if scenario['createmax'] and update_count>=scenario['createmax']:
                break

    added_count += update_count
    update_count = 0

    # -- copy source e-features to output
    #    This keeps having an exception because the total number of items seems to be changing...
    if 'label_areq' not in scenario or scenario['label_areq']:    # e.g., copy_areq is undefined or copy_areq = True
        e_features = [e_feature for e_feature in jira.do_query(areq_source_e_feature_query)]
        for source_e_feature in e_features:
            updated = False
            source_areq_scanned += 1

            log.logger.info("Source: %s '%s'", source_e_feature.key, source_e_feature.fields.summary)

            if 'UPDATE_FIELDS' in scenario and scenario['UPDATE_FIELDS']:
                updated = update_labels(jira, scenario, source_e_feature, label, update, 0, log)

            if updated:
                update_count += 1

            if scenario['createmax'] and update_count >= scenario['createmax']:
                break

    added_count += update_count

    log.logger.info("-----------------------------------------------------------------")
    log.logger.info("%s UCIS source entries were considered. ", source_preq_scanned)
    log.logger.info("%s E-Feature source entries were considered. ", source_areq_scanned)
    log.logger.info("%s labels added. ", added_count)
    log.logger.info("")

