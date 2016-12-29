#!/usr/bin/env python

### TODO : project = CREQ AND issuetype = Feature 

from gojira import init_jira, jql_issue_gen
from jirafields import make_field_lookup

PROJECT = 'CREQ'

areqs= [
('AREQ-16492','Glenview','N','pzou1','ruili1x',['']),
('AREQ-11608','Glenview','N','eepshtey','maxiaoso',['']),
('AREQ-11607','Glenview','N','eepshtey','maxiaoso',['']),
('AREQ-11606','Glenview','N','eepshtey','maxiaoso',['']),
('AREQ-10268','Glenview','N','eepshtey','maxiaoso',['']),
('AREQ-389','Glenview','N','eepshtey','maxiaoso',['']),
('AREQ-327','Glenview','N','eepshtey','maxiaoso',['']),
('AREQ-265','Glenview','N','eepshtey','maxiaoso',[''])
]

ASSIGNEE = None
VAL_LEAD = None

if __name__ == "__main__":
    i = 0

    j = init_jira()
    fl = make_field_lookup(j)

    val_lead_key = fl.reverse('Validation Lead')
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')
    exist_on_key = fl.reverse('Exists On')

    jql = """project = CREQ AND issuetype = Feature AND assignee = swmckeox"""
    for areq in jql_issue_gen(jql, j):
        print areq.key, areq.fields.summary

        for platprog in getattr(areq.fields, platprog_key):
            # Create Sub-task
            i += 1
            issue_dict = {
                'project': {'key': PROJECT},
                'parent': {'key': areq.key},
                'summary': 'TBD',
                'issuetype': {'name': 'E-Feature'},
                'assignee': {'name': ASSIGNEE},
                val_lead_key: {'name':VAL_LEAD},
                #and_vers_key: [{'value':getattr(areq.fields, and_vers_key)[0].value}],
                platprog_key: [{'value':platprog.value}]
            }

            print i, areq.key, platprog.value
            efeature = j.create_issue(fields=issue_dict)
            new_sum = efeature.fields.summary.replace('[]', '[4.4]')
            efeature.update(fields={'summary':new_sum})
            print efeature.key, efeature.fields.summary

