#!/usr/bin/env python
import pprint

from jira.client import JIRA
import yaml
import os
import sqlite3

# TODO: do this properly
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from jirafields import make_field_lookup
import jiradump
import loaders


CONFIG_FILE = 'config.yaml'
DB_FILE = 'ivirpt.sqlite3'


# set up jira connection
def init():
    """Load Configuration"""
    # Read File
    try:
        stream = open(CONFIG_FILE, 'r')
        config = yaml.load(stream)
    except:
        print "Cannot load configuration file."
        exit(0)

    # Check Options
    try:
        config['connection']['server']
        config['user']['username']
        config['user']['password']
    except:
        print "Cannot load configuration options."
        exit(0)

    # Connect to JIRA
    try:
        auth = (config['user']['username'], config['user']['password'])
        jira = JIRA(config['connection'], basic_auth=auth)
    except Exception as e:
        print e
        print "Failed to connect to JIRA."
        exit(0)

    return jira

def init_db(newdb = False, newfeatures=False, newefeatures=False, newpreq=False):
    if newdb:
        if os.path.exists(DB_FILE):
            os.unlink(DB_FILE)

    conn = sqlite3.connect('ivirpt.sqlite3')
    c = conn.cursor()

    if newfeatures:
        c.execute("DROP TABLE IF EXISTS areq_features")
    c.execute("""
        CREATE TABLE IF NOT EXISTS areq_features (
            jkey TEXT PRIMARY KEY,
            priority TEXT,
            summary TEXT,
            permalink TEXT,
            abt TEXT
        )
    """)

    if newefeatures:
        c.execute("DROP TABLE IF EXISTS areq_e_features")
    c.execute("""
        CREATE TABLE IF NOT EXISTS areq_e_features (
            jkey TEXT PRIMARY KEY,
            feature_jkey TEXT,
            platform TEXT,
            version TEXT,
            priority TEXT,
            status TEXT,
            rejected BOOLEAN,
            summary TEXT,
            permalink TEXT,
            FOREIGN KEY(feature_jkey) REFERENCES areq_features(jkey)
        )
    """)

    if newpreq:
        c.execute("DROP TABLE IF EXISTS preq_features")
    c.execute("""
        CREATE TABLE IF NOT EXISTS preq_features (
            jkey TEXT PRIMARY KEY,
            global_id TEXT,
            platform TEXT,
            version TEXT,
            priority TEXT,
            status TEXT,
            rejected BOOLEAN,
            summary TEXT,
            permalink TEXT
        )
    """)
    
    conn.commit()

    return conn
    
def load_ivi_stuff(j):
    db = init_db(newdb=True)

    fl = make_field_lookup(j)

    loaders.load_features('project = AREQ AND issuetype = Feature ORDER BY key', j, db, fl)

    #EF_QUERY = """project = AREQ AND issuetype = E-Feature AND "Android Version(s)" in (M, N, O) AND "Platform/Program" in (Broxton, "Broxton-P IVI")"""
    EF_QUERY = """project = AREQ AND issuetype = E-Feature AND "Platform/Program" in (Broxton, "Broxton-P IVI")"""
    loaders.load_e_features(EF_QUERY, j, db, fl)

    #PF_QUERY = 'project = PREQ AND issuetype = UCIS AND "Platform/Program" in (Broxton, "Broxton-P IVI") AND "Android Version(s)" in (M, N, O)'
    PF_QUERY = 'project = PREQ AND issuetype = UCIS AND Classification = "Functional Use Case" AND "Platform/Program" in (Broxton, "Broxton-P IVI")'
    loaders.load_preq_features(PF_QUERY, j, db, fl)


def copy_components(j, source_project, dest_project):
    src_comps = j.project_components(project = source_project)
    dest_comps = j.project_components(project = dest_project)

    src_names = set(c.name for c in src_comps)
    dest_names = set(c.name for c in dest_comps)

    print src_names - dest_names
    print dest_names - src_names

    src_comps_by_name = {c.name:c for c in src_comps}
    dest_comps_by_name = {c.name:c for c in dest_comps}

    for comp in src_comps:
        ### print comp
        stuff = {
            'assigneeType': comp.assigneeType,
        }
        try:
            lead = comp.lead.name
            stuff['leadUserName']= lead
        except AttributeError:
            pass

        try:
            desc = comp.description
            stuff['description'] = desc
        except AttributeError:
            pass
        ### print stuff

        if comp.name not in dest_comps_by_name:
            print "%s does not exist, creating"%comp.name
            stuff['project'] = dest_project
            stuff['name'] = comp.name
            ### print stuff
            ### print '*'*40
            j.create_component(**stuff)

        else:
            print "%s already exists, updating"%comp.name
            dest = dest_comps_by_name[comp.name]
            ### print stuff
            ### print '*'*40
            dest.update(stuff)


def main():
    j = init()
    #copy_components(j, 'AREQ', 'CREQ')
    # load_ivi_stuff(j)
    print "not doing anything"


if __name__ == main():
    main()
