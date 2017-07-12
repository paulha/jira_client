from os.path import expanduser, pathsep
import argparse
import csv
import sys
from gojira import init_jira, jql_issue_gen, issue_keys_issue_gen
from jirafields import make_field_lookup
from utility_funcs.search import get_server_info
import logging
import logger_yaml as log

CONFIG_FILE = './config.yaml'+pathsep+'~/.jira/config.yaml'
QUERIES_FILE = './queries.yaml'+pathsep+'~/.jira/queries.yaml'

# -- See logger.yaml:
log_file = logging.getLogger("file")
log_file.info("Hello World!")


#AND_VER = "O"
#PLATFORM = 'Broxton-P IVI"'
#droid_ver_id = 'customfield_10811'


## from the create_efeature_add_dessert
#            if target_dessert: ### TODO NOT WORKING TODO NOT WORKING TODO ###
#                # if a new dessert letter is passed, navigate the parent subtask-list for each source child's parent
#                find_parent = "key = %s"%parent_key
#                parent_feature = j.search_issues("key=%s"%issue.fields.parent.key, 0)[0]
#                parent_subtasks = list(parent_feature.fields.subtasks)
#
#                dupe_list = []
#                for subtask in parent_subtasks:
#                    find_subtask_dessert = "key = %s"%subtask.key
#                    subtask_info = j.search_issues(find_subtask_dessert, 0)[0]
#                    subtask_dessert_version = getattr(subtask_info.fields, and_vers_key)[0].value
#                    if (subtask_dessert_version == "O"):
#                        this_issue_prio = [{'issue_id': issue.key, 'parent_id': issue.fields.parent.key, 'clone_id': subtask.key, 'pri_name': issue.fields.priority.name, 'pri_id': issue.fields.priority.id}]
#                        dupe_list.append(subtask_info.key)
#                        # create dupe list
#                if dupe_list:
#                    doing_list += [{'source_id': issue.key, 'summary': 'dupe;no-clone'}]
#                    log.logger.info( "already got %s"%issue.key )
def create_from_jql(j):
    i = 0

    fl = make_field_lookup(j)
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')

    #jql = """project = CREQ AND issuetype = Feature AND assignee = swmckeox"""
    jql = """project = %s AND issuetype = Feature"""%(PROJECT,)
    for areq in jql_issue_gen(jql, j):
        log.logger.info(areq.key, areq.fields.summary, getattr(areq.fields, and_vers_key)[0].value)

        for platprog in getattr(areq.fields, platprog_key):
            # Create Sub-task
            i += 1
            and_ver = getattr(areq.fields, and_vers_key)[0].value

            ### Nerfed for safety
            # log.logger.info( i, areq.key, platprog.value )
            # efeature=create_e_feature_from_feature(j, areq, ASSIGNEE, VAL_LEAD, and_ver, platprog.value)
            # new_sum = efeature.fields.summary.replace('[]', '[4.4]')
            # efeature.update(fields={'summary':new_sum})
            # log.logger.info( "\t", efeature.key,efeature.fields.summary, getattr(efeature.fields, and_vers_key)[0].value )
            # log.logger.info( "\t", efeature.key,efeature.fields.summary, getattr(efeature.fields, and_vers_key)[0].value )


def add_value_to_list(issue, key, new_value):
    values = [x.value for x in getattr(issue.fields, key)]
    if new_value not in values:
        values.append(new_value)
        update = [{'value':v} for v in values]
        issue.update(fields = {key: update})


def ensure_parent_feature(jira, issue):
    if issue.fields.issuetype.name == 'E-Feature':
        feature_key = issue.fields.parent.key
        feature = j.issue(feature_key)
    elif issue.fields.issuetype.name != 'Feature':
        key = issue.key
        itype = issue.fields.issuetype.name
        msg = '{} is a {}, not a Feature or E-Feature'.format(key, itype)
        raise Exception(msg)
    else:
        feature = issue
    return feature


