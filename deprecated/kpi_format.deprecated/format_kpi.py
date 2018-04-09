#!/bin/env python
import csv

def read_kpis(fname):
    kpis = []
    with open(fname) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for rec in reader:
            kpis.append(rec)
    return kpis


# ['Last Activity Date', 'Min', 'Priority', 'Source', '=========Definition_Generic_Fields=========', 'Units', 'Type', 'Actual Debug Start Date', 'Modified By', 'Planned Debug Start Date', 'Description', 'Target (Typical)', 'Max', 'Workspace Name', 'Conditions (old)', 'Rationale', '=========Definition_Specific_Fields=========', '# of Upstream Relationships', 'Name', 'Created Date', '# of Downstream Relationships', 'Created By', 'KPI', 'Reference Value', 'ID', 'Waiver', 'Specific To', 'Project', 'Domain', 'Modified Date', 'Target Type', 'Item Type', 'Applicability', 'Owner', 'Generic Part Is']

MIN_AND_HIGH  = "Min Value and Higher"
MAX_AND_LOW   = "Max Value and Lower"
MIN_MAX_RANGE = "Min-Max Value Range"
SELECT_ONE    = "{Select One}"

def format_kpi(k):
    fmt_rec = {
        "refval" : k.get('Refernce Value'),
        "target" : k.get('Target (Typical)'),
        "units"  : k.get('Units'),
        "minval" : k.get('Min'),
        "maxval" : k.get('Max'),
        "ctype"  : k.get('Target Type'),
    }

    display_comp = {
        MIN_AND_HIGH  : "x > {minval}",
        MAX_AND_LOW   : "x < {maxval}",
        MIN_MAX_RANGE : "{minval} < x < {maxval}",
    }.get(fmt_rec['ctype'], '*** ERR ***')

    fmt = "{target} {units} (" + display_comp + ")"
    return fmt.format(**fmt_rec) + "  ||| " + str(fmt_rec)


    

if __name__ == "__main__":
    print( "-" * 78 )
    kpis = read_kpis('Key+Performance+Indicators.txt')
    for k in kpis:
        print( format_kpi(k) )
    print( "-" * 78 )
