#!/usr/bin/env python
import pprint

import os
import sqlite3

from jirafields import make_field_lookup
import jiradump
from gojira import init_jira, jql_issue_gen


DB_FILE = 'ivirpt.sqlite3'

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
            abt TEXT,
            profile TEXT
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

def load_features(query, jira, db, fl):
    c = db.cursor()
    abt_key = fl.reverse('ABT Entry?')
    profile_key = fl.reverse('Profile/s')

    for f in jql_issue_gen(query, jira, True):
        abtf = getattr(f.fields, abt_key)
        if abtf:
            abtval = abtf.value
        else:
            abtval = 'NULL'

        profile = getattr(f.fields, profile_key)
        if profile:
            pprint.pprint(profile)
            profval = "|".join([p.value for p in profile])
        else:
            profval = "NULL"

        vals = (
            f.key,
            f.fields.priority.name,
            f.fields.summary,
            f.permalink(),
            abtval,
            profval
        )
        c.execute('INSERT INTO areq_features VALUES(?,?,?,?,?,?)', vals)

    db.commit()


### c.execute("""
###     CREATE TABLE IF NOT EXISTS areq_e_features (
###         jkey TEXT PRIMARY KEY,
###         feature_jkey TEXT,
###         platform TEXT,
###         android_version TEXT,
###         priority TEXT,
###         status TEXT,
###         summary TEXT,
###         permalink TEXT,
###         FOREIGN KEY(feature_jkey) REFERENCES areq_features(jkey)
###     )
### """)
def load_e_features(query, jira, db, fl):
    c = db.cursor()

    andv_key = fl.reverse('Android Version(s)')
    plat_key = fl.reverse('Platform/Program')

    for f in jql_issue_gen(query, jira, True):
        vals = (
            f.key,
            f.fields.parent.key,
            getattr(f.fields, plat_key)[0].value,
            getattr(f.fields, andv_key)[0].value,
            f.fields.priority.name,
            f.fields.status.name,
            (f.fields.status.name == 'Rejected'),
            f.fields.summary,
            f.permalink(),
        )
        c.execute('INSERT INTO areq_e_features VALUES(?,?,?,?,?,?,?,?,?)', vals)

    db.commit()

###c.execute("""
###    CREATE TABLE IF NOT EXISTS preq_features (
###        jkey TEXT PRIMARY KEY,
###        global_id = TEXT,
###        platform TEXT,
###        version TEXT,
###        priority TEXT,
###        status TEXT,
###        summary TEXT,
###        permalink TEXT,
###    )
###""")
def load_preq_features(query, jira, db, fl):
    c = db.cursor()

    andv_key = fl.reverse('Android Version(s)')
    plat_key = fl.reverse('Platform/Program')
    glob_key = fl.reverse('Global ID')

    for f in jql_issue_gen(query, jira, True):
        vals = (
            f.key,
            getattr(f.fields, glob_key),
            getattr(f.fields, plat_key)[0].value,
            getattr(f.fields, andv_key)[0].value,
            f.fields.priority.name,
            f.fields.status.name,
            (f.fields.status.name == 'Rejected'),
            f.fields.summary,
            f.permalink(),
        )
        c.execute('INSERT INTO preq_features VALUES(?,?,?,?,?,?,?,?,?)', vals)

    db.commit()
    
def load_ivi_stuff(j):
    db = init_db(newdb=True)

    fl = make_field_lookup(j)

    load_features('project = AREQ AND issuetype = Feature AND status = Candidate', j, db, fl)

    #EF_QUERY = """project = AREQ AND issuetype = E-Feature AND "Android Version(s)" in (M, N, O) AND "Platform/Program" in (Broxton, "Broxton-P IVI")"""
    #EF_QUERY = """project = AREQ AND issuetype = E-Feature AND "Platform/Program" in (Broxton, "Broxton-P IVI")"""
    #load_e_features(EF_QUERY, j, db, fl)

    #PF_QUERY = 'project = PREQ AND issuetype = UCIS AND "Platform/Program" in (Broxton, "Broxton-P IVI") AND "Android Version(s)" in (M, N, O)'
    #PF_QUERY = 'project = PREQ AND issuetype = UCIS AND Classification = "Functional Use Case" AND "Platform/Program" in (Broxton, "Broxton-P IVI")'
    #load_preq_features(PF_QUERY, j, db, fl)


def copy_components(j, source_project, dest_project):
    src_comps = j.project_components(project = source_project)
    dest_comps = j.project_components(project = dest_project)

    src_names = set(c.name for c in src_comps)
    dest_names = set(c.name for c in dest_comps)

    print src_names - dest_names
    print dest_names - src_names

    return
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
    j = init_jira()
    #copy_components(j, 'AREQ', 'CREQ')
    load_ivi_stuff(j)
    #print "not doing anything"


if __name__ == main():
    main()
