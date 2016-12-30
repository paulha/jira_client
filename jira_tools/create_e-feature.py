#!/usr/bin/env python

### TODO : project = CREQ AND issuetype = Feature 

from gojira import init_jira, jql_issue_gen
from jirafields import make_field_lookup

PROJECT = 'CREQ'

ASSIGNEE = 'dajakli'
VAL_LEAD = 'dajakli'

if __name__ == "__main__":
    i = 0

    j = init_jira()
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

