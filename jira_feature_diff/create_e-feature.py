#!/usr/bin/env python

import json
from jira.client import JIRA
import config
import sys

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


jira = JIRA(config.options, config.basic_auth)
from jirafields import make_field_lookup
fl = make_field_lookup(jira)

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

for areq in areqs:
    print areq
    # Create target device dict
    devices = []
    for device in areq[5]:
        devices.append({'value':device})

    val_lead_key = fl.reverse('Validation Lead')
    and_vers_key = fl.reverse('Android Version(s)')
    platprog_key = fl.reverse('Platform/Program')
    exist_on_key = fl.reverse('Exists On')

    # Create Sub-task
    issue_dict = {
        'project': {'key': 'AREQ'},
        'parent': {'key': areq[0]},
        'summary': 'TBD',
        'issuetype': {'name': 'E-Feature'},
        'assignee': {'name': areq[3]},
        val_lead_key: {'name':areq[4]},
        and_vers_key: [{'value':areq[2]}],
        platprog_key: [{'value':areq[1]}],
        exist_on_key: devices}
    jira.create_issue(fields=issue_dict)
