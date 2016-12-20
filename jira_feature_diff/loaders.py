# functions to hit the Jira API and slurp down the data.  This could easily be
# cleaned up so there's no so much duplicated code

def jql_issue_gen(query, jira, show_status=False):
    if not query:
        raise Exception('no query provided')

    if show_status:
        print "JQL:", query

    seen = 0
    startAt = 0
    total = None
    while 1:
        issues = jira.search_issues(query, startAt=startAt)

        if len(issues) == 0:
            if show_status:
                print "loaded all %d issues"%total
            break

        if total is None:
            total = issues.total
        elif total != issues.total:
            raise Exception('Total changed while running %d != %d'%(total, issues.total))

        for i in issues:
            yield i

        seen += len(issues)
        if show_status:
            print "loaded %d issues starting at %d, %d/%d"%(len(issues), startAt, seen, total)
        startAt += len(issues)


### c.execute("""
###     CREATE TABLE areq_features (
###         jkey TEXT PRIMARY KEY,
###         priority TEXT,
###         summary TEXT,
###         permalink TEXT
###     )
### """)
def load_features(query, jira, db, fl):
    c = db.cursor()
    abt_key = fl.reverse('ABT Entry?')

    for f in jql_issue_gen(query, jira, True):
        abtf = getattr(f.fields, abt_key)
        if abtf:
            abtval = abtf.value
        else:
            abtval = 'NULL'

        vals = (
            f.key,
            f.fields.priority.name,
            f.fields.summary,
            f.permalink(),
            abtval
        )
        c.execute('INSERT INTO areq_features VALUES(?,?,?,?,?)', vals)

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
