import pprint

def dump_areq_ef(issue, fl):
    "(e-feature) [AREQ-1234] - desc - platform - version - parent - priority - status"
    andv_key = fl.reverse('Android Version(s)')
    plat_key = fl.reverse('Platform/Program')

    dump_fields = [
        issue.fields.issuetype.name,
        issue.key,
        issue.fields.summary,
        getattr(issue.fields, plat_key)[0].value,
        getattr(issue.fields, andv_key)[0].value,
        issue.fields.priority.name,
        issue.fields.status.name,
        issue.fields.parent.key,
        issue.permalink(),
    ]

    print " | ".join(dump_fields)

def dump_areq_f(issue, fl):
    "(e-feature) [AREQ-1234] - desc - platform - version - parent - priority - status"
    andv_key = fl.reverse('Android Version(s)')
    plat_key = fl.reverse('Platform/Program')

    dump_fields = [
        issue.fields.issuetype.name,
        issue.key,
        issue.fields.summary,
        getattr(issue.fields, plat_key)[0].value,
        getattr(issue.fields, andv_key)[0].value,
        issue.fields.priority.name,
        issue.fields.status.name,
        '---',
        issue.permalink(),
    ]

    print " | ".join(dump_fields)