def create_e_feature_from_feature(jira, feature, assignee, val_lead, and_ver, platform):
    fl = make_field_lookup(jira)
    val_lead_key = fl.reverse('Validation Lead')
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')

    new_efeature_dict = {
            'project': {'key': feature.fields.project.key},
            'parent': {'key': feature.key},
            'summary': 'TBD',
            'issuetype': {'name': 'E-Feature'},
            'assignee': {'name': assignee},
            val_lead_key: {'name': val_lead},
            and_vers_key: [{'value': and_ver}],
            platprog_key: [{'value': platform}]
    }

    efeature = jira.create_issue(fields=new_efeature_dict)
    return efeature


def create_from_efeature_key_list(j, filename):
    create_count = 0

    fl = make_field_lookup(j)
    platprog_key = fl.reverse('Platform/Program')
    and_vers_key = fl.reverse('Android Version(s)')

    source_issue_keys = ( line.strip() for line in open(filename) if line.strip() )

    for source_issue in issue_keys_issue_gen(source_issue_keys, j):
        log.logger.info("-" * 40)
        log.logger.info(source_issue.key, source_issue.fields.summary)

        feature = ensure_parent_feature(j, source_issue)

        log.logger.info(feature.key, feature.fields.summary)

        add_value_to_list(feature, platprog_key, NEW_PLATFORM)
        efeature = create_e_feature_from_feature(jira, feature, ASSIGNEE, VAL_LEAD, AND_VER, NEW_PLATFORM)

        create_count += 1
        log.logger.info(efeature.key, efeature.fields.summary, getattr(efeature.fields, and_vers_key))

    log.logger.info("created {} new e-features".format(create_count))


def add_dessert(j, jql, dessert):
    update_count = 0

    fl = make_field_lookup(j)
    and_vers_key = fl.reverse('Android Version(s)')


    for issue in jql_issue_gen(jql, j, count_change_ok=True):
        log.logger.info(issue.key)
        add_value_to_list(issue, and_vers_key, 'O')
        update_count += 1

    log.logger.info("Updated {} issues".format(update_count))


def clone_efeature_add_dessert(jira, jira_query, doing_list, target_platform, target_dessert, unassign_new):
    update_count = 0
    fl = make_field_lookup(jira)
    val_lead_key = fl.reverse('Validation Lead')
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')
    exists_on = fl.reverse('Exists On')

    # get the initial list of source issues and iterate
    for issue in jql_issue_gen(jira_query, jira, count_change_ok=True):
        # TODO set up more logging
        # TODO set up more error handling for things like inactive users
        # TODO encapsulate in such a way that in the future this script should have separate functions to support:
        # * same platform, new dessert
        # * same dessert, new platform
        # current flow is: start with source child -> get to parent by ID -> get parent metadata and cut new e-feature into new platform
        try:
    
            # capture some info from each issue as it gets iterated over
            parent_key = issue.fields.parent.key
            doing_list += [{'parent': parent_key, 'source_child': issue.key, 'summary': issue.fields.summary}]
            # the new e-features should hit this as TRUE if the AREQ requester defined this as an SD;NP: request
            if target_platform:
                child_platform = target_platform
            else: # new e-features should hit this as FALSE if the AREQ requester defined this as an SP;ND: request
                child_platform = getattr(issue.fields, platprog_key)[0].value

            # Note: This looks like a tangiential issue not strictly related to the close...
            # set the assignee
            if issue.fields.assignee.name == 'danunora':
                target_assign = 'daqualls'
            elif issue.fields.assignee.name == 'etang1':
                target_assign = 'daqualls'
            elif issue.fields.assignee.name == 'atena':
                target_assign = 'daqualls' 
            else:
                target_assign = issue.fields.assignee.name
        
            if target_dessert == "":
                child_dessert = getattr(issue.fields, and_vers_key)[0].value

            # Note: These are the values for the record to be created...
            if True: ### TODO ALL SHOULD CURRENTLY GO THIS ROUTE AS OF 21MAR2017 TODO ###
                new_efeature_dict = {
                    'project': {'key': issue.fields.project.key},
                    'parent': {'key': issue.fields.parent.key},
                    'summary': issue.fields.summary,
                    'issuetype': {'name': 'E-Feature'},
                    'assignee': {'name': target_assign},
                    and_vers_key: [{'value': child_dessert}],
                    platprog_key: [{'value': child_platform}],
                    exists_on: [{'value': 'BXT-Joule'}]
                }

            log.logger.info( "creating new clone of %s" % issue.key )
            # fixme: This  doesn't seem right -- would try to create result from new_efeature_dict,
            #        even if it was left over from the previous iteration...
            efeature = jira.create_issue(fields=new_efeature_dict)
            update_count += 1
        except:
            logging.exception('cloning process halted and caught fire on issue %s' % issue.key)
            doing_list += [{'error_issue': issue.key, 'error_text': sys.exc_info()[0]}]
            log.logger.error("caught exception while cloning %s" % issue.key)
            return doing_list
 
    log.logger.info( "Updated {} issues".format(update_count) )
    return doing_list

