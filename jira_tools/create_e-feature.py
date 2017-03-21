
import csv

from gojira import init_jira, jql_issue_gen, issue_keys_issue_gen
from jirafields import make_field_lookup

#PROJECT = 'AREQ'
#ISSUETYPE = 'E-Feature'
#ASSIGNEE = ''
#VAL_LEAD = 'wilcoxjx'
AND_VER = "O"
#PLATFORM = 'Broxton-P IVI"'
droid_ver_id = 'customfield_10811'

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

def clone_efeature_add_dessert(j, jql, inner_list):
    update_count = 0
    fl = make_field_lookup(j)
    val_lead_key = fl.reverse('Validation Lead')
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')

    for issue in jql_issue_gen(jql, j, count_change_ok=True):
        inner_list += [{'issue_id': issue.key, 'summary': issue.fields.summary}]
        parent_platform = getattr(issue.fields, platprog_key)[0].value
        parent_key = issue.fields.parent.key
        find_parent = "key = %s"%parent_key
        parent_feature = j.search_issues("key=%s"%issue.fields.parent.key, 0)[0]
        parent_subtasks = list(parent_feature.fields.subtasks)

#        dupe_list = []
#        for subtask in parent_subtasks:
#            find_subtask_dessert = "key = %s"%subtask.key
#            subtask_info = j.search_issues(find_subtask_dessert, 0)[0]
#            subtask_dessert_version = getattr(subtask_info.fields, and_vers_key)[0].value
#            if (subtask_dessert_version == "O"):
#                this_issue_prio = [{'issue_id': issue.key, 'parent_id': issue.fields.parent.key, 'clone_id': subtask.key, 'pri_name': issue.fields.priority.name, 'pri_id': issue.fields.priority.id}]
#                dupe_list.append(subtask_info.key)
#                # create dupe list
#        if dupe_list:
#            print "already got %s"%issue.key
#        else:    

        new_efeature_dict = {
            'project': {'key': issue.fields.project.key},
            'parent': {'key': issue.fields.parent.key},
            'summary': issue.fields.summary,
            'issuetype': {'name': 'E-Feature'},
            'assignee': {'name': issue.fields.assignee.name},
            and_vers_key: [{'value': 'O'}],
            platprog_key: [{'value': parent_platform}]
        }

        print "creating new clone of %s"%issue.key
        efeature = jira.create_issue(fields=new_efeature_dict) 
        update_count += 1
    print "Updated {} issues".format(update_count)
    return inner_list

def mycsv_reader(csv_reader): 
    while True: 
        try: 
            yield next(csv_reader) 
        except csv.Error: 
            # error handling what you want.
            print("error caught inside csv reader.")
            pass
        continue 
    return
  
def change_priority_by_id(j, q):
    update_count = 0
#    for k,v in d.items():
#        update_priority_dict = {
#            'key': k,
#            'project': 'AREQ',
#            'priority': v
#        }
#        jira.create_issue(fields=update_priority_dict)
#        print(update_priority_dict)
    results = j.search_issues(q,0)
    target_subtasks = []
    for issue in results:
        parent_id = issue.fields.parent.key
        parent_feature = j.search_issues("key=%s"%parent_id, 0)[0]
        parent_subtask_keys = list(parent_feature.fields.subtasks)
        for subtask in parent_subtask_keys:
            find_subtask_dessert = "key = %s"%subtask.key
            subtask_info = j.search_issues(find_subtask_dessert, 0)[0]
            subtask_dessert_version = getattr(subtask_info.fields, and_vers_key)[0].value
            if (subtask_dessert_version == "O"):
                target_subtasks



        update_count += 1

    return update_count

if __name__ == "__main__":
    jira = init_jira()
#    sibs_list = []
#    csv_in_list = []
    test_jql = """key = AREQ-18873"""
    amy_jql = """project = AREQ AND issuetype = E-Feature AND status in (Open, "In Progress", Closed, Merged, Blocked) AND "Android Version(s)" in (O) AND "Platform/Program" in ("Broxton-P IVI") ORDER BY key ASC"""
#    ccb_jql = """project = AREQ AND issuetype = E-Feature AND "Android Version(s)" in (N) AND "Platform/Program" in ("Broxton-P IVI") AND labels in (CCB_InProgress)"""
#    sib_jql = """key in (AREQ-19472,AREQ-18872,AREQ-19294,AREQ-18909,AREQ-19075,AREQ-19079,AREQ-19091,AREQ-19496,AREQ-19095,AREQ-19103,AREQ-19108,AREQ-19111,AREQ-19115,AREQ-19131,AREQ-19133,AREQ-19168,AREQ-19178,AREQ-19182,AREQ-19187,AREQ-19194,AREQ-19204,AREQ-19205,AREQ-19224,AREQ-19226)"""
#    blocked_jql = """key in (PREQ-20263,PREQ-20255,PREQ-19860,PREQ-19811,PREQ-20434,PREQ-19690)"""
#    jql = """project = AREQ AND assignee != 'mbergstr' AND assignee != 'bfradin' AND issuetype = E-Feature AND status in (Open, "In Progress", Closed, Merged) AND "Android Version(s)" in (N) AND "Platform/Program" in ("Broxton-P IVI") ORDER BY key ASC"""
#    ccb_jql = """project = AREQ AND issuetype = E-Feature AND "Android Version(s)" in (N) AND "Platform/Program" in ("Broxton-P IVI") AND labels in (CCB_InProgress)"""
#    sib_jql = """key in (AREQ-19472,AREQ-18872,AREQ-19294,AREQ-18909,AREQ-19075,AREQ-19079,AREQ-19091,AREQ-19496,AREQ-19095,AREQ-19103,AREQ-19108,AREQ-19111,AREQ-19115,AREQ-19131,AREQ-19133,AREQ-19168,AREQ-19178,AREQ-19182,AREQ-19187,AREQ-19194,AREQ-19204,AREQ-19205,AREQ-19224,AREQ-19226)"""
#    blocked_jql = """key in (PREQ-20263,PREQ-20255,PREQ-19860,PREQ-19811,PREQ-20434,PREQ-19690)"""
#    print_list = clone_efeature_add_dessert(jira, blocked_jql, sibs_list)

#    colnames = ['id', 'priority']
#    data = pandas.read_csv('formatted_pri_list.csv', names=colnames)
#    prilist = data.priority.tolist()
#    idlist = data.id.tolist()
#    for i in idlist:
#        prilist[i].append(idlist[i])
#    print (prilist)

#    with open('formatted_pri_list.csv', 'rU') as infile:
#        reader = csv.reader(infile)
#        mydict = dict(reader)
# open the file in universal line ending mode 
#    with open('formatted_pri_list.csv', 'rU') as infile:
        # read the file as a dictionary for each row ({header : value})
#        reader = csv.DictReader(infile)
#        csv_data = {}
#        for row in reader:
#            for header, value in row.items():
#                try:
#                    csv_data[header].append(value)
#                except KeyError:
#                    csv_data[header] = [value]
#    with open('formatted_pri_list.csv', 'rU') as f:
#        reader = csv.reader(f, dialect=csv.excel_tab)
#        csv_in_list = list(reader)
    completed = change_priority_by_id(jira, test_jql)
    print "updated %d rows"%completed

