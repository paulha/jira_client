#!/usr/bin/env python
import pprint

from jira.client import JIRA
import yaml
import os
import sqlite3
import itertools
import collections
import pprint

# TODO: do this properly
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from jirafields import make_field_lookup
import jiradump
import areq as loader


CONFIG_FILE = 'config.yaml'
DB_FILE = 'ivirpt.sqlite3'


def init():
    """Load Configuration"""
    # Read File
    try:
        stream = open(CONFIG_FILE, 'r')
        config = yaml.load(stream)
    except:
        print( "Cannot load configuration file." )
        exit(0)

    # Check Options
    try:
        config['connection']['server']
        config['user']['username']
        config['user']['password']
    except:
        print( "Cannot load configuration options." )
        exit(0)

    # Connect to JIRA
    try:
        auth = (config['user']['username'], config['user']['password'])
        jira = JIRA(config['connection'], basic_auth=auth)
    except Exception as e:
        print( e )
        print( "Failed to connect to JIRA." )
        exit(0)

    return jira

def main():
    j = init()
    fl = make_field_lookup(j)

    query = 'project = AREQ AND issuetype = Task'
    if not query:
        raise Exception('no query provided')

    values = collections.Counter()
    seen = 0
    startAt = 0
    total = None
    while 1:
        issues = j.search_issues(query, startAt=startAt)

        if len(issues) == 0:
            print( "loaded all %d issues"%total )
            break

        if total is None:
            total = issues.total
        elif total != issues.total:
            raise Exception('Total changed while running %d != %d'%(total, issues.total))

        values.update(c.value for c in itertools.chain(*[i.fields.customfield_13603 for i in issues]))

        seen += len(issues)
        print( "loaded %d issues starting at %d, %d/%d"%(len(issues), startAt, seen, total) )
        startAt += len(issues)

    pprint.pprint(sorted(values.items(), lambda a,b:-cmp(a[1],b[1])))


if __name__ == main():
    main()