# def dump_parent_info(jira, search_query, doing_list, target_platform, target_dessert, unassign_new):
#     fl = make_field_lookup(jira)
#     val_lead_key = fl.reverse('Validation Lead')
#     and_vers_key = fl.reverse('Android Version(s)')
#     platprog_key = fl.reverse('Platform/Program')
#     exists_on = fl.reverse('Exists On')
#
#     # get the initial list of source issues and iterate
#     for issue in jql_issue_gen(search_query, jira, count_change_ok=True):
#         # capture some info from each issue as it gets iterated over
#         parent_key = issue.fields.parent.key
#         find_parent = "key = %s" % parent_key
#         parent_feature = jira.search_issues("key=%s" % issue.fields.parent.key, 0)[0]
#         parent_subtasks = list(parent_feature.fields.subtasks)
#         log.logger.info("trying %s" % parent_key)
#         try:
#             parent = jira.search_issues(find_parent, 0)[0]
#             p_plats = []
#             p_plats += getattr(parent.fields, platprog_key)
#             log.logger.info(p_plats)
#             for plat in p_plats:
#                 ICL_found = 0
#                 if plat.value == "Icelake-U SDC":
#                     ICL_found += 1
#
#                 if ICL_found:
#                     log.logger.info("ICL num check TRUE")
#                 else:
#                     doing_list += [{'key': parent.key}]
#
#         except:
#             log.logger.error("ISSUE ERROR!")
#             doing_list += [{'error hit inside dump_parent_info sub-issue search': issue.key}]
#             continue
#
#
#     return doing_list

#============= Retired Code =======================================================
# def compare_priorities( args, config ):
#     jira = init_jira( args.name, config )
#     test_jql = """key = AREQ-23610"""
#     done_list = []
#
#     test_jql = """key = AREQ-23610"""
#     done_list = []
#
#     # get input from cmd line - TODO to be used for direction to either New Platform or New Dessert functions later
#     #    parser = argparse.ArgumentParser(description='Use this weird trick to save 600% time on cutting your *NEW* Android Requirement E-Features from home and make $7253 a month that insurance companies in OREGON don\'t want YOU to know!!')
#     #    parser.add_argument('-i','--input', help='Input file name',required=False)
#     #    args = parser.parse_args()
#
#     # SDNP = same dessert; new platform / SPND = same platform; new dessert
#     # set this according to AREQ request using cmd line args above
#     hasNewPlatform = False
#     hasNewDessert = False
#     if hasNewPlatform:
#         target_platform = "Broxton"
#         target_dessert = ""
#     if hasNewDessert:
#         target_platform = ""
#         target_dessert = "O"
#     else:
#         target_platform = ""
#         target_dessert = ""
#         #    dustin_jql = """project = AREQ AND "Platform/Program" = "Icelake-U SDC" AND issuetype = E-Feature AND priority != P4-Low ORDER BY priority ASC"""
#     amy_jql = """project = "Platforms Requirements" AND "Platform/Program" = "Icelake-U SDC" ORDER BY "Global ID" ASC"""
#     #    completed = dump_parent_info(jira, amy_jql, done_list, target_platform, target_dessert, True)
#     completed = compare_prios(jira, amy_jql, done_list)
#     filename = "17APR1427_AREQ-24084.txt"
#     thefile = open('%s' % filename, 'w')
#     for item in completed:
#         thefile.write("%s\n" % item)
#======================================================================================


