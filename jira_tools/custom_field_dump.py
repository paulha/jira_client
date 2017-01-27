#!/bin/env python
import pprint

from jirafields import make_field_lookup
from gojira import init_jira, jql_issue_gen

def main():
    j = init_jira()
    fl = make_field_lookup(j)
    pprint.pprint(fl._reverse)


if __name__ == main():
    main()
