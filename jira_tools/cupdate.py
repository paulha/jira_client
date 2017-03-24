#!/usr/bin/env python

import json
from jira.client import JIRA
from jirafields import make_field_lookup
from gojira import init_jira
import sys
import pyexcel as pe
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def update_new_preq_component_from_old_preq(jira, old_preqs):
    print "Attempting to copy component information from:"
    update_count = 0
    fl = make_field_lookup(jira)
    gid_key = fl.reverse('Global ID')
    for preq in old_preqs:
        source = jira.issue(preq['source'])
        gid = getattr(source.fields, gid_key)
        updated_fields = {}
        all_components = []
        for component in source.fields.components:
            all_components.append({"name": component.name})
        if all_components:
            updated_fields["components"] = all_components
        destination = jira.search_issues("\"Platform/Program\" = \"Icelake-U SDC\" AND \"Global ID\" ~ \"%s\""%gid, 0)[0]
        if updated_fields:
            print "%s >>>---%s--->>> %s"%(source.key,all_components,destination.key)
            destination.update(fields=updated_fields)
            update_count += 1

    return update_count

if __name__ == "__main__":
    jira = init_jira()
# TODO make script take file input given as python arg during call
    preqs = pe.iget_records(file_name="cupdate.xlsx")
    updates_made = update_new_preq_component_from_old_preq(jira, preqs)
    print "%s updates were made. Today was a good day."%updates_made