def dump_parents(parser, args, config, queries ):
    #
    # -- What's the actual goal of this?
    #
    if dump_parents.__name__ not in queries:
        log.logger.fatal( "Query section for %s is missing: %s", dump_parents.__name__, queries)
        exit(-1)

    items=queries[dump_parents.__name__]

    # -- Make sure search query is defined
    if 'search' not in items:
        log.logger.fatal( "Search query for %s.search is missing: %s", dump_parents.__name__, queries)
        exit(-1)

    # -- Get and format it:
    search_query = items['search'].format_map(vars(args))
    log.logger.debug( "search query is: %s", search_query)

    # -- Make sure the match query is defined. (Don't fill it out yet though...)
    if 'match' not in items:
        log.logger.fatal( "Search query for %s.match is missing: %s", dump_parents.__name__, queries)
        exit(-1)
    match_query=items['match']
    log.logger.debug( "Match query is: %s", match_query)

    done_list = []

    jira = init_jira( args.name, config )

    field_lookup = make_field_lookup(jira)
    val_lead_key = field_lookup.reverse('Validation Lead')
    and_vers_key = field_lookup.reverse('Android Version(s)')
    platprog_key = field_lookup.reverse('Platform/Program')
    gid_finder = field_lookup.reverse('Global ID')

    for issue in jql_issue_gen(search_query, jira, count_change_ok=True):
        log.logger.info("Issue %s: %s", issue.key, issue.fields.summary)

        # -- Guarded access to parent key (may not exist!)
        try:
            parent_key = issue.fields.parent.key

        except AttributeError as e:
            log.logger.error("Exception %s: Results of the query '%s' do not have a 'parent' field.", e, search_query)
            return

        # -- fill out the match search
        temp_dict = {'key': parent_key}     # What we're really looking for...
        temp_dict.update(vars(args))        # other values that might be useful in a complex query
        find_parent = match_query.format_map(temp_dict)
        log.logger.debug("match query is: %s", find_parent)

        try:
            parent = jira.search_issues(find_parent, 0)[0]
            p_plats = []
            p_plats += getattr(parent.fields, platprog_key)
            log.logger.debug(p_plats)
            # todo: Make Generic! (I'm not clear on exactly what this is trying to do...)
            # Looks like this is finding the cases where Icelake is NOT found in p_plats
            #
            #   Note:   This is odd because you should be able to use
            #
            #               if "Icelake-U SDC" not in p_plats:
            #                   log.logger.info( "New      -- Icelake not in %s", parent.key )
            #
            #           but it doesn't work correctly in the case where there's only
            #           a single "Icelake-U SDC" entry in p_plats. It always returns
            #           True in that case, instead of the correct False.
            #

            # todo: Make Generic! (I'm not clear on exactly what this is trying to do...)
            ICL_NOT_found = True
            for plat in p_plats:
                log.logger.debug( "plat is '%s'", plat)
                ICL_NOT_found = False if "Icelake-U SDC" == plat.value else ICL_NOT_found

            if ICL_NOT_found:
                log.logger.info("Icelake not in %s", parent.key)
                done_list += [{'key': parent.key}]
                old_printed=True

        except Exception as e:
            log.logger.error("ISSUE ERROR! %s", e)
            done_list += [{'error hit inside dump_parent_info sub-issue search': issue.key}]
            continue

    # -- Dump the output file
    with open(args.output,'w') as outfile:
        for item in done_list:
            outfile.write("%s\n" % item)


