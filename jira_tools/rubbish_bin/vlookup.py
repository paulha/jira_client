#!/usr/bin/env python

import json
from jira.client import JIRA
from gojira import init_jira
import sys
import pyexcel as pe
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# jira = JIRA(config.options, config.basic_auth)


reqs = [
('PREQ-23802','PREQ-24922'),
('PREQ-24319', 'PREQ-24703')
]
# import .xlsx file where first worksheet
# areqs = pe.iget_records(file_name="vlookup.xlsx")



def get_valid_transition(issue, transition_name):
    """Find Valid Transition for Issue"""
    transitions = jira.transitions(issue)

    # Find Transition ID
    for t in transitions:
        print t['name']
        if (transition_name == t['name']):
            return t['id']
    return None


def update_status(source, destination):
    """Attempt to Update Status"""

    print "TRANSITIONS IDS"
    print  "REJECTED: " + get_valid_transition(destination, "To Rejected")

    # Check for same status
    if (source.fields.status.name == destination.fields.status.name):
        return

    # Check for valid transition
    transition_id = get_valid_transition(destination, source.fields.status.name)

    # Update Status
    if (transition_id):
        transition_issue(destination, transition_id)

def vlookup_data(jira, map_file):
    for preq in map_file:
        # Print
        print("GID %s matches N-dessert %s and O-dessert %s" % (preq['Global ID'], preq['N-dessert'], preq['O-dessert']))
        source = jira.issue(preq['N-dessert'])
        destination = jira.issue(preq['O-dessert'])
        # Updated Fields
        updated_fields = {}

        # Components
        all_components = []
        for component in source.fields.components:
            all_components.append({"name": component.name})
        if all_components:
            updated_fields["components"] = all_components

        # Assignee
        assignee = source.fields.assignee
        if assignee:
            updated_fields["assignee"] = {"name": assignee.name}

        # Validation Lead
        validation_lead = source.fields.customfield_19700
        if validation_lead:
            updated_fields["customfield_19700"] = {"name": validation_lead.name}

        # Priority
        priority = source.fields.priority
        if priority:
            updated_fields["priority"] = {"name": priority.name}

        # Update
        if updated_fields:
            destination.update(fields=updated_fields)
        
    return len(updated_fields)

#    print areq[0] + " -> " + areq[1]
#    source = jira.issue(areq[0])
#    destination = jira.issue(areq[1])


    # Fix Version/s
#    fix_versions = []
#    for version in source.fields.fixVersions:
#        fix_versions.append({"name": version.name})
#    if fix_versions:
#        updated_fields["fixVersions"] = fix_versions

    # Exists On
#    exists_on = []
#    if source.fields.customfield_18202:
#        for target in source.fields.customfield_18202:
#            exists_on.append({"value": target.value})
#    if exists_on:
#        updated_fields["customfield_18202"] = exists_on

    # Verified On
#    verified_on = []
#    if source.fields.customfield_15301:
#        for target in source.fields.customfield_15301:
#            verified_on.append({"value": target.value})
#    if verified_on:
#        updated_fields["customfield_15301"] = verified_on

    # Planned Release
#    if source.fields.customfield_18400:
#        updated_fields["customfield_18400"] = {"value": source.fields.customfield_18400.value}

    # Actual Release
#    if source.fields.customfield_17803:
#        updated_fields["customfield_17803"] = {"value": source.fields.customfield_17803.value}

    # Test Date/Time
#    if source.fields.customfield_12121:
#        updated_fields["customfield_12121"] = source.fields.customfield_12121

    # Labels
#    if source.fields.labels:
#        destination.update(fields={"labels": source.fields.labels})

    # Status
#    update_status(source, destination)

    # Link
#    jira.create_issue_link("Duplicate",source,destination)

    # Link and Comment
#    jira.create_issue_link("Duplicate",source,destination,
#        comment={"body": "Platform Requirements have been transitioned to iCDG JAMA instance.\n\r\n\rReplacing '%s' --> '%s'" % (source.key, destination.key)})

    # Reject Source
#    jira.transition_issue(source, 51)


if __name__ == "__main__":
    jira = init_jira()
#   import .xlsx file where first worksheet is A1=Global ID, B1=N-dessert, C1=O-dessert

###
    sys.exit("edit line 156 in this file and then uncomment it to run .xlsx-based PREQ change script")
# Rename the file input in the below iget_records function arg
# TODO make script take file input given as python arg during call
    preqs = pe.iget_records(file_name="vlookup.xlsx")
    changes_made = vlookup_data(jira, preqs)
    
