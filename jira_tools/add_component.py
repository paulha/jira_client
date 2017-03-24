#!/usr/bin/env python

import json
from jira.client import JIRA
import config
import sys

jira = JIRA(config.options, config.basic_auth)

# (source, detination)
reqs = [
('PREQ-23802','PREQ-24922'),
('PREQ-24319', 'PREQ-24703')
]

for req in reqs:
    # Print
    print areq[0] + " -> " + areq[1]
    source = jira.issue(areq[0])
    destination = jira.issue(areq[1])

    # Get Components
    all_components = []
    for component in source.fields.components:
        all_components.append({"name": component.name})