def compare_priorities(parser, args, config, queries):
    if compare_priorities.__name__ not in queries:
        log.logger.fatal( "Query section for %s is missing: %s", dump_parents.__name__, queries)
        exit(-1)

    items=queries[compare_priorities.__name__]

    # -- Make sure search query is defined
    if 'search' not in items:
        log.logger.fatal( "Search query for %s.search is missing: %s", compare_priorities.__name__, queries)
        exit(-1)

    # -- Get and format it:
    search_query = items['search'].format_map(vars(args))
    log.logger.debug( "search query is: %s", search_query)

    # -- Make sure the match query is defined. (Don't fill it out yet though...)
    if 'match' not in items:
        log.logger.fatal( "Search query for %s.match is missing: %s", dump_parents.__name__, queries)
        exit(-1)
    match_query=items['match']
    log.logger.debug( "Match query is: %s", match_query)

    done_list = []

    jira = init_jira( args.name, config )

    field_lookup = make_field_lookup(jira)
    val_lead_key = field_lookup.reverse('Validation Lead')
    and_vers_key = field_lookup.reverse('Android Version(s)')
    platprog_key = field_lookup.reverse('Platform/Program')
    gid_finder = field_lookup.reverse('Global ID')

    for issue in jql_issue_gen(search_query, jira, count_change_ok=True):
        log.logger.info("Issue %s: %s", issue.key, issue.fields.summary)
        gid = getattr(issue.fields, gid_finder)
        log.logger.debug( "trying %s"%gid )

        # -- substitute in the gid at the last moment...
        temp_dict = {'gid': gid}            # What we're really looking for...
        temp_dict.update(vars(args))        # other values that might be useful in a complex query
        query = match_query.format_map(temp_dict)
        log.logger.debug("match query is: %s", query)
        try:
            matches = jira.search_issues(query, 0)
            if isinstance(matches, object) and len(matches)>0:
                match = matches[0]
                id1 = match.fields.priority.id
                id2 = issue.fields.priority.id
                if id1 == id2:
                    log.logger.debug("priority match")
                else:
                    log.logger.debug("priority mismatch")
                    done_list += [{'key': issue.key, 'pri': match.fields.priority.name}]
            else:
                log.logger.info("No match found! -- %s", query)
                done_list += [{'no match': issue.key}]

        except Exception as e:
            # No errors should happen now...
            log.logger.warn("Error occured processing issue -- %s %s", e.__class__, e.__cause__)
            continue

    with open(args.output,'w') as outfile:
        for item in done_list:
            outfile.write("%s\n" % item)


def query_one_item(jira, item_query, param_dict):
    formatted_query = item_query.format_map(param_dict)
    log.logger.debug("get_one_item formatted_query is: %s", formatted_query)
    try:
        item = jira.search_issues(formatted_query, 0)
        if isinstance(item, list) and len(item) > 0:
            item = item[0]
            log.logger.debug("\tget_one_item item found: %s: %s", item.key, item.fields.summary)
        else:
            item = None
            log.logger.debug("No item found for query '%s'!", formatted_query)

    except Exception as e:
        # No errors should happen now...
        log.logger.warn("Error occured processing issue -- %s %s", e.__class__, e.__cause__)

    # -- parent_feature containst the parent or is None.
    return item


