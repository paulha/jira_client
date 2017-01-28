#!/usr/bin/env python

### TODO : project = CREQ AND issuetype = Feature 

from gojira import init_jira, jql_issue_gen, issue_keys_issue_gen
from jirafields import make_field_lookup

PROJECT = 'CREQ'

ASSIGNEE = 'arocchia'
VAL_LEAD = 'arocchia'
NEW_PLATFORM = 'Apollo Lake'

def create_from_jql(j):
    i = 0

    fl = make_field_lookup(j)
    val_lead_key = fl.reverse('Validation Lead')
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')

    #jql = """project = CREQ AND issuetype = Feature AND assignee = swmckeox"""
    jql = """project = %s AND issuetype = Feature"""%(PROJECT,)
    for areq in jql_issue_gen(jql, j):
        print areq.key, areq.fields.summary, getattr(areq.fields, and_vers_key)[0].value

        for platprog in getattr(areq.fields, platprog_key):
            # Create Sub-task
            i += 1
            issue_dict = {
                'project': {'key': areq.fields.project.key},
                'parent': {'key': areq.key},
                'summary': 'TBD',
                'issuetype': {'name': 'E-Feature'},
                'assignee': {'name': ASSIGNEE},
                val_lead_key: {'name':VAL_LEAD},
                and_vers_key: [{'value':getattr(areq.fields, and_vers_key)[0].value}],
                #and_vers_key: [{'value':'4.4'}],
                platprog_key: [{'value':platprog.value}]
            }

            ### Nerfed for safety
            #print i, areq.key, platprog.value
            #efeature = j.create_issue(fields=issue_dict)
            #new_sum = efeature.fields.summary.replace('[]', '[4.4]')
            #efeature.update(fields={'summary':new_sum})
            #print "\t", efeature.key, efeature.fields.summary, getattr(efeature.fields, and_vers_key)[0].value
            #print "\t", efeature.key, efeature.fields.summary, getattr(efeature.fields, and_vers_key)[0].value


def create_from_efeature_key_list(j, filename):
    create_count = 0

    fl = make_field_lookup(j)
    val_lead_key = fl.reverse('Validation Lead')
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')

    source_issue_keys = ( line.strip() for line in open(filename) if line.strip() )

    for source_issue in issue_keys_issue_gen(source_issue_keys, j):
        print "-"*40
        print source_issue.key, source_issue.fields.summary

        if source_issue.fields.issuetype.name == 'E-Feature':
            feature_key = source_issue.fields.parent.key
            feature = j.issue(feature_key)
        elif source_issue.fields.issuetype.name != 'Feature':
            print "WARNING: {} is not a feature".format(source_issue.key)
        else:
            feature = source_issue

        print feature.key, feature.fields.summary

        feature_platforms = [p.value for p in getattr(feature.fields, platprog_key)]
        if NEW_PLATFORM not in feature_platforms:
            feature_platforms.append(NEW_PLATFORM)
            plat_update = [{'value':p} for p in feature_platforms]
            feature.update(fields = {platprog_key: plat_update})

        new_efeature_dict = {
                'project': {'key': feature.fields.project.key},
                'parent': {'key': feature.key},
                'summary': 'TBD',
                'issuetype': {'name': 'E-Feature'},
                'assignee': {'name': ASSIGNEE},
                val_lead_key: {'name':VAL_LEAD},
                and_vers_key: [{'value':'N'}],
                platprog_key: [{'value': NEW_PLATFORM}]
        }
        create_count += 1
        efeature = j.create_issue(fields=new_efeature_dict)
        print efeature.key, efeature.fields.summary, getattr(efeature.fields, and_vers_key)

    print "created {} new e-features".format(create_count)


if __name__ == "__main__":
    jira = init_jira()
    #create_from_efeature_key_list(jira, 'apollo_lake.txt')
