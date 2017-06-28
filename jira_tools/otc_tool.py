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

# TODO currently have to set new log file name each time
# make so that it uses issue key to name the file + timestamp
# LOG_FILENAME = "AREQ-22968_22MAR0231.log"
# logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

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
            for plat in p_plats:
                ICL_found = 0
                # todo: Make Generic!
                if plat.value == "Icelake-U SDC":
                    ICL_found += 1

                if ICL_found:
                    log.logger.debug("ICL num check TRUE")
                else:
                    done_list += [{'key': parent.key}]

        except:
            log.logger.error("ISSUE ERROR!")
            done_list += [{'error hit inside dump_parent_info sub-issue search': issue.key}]
            continue

    # -- Dump the output file
    with open(args.output,'w') as outfile:
        for item in done_list:
            outfile.write("%s\n" % item)


def compare_priorities( parser, args, config, queries ):
    search_query = """project = "{sproject}" AND "Platform/Program" = "{splatform}" ORDER BY "Global ID" ASC""".format_map(vars(args))
    log.logger.debug( "search query is: %s", search_query)

    # TODO: Check: shouldn't this qualify by project as well?
    match_query = """ "Platform/Program" = "{tplatform}" AND "Android Version(s)" = '{taversion}' AND 'Global ID' ~ %s""".format_map(vars(args))
    log.logger.debug( "match query is: %s", match_query)

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
        # substitute in the gid at the last moment...
        query = match_query % gid
        try:
            match = jira.search_issues(query, 0)[0]
            id1 = match.fields.priority.id
            id2 = issue.fields.priority.id
            if id1 == id2:
                log.logger.debug("priority match")
            else:
                log.logger.debug("priority mismatch")
                done_list += [{'key': issue.key, 'pri': match.fields.priority.name}]
        except:
            log.logger.warn("ISSUE ERROR!")
            done_list += [{'no match': issue.key}]
            continue

    with open(args.output,'w') as outfile:
        for item in done_list:
            outfile.write("%s\n" % item)


if __name__ == "__main__":
    # Todo: add control of log level
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
    parser.add_argument("-o","--output",nargs='?',default="output.txt",help="Where to store the result.")
    parser.add_argument("-l", "--log_level", choices=['debug','info','warn','error','fatal'])
    parser.add_argument("command", choices=['help','compare_priorities','dump_parents'])
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
    else:
        parser.print_help()
        exit(1)

    log.logger.info( "Run completed." )