def areq_24628(parser, args, config, queries):
    """Create O-MR1 dessert AREQ eFeatures for BXT-P IVI based on O dessert

    Attributes:
        parser (argparse.ArgumentParser): Can be used for option specific parsing of arguments.
        args (Namespace): Dictionary like list of arguments and values from the command line. NOT iterable!
        config (YAML): Hierarchical list of configuration settings based on server name command argument
        queries (YAML): Also a hierarchical list of queries to use...

    Processing:
        * For each AREQ eFeature by this JQL query:
                project = AREQ AND issuetype = E-Feature AND status in (Open, "In Progress", Closed, Merged, Blocked)
                            AND "Android Version(s)" in (O) AND "Platform/Program" in ("Broxton-P IVI")
            - If there is NOT an O-MR1 dessert eFeature mapping to the same Parent:

                * Clone the existing "O" **feature** entry (not the e-feature!)
                * set state to "OPEN"
                * set android version(s) to "O-MR1"
                * (Be sure that Priority, Owner, Exists On are set from the (existing) "O" version of the e-feature.
                   Note that most of these fields should copy from the Feature, even though we're createing an
                   e-feature!)
                * Set title to the O-MR1 dessert version format
                * Save and link to the parent feature

    Note:
        * In verify mode:
            - If sibling_e_feature is found, then it should be compared to the parent_feature from which it
              should have been cloned
            - If sibling_e_feature is NOT found, there is a missing entry which should be logged.

        * In update mode:
            - If sibling_e_feature is found, then update can be short circuited
            - If sibling_e_feature is NOT found, there is a missing entry which should be created.


    :return: Nothing on success, exits on error.
    """
    update = True if args.update is not None else False
    verify = True if args.verify is not None else False

    if areq_24628.__name__ not in queries:
        log.logger.fatal( "Query section for %s is missing: %s", areq_24628.__name__, queries)
        exit(-1)

    items=queries[areq_24628.__name__]

    # -- Make sure search query is defined
    if 'candidate_e-features' not in items:
        log.logger.fatal( "Search query for %s.search is missing: %s", 'candidate_e-features', queries)
        exit(-1)

    # -- Get and format it:
    candidate_efeatures_query = items['candidate_e-features'].format_map(vars(args))
    log.logger.debug( "search query is: %s", candidate_efeatures_query)

    # -- Make sure parent_query is defined
    if 'parent_query' not in items:
        log.logger.fatal( "Parent query for %s.search is missing: %s", 'parent_query', queries)
        exit(-1)

    parent_query = items['parent_query']
    log.logger.debug( "parent query is: %s", parent_query)

    # -- Make sure parent_query is defined
    if 'sibling_query' not in items:
        log.logger.fatal( "Sibling query for %s.search is missing: %s", 'sibling_query', queries)
        exit(-1)

    sibling_query = items['sibling_query']
    log.logger.debug( "sibling query is: %s", sibling_query)

    # -- Get and format it:
    jira = init_jira(args.name, config)

    field_lookup = make_field_lookup(jira)
    and_vers_key = field_lookup.reverse('Android Version(s)')
    platprog_key = field_lookup.reverse('Platform/Program')
    exists_on = field_lookup.reverse('Exists On')

    features_scanned = 0
    update_count = 0
    verify_failures = 0
    processing_errors = 0
    for current_e_feature in jql_issue_gen(candidate_efeatures_query, jira, count_change_ok=True):
        features_scanned += 1
        log.logger.debug("Checking Issue %s: %s", current_e_feature.key, current_e_feature.fields.summary)

        # -- OK so now we have found the source e-feature. We want to get its parent
        param_dict = {'parent_key': current_e_feature.fields.parent}     # What we're really looking for...
        param_dict.update(vars(args))                                    # other values that might be useful in a complex query

        # -- Check for duplicate sibling feature, if found no need to create a new one.
        sibling_e_feature = query_one_item(jira, sibling_query, param_dict)
        if sibling_e_feature is not None:
            # -- Sibling already exists
            if update:
                # -- no need to output a E-Feature
                log.logger.info("Sibling to E-Feature already exists: %s %s", sibling_e_feature.key, sibling_e_feature.fields.summary)

            if verify:
                # -- Look up the parent, to make a comparison
                parent_feature = query_one_item(jira, parent_query, param_dict)
                if parent_feature is None:
                    # -- Sibling without parent
                    log.logger.warning("E-Feature %s has no parent", current_e_feature.key)
                    processing_errors += 1
                # todo: compare the found sibling to the parent, output on compare fail...
                # verify_failures += 1

            continue

        parent_feature = query_one_item(jira, parent_query, param_dict)
        if parent_feature is None:
            # -- Sibling without parent
            log.logger.warning("E-Feature %s has no parent", current_e_feature.key)
            processing_errors += 1
            continue

        # -- Note: Code to fill out new sibling goes here.
        if verify:
            log.logger.warning("Sibling to E-Feature is missing. %s %s", current_e_feature.key, current_e_feature.fields.summary)
            verify_failures += 1

        if update:
            log.logger.info("Creating E-Feature Sibling for Feature: %s %s", parent_feature.key, parent_feature.fields.summary)

            try:
                if current_e_feature.fields.assignee is None:
                    log.logger.debug("Assigning new e-feature to None (is that valid?)")
                    target_assign = None
                elif current_e_feature.fields.assignee.name in ['danunora', 'etang1', 'atena']:
                    log.logger.debug("Assigning new e-feature to 'daqualls'")
                    target_assign = 'daqualls'
                else:
                    target_assign = current_e_feature.fields.assignee.name
            except Exception as e:
                log.logger.error(e, exc_info=True)
                pass

            child_dessert="FIG"
            child_platform="Merry-Go-Round"
            exists_on_platform="Everywhere"

            new_sibling_dict = {
                'project': {'key': parent_feature.fields.project.key},
                'parent': {'key': parent_feature.key},
                'summary': parent_feature.fields.summary,
                'issuetype': {'name': 'E-Feature'},
                'assignee': {'name': target_assign},
                and_vers_key: [{'value': child_dessert}],
                platprog_key: [{'value': child_platform}],
                exists_on: [{'value': exists_on_platform}]
            }

            log.logger.info("creating new clone of %s:%s" % (current_e_feature.key, new_sibling_dict))
            # sibling_e_feature = jira.create_issue(fields=new_efeature_dict)
            update_count += 1

    log.logger.info("%s source E-Features considered. ", features_scanned)

    if verify:
        log.logger.info("%s E-Feature comparison failures. ", verify_failures)

    if update:
        log.logger.info("%s new E-Features were created. ", update_count)

    log.logger.info("%s processing errors. ", processing_errors)


