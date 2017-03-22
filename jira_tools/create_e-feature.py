import argparse
import csv
import sys
from gojira import init_jira, jql_issue_gen, issue_keys_issue_gen
from jirafields import make_field_lookup

import logging
# TODO currently have to set new log file name each time
# make so that it uses issue key to name the file + timestamp
LOG_FILENAME = 'AREQ-22968.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

#AND_VER = "O"
#PLATFORM = 'Broxton-P IVI"'
#droid_ver_id = 'customfield_10811'

def create_from_jql(j):
    i = 0

    fl = make_field_lookup(j)
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')

    #jql = """project = CREQ AND issuetype = Feature AND assignee = swmckeox"""
    jql = """project = %s AND issuetype = Feature"""%(PROJECT,)
    for areq in jql_issue_gen(jql, j):
        print areq.key, areq.fields.summary, getattr(areq.fields, and_vers_key)[0].value

        for platprog in getattr(areq.fields, platprog_key):
            # Create Sub-task
            i += 1
            and_ver = getattr(areq.fields, and_vers_key)[0].value

            ### Nerfed for safety
            #print i, areq.key, platprog.value
            #efeature=create_e_feature_from_feature(j, areq, ASSIGNEE, VAL_LEAD, and_ver, platprog.value)
            #new_sum = efeature.fields.summary.replace('[]', '[4.4]')
            #efeature.update(fields={'summary':new_sum})
            #print "\t", efeature.key,efeature.fields.summary, getattr(efeature.fields, and_vers_key)[0].value
            #print "\t", efeature.key,efeature.fields.summary, getattr(efeature.fields, and_vers_key)[0].value

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
        print "-"*40
        print source_issue.key, source_issue.fields.summary

        feature = ensure_parent_feature(j, source_issue)

        print feature.key, feature.fields.summary

        add_value_to_list(feature, platprog_key, NEW_PLATFORM)
        efeature = create_e_feature_from_feature(jira, feature, ASSIGNEE, VAL_LEAD, AND_VER, NEW_PLATFORM)

        create_count += 1
        print efeature.key, efeature.fields.summary, getattr(efeature.fields, and_vers_key)

    print "created {} new e-features".format(create_count)


def add_dessert(j, jql, dessert):
    update_count = 0

    fl = make_field_lookup(j)
    and_vers_key = fl.reverse('Android Version(s)')


    for issue in jql_issue_gen(jql, j, count_change_ok=True):
        print issue.key
        add_value_to_list(issue, and_vers_key, 'O')
        update_count += 1

    print "Updated {} issues".format(update_count)

def clone_efeature_add_dessert(j, jql, doing_list, target_platform, target_dessert, unassign_new):
    update_count = 0
    fl = make_field_lookup(j)
    val_lead_key = fl.reverse('Validation Lead')
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')

    # get the initial list of source issues and iterate
    for issue in jql_issue_gen(jql, j, count_change_ok=True):
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

            # set the assignee
            if unassign_new:
                target_assign = ""
            else:
                target_assign = issue.fields.assignee.name
        
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
#                    print "already got %s"%issue.key

            if False:
                print "impossibru!"
            else: ### TODO ALL SHOULD CURRENTLY GO THIS ROUTE AS OF 21MAR2017 TODO ###
                new_efeature_dict = {
                    'project': {'key': issue.fields.project.key},
                    'parent': {'key': issue.fields.parent.key},
                    'summary': issue.fields.summary,
                    'issuetype': {'name': 'E-Feature'},
                    'assignee': {'name': target_assign},
                    and_vers_key: [{'value': target_dessert}],
                    platprog_key: [{'value': child_platform}]
                }
            
            print "creating new clone of %s"%issue.key
            efeature = jira.create_issue(fields=new_efeature_dict) 
            update_count += 1
        except:
            logging.exception('cloning process halted and caught fire on issue %s'%issue.key)
            doing_list += [{'error_issue': issue.key, 'error_text': sys.exc_info()[0]}]
            print "caught exception while cloning %s"%issue.key
            return doing_list
 
    print "Updated {} issues".format(update_count)
    return doing_list

if __name__ == "__main__":
    jira = init_jira()
    test_jql = """key = AREQ-21218"""
    done_list = []
    
    # get input from cmd line - TODO to be used for direction to either New Platform or New Dessert functions later
    parser = argparse.ArgumentParser(description='Use this weird trick to save 600% time on cutting your *NEW* Android Requirement E-Features from home and make $7253 a month that insurance companies in OREGON don\'t want YOU to know!!')
    parser.add_argument('-i','--input', help='Input file name',required=False)
    args = parser.parse_args()

    # SDNP = same dessert; new platform / SPND = same platform; new dessert
    # set this according to AREQ request using cmd line args above
    hasNewPlatform = True ## set to True for AREQ-22968
    hasNewDessert = False ## * * * * *
    if hasNewPlatform:
        target_platform = "Icelake-U SDC"
        target_dessert = "O" # set to O for AREQ-22968
    if hasNewDessert:
        target_platform = ""
        target_dessert = "O"

    amy_jql = """project = AREQ AND issuetype = E-Feature AND status in (Open, "In Progress", Closed, Merged, Blocked) AND "Android Version(s)" in (O) AND "Platform/Program" in ("Broxton-P IVI") ORDER BY key ASC"""
    completed = clone_efeature_add_dessert(jira, test_jql, done_list, target_platform, target_dessert, True)
    filename = "test.txt"
    thefile = open('%s'%filename, 'w')
    for item in completed:
        thefile.write("%s\n" % item)
    print "completion file written in this dir as %s"%filename

