#!/usr/bin/env python2.7

import pprint

import gojira

def main():
    j = gojira.init_jira()
    perms = j.my_permissions()
    pprint.pprint(perms)

    
if __name__ == "__main__":
    main()