def main():
    parser = argparse.ArgumentParser( description="This is an OTC tool for working with Jira projects.")
    connection_group=parser.add_argument_group(title="Connection control", description="About the connectionn to the server")
    connection_group.add_argument("-n", "--name", nargs='?', default="default", help="Alias for the target host" )
    connection_group.add_argument("-u", "--user", nargs='?', help="User Name (future)" )
    connection_group.add_argument("-p", "--password", nargs='?', help="Password (future)" )
    project_group=parser.add_argument_group(title="Project control", description="Selecting which projects...")
    project_group.add_argument("--sproject", nargs='?', default="Platforms Requirements", help="Jira source project" )
    project_group.add_argument("--splatform", nargs='?', default="Icelake-U SDC", help="Jira source platform" )
    project_group.add_argument("--tplatform", nargs='?', default="Broxton-P IVI", help="Jira source platform" )
    project_group.add_argument("--taversion", nargs='?', default="O", help="Android target version" )
    project_group.add_argument("--update", nargs='?', default=True, help="Update target" )
    project_group.add_argument("--verify", nargs='?', default=True, help="Verify target" )
    parser.add_argument("-o","--output",nargs='?',default="output.txt",help="Where to store the result.")
    parser.add_argument("-l", "--log_level", choices=['debug','info','warn','error','fatal'])
    parser.add_argument("command", choices=['help','compare_priorities','dump_parents','areq-24628'])
    args = parser.parse_args()

    if args.log_level is not None:
        log.logger.setLevel( logging.getLevelName(args.log_level.upper()))

    args.command = args.command.lower()

    config = get_server_info(args.name, CONFIG_FILE)    # possible FileNotFoundError
    queries = get_server_info(args.name, QUERIES_FILE)   # possible FileNotFoundError

    errors = 0
    if config is None:
        errors = 1
        log.logger.fatal("Configuration section for server %s is missing." % (args.name))
        exit(-1)
    if 'username' not in config:
        errors += 1
        log.logger.fatal("username for server %s is missing." % (args.name))
    if 'password' not in config:
        errors += 1
        log.logger.fatal("password for server %s is missing." % (args.name))
    if 'host' not in config:
        errors += 1
        log.logger.fatal("host url for server %s is missing." % (args.name))
    if errors > 0:
        log.logger.fatal("configuration errors were found, exiting." )
        exit(-1)

    # --> Dispatch to action routine:
    log.logger.info("Application Starting! Comamnd='%s'" % args.command)

    if 'help'==args.command:
        parser.print_help()
    elif 'compare_priorities' == args.command:
        compare_priorities(parser, args, config, queries)
    elif 'dump_parents' == args.command:
        dump_parents(parser, args, config, queries)
    elif 'areq-24628' == args.command:
        areq_24628(parser, args, config, queries)
    else:
        parser.print_help()
        exit(1)

    log.logger.info( "Run completed." )
    return


if __name__ == "__main__":
    main()
    exit(0)


