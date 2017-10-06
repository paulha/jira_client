from jira_class import Jira, get_query
from re import search

def update_labels(jira, scenario, source_preq, update, update_count, log=None):
    updated = False
    delete_list = [x for x in scenario['delete_labels']] if 'delete_labels' in scenario else []
    add_list = [x for x in scenario['add_labels']] if 'add_labels' in scenario else []

    label_field_name = jira.get_field_name("Labels")
    label_field = getattr(source_preq.fields, label_field_name)

    source_labels = {x: x for x in label_field} if isinstance(label_field, list) else {}
    destination_labels = source_labels.copy()

    # -- Remove labels in delete list from source_labels:
    for regex in delete_list:
        for key, item in source_labels.copy().items():
            if search(regex, item):
                log.logger.info("Removing label %s (found by regex '%s') from item %s",
                                key, regex, source_preq.key)
                del source_labels[key]

    # -- amd insert those in the add list:
    for label in add_list:
        log.logger.info("Adding label %s to item %s",
                        label, source_preq.key)
        source_labels[label] = label

    if source_labels != destination_labels:
        update_fields = {'labels': [key for key, item in source_labels.items()]}
        if update:
            # -- only update if we're going to change something...
            log.logger.info("Updating %s with %s, was %s", source_preq.key, source_labels, destination_labels)
            source_preq.update(notify=False, fields=update_fields)
            jira.jira_client.add_comment(source_preq,
                                         """This Label ('%s') was updated from %s to %s by {command}.

                                         %s""".format_map(scenario)
                                         % (source_preq.key, destination_labels, source_labels,
                                            scenario['comment'] if scenario['comment'] is not None else ""))
            updated = True
        else:
            log.logger.info("NO LABEL UPDATE; will update %s from %s, to %s", source_preq.key, destination_labels, source_labels)

    if updated:
        update_count += 1

    return update_count


def add_label_to_platform_version(parser, scenario, config, queries, search, log=None):
    """Update the Label field, based on the UCIS and E-Feature entries of the source platform"""

    preq_source_query = get_query('preq_source_query', queries, add_label_to_platform_version.__name__, params=scenario, log=log)
    areq_source_e_feature_query = get_query('areq_source_e_feature', queries, add_label_to_platform_version.__name__, params=scenario, log=log)

    log.logger.info("Labeling source platform {splatform}, source android version {sversion} with {label}".format_map(scenario))

    verify = scenario['verify']
    update = scenario['update']

    log.logger.info("Verify is %s and Update is %s", verify, update)
    log.logger.info("=================================================================")

    # -- Get and format it:
    jira = Jira(scenario['name'], search, log=log.logger)

    source_preq_scanned = 0
    source_areq_scanned = 0

    update_count = 0
    added_count = 0

    # -- Label preqs:
    if 'label_preq' not in scenario or scenario['label_preq']:    # e.g., copy_preq is undefined or copy_preq = True
        for source_preq in jira.do_query(preq_source_query):
            updated = False
            source_preq_scanned += 1

            log.logger.info("Source: %s '%s'", source_preq.key, source_preq.fields.summary)

            if 'UPDATE_FIELDS' in scenario and scenario['UPDATE_FIELDS']:
                updated = update_labels(jira, scenario, source_preq, update, 0, log)

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
                updated = update_labels(jira, scenario, source_e_feature, update, 0, log)

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

