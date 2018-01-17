from jira_class import Jira, get_query
from navigate import *
import sys
from os.path import expanduser, pathsep, dirname, realpath
from jira_class import Jira
from jira.exceptions import JIRAError
import re
# -- todo: Uncomfortable for two different imports from the same module to be handled differently...
from utility_funcs.search import get_server_info, search_for_profile, search_for_file
import utility_funcs.logger_yaml as log
import argparse
import main

LOG_CONFIG_FILE = 'logging.yaml'+pathsep+dirname(realpath(sys.argv[0]))+'/logging.yaml'
CONFIG_FILE = dirname(realpath(sys.argv[0]))+'/config.yaml'+pathsep+'~/.jira/config.yaml'
QUERIES_FILE = dirname(realpath(sys.argv[0]))+'/queries.yaml'+pathsep+'~/.jira/queries.yaml'
SCENARIO_FILE = 'scenarios.yaml'+pathsep+dirname(realpath(sys.argv[0]))+'/scenarios.yaml'
log_file = log.logging.getLogger("file")

class E_Feature_by_Parent:
    def __init__(self, jira, parser=None, scenario=None, config=None, queries=None, search=None, log=None):
        self.jira = jira
        self.parser = parser
        self.scenario = scenario
        self.config = config
        self.queries = queries
        self.search = search
        self.log = log
        self.update = True if 'update' in scenario and scenario['update'] else False
        self.errors = 0
        self.updated = 0
        self.not_updated = 0
        self.considered = 0

    def scrub(self, key):
        return self.jira.strip_non_ascii(key)

    def get_features(self):
        feature_query = get_query('areq_feature_query', self.queries, E_Feature_by_Parent.__name__,
                                  params=self.scenario, log=self.log)
        return self.jira.do_query(feature_query)

    def get_e_features(self):
        e_feature_query = get_query('areq_e_feature_query', self.queries, E_Feature_by_Parent.__name__,
                                  params=self.scenario, log=self.log)
        return self.jira.do_query(e_feature_query)


def e_feature_by_parent(parser, scenario, config, queries, search, log=None):
    update = scenario['update']
    log.logger.info("Update is %s", update)
    log.logger.info("Marking AREQ items as superseded by PREQ item.")
    log.logger.info("=================================================================")

    updates = 0

    # -- Get and format it:
    jira = Jira(scenario['name'], search, log=log.logger)

    work = E_Feature_by_Parent(jira, parser, scenario, config, queries, search, log=log)
    parents = {work.scrub(parent.key): parent for parent in work.get_features()}
    all_children = [child for child in work.get_e_features()]
    children = [child for child in all_children
                if work.scrub(child.fields.parent.key) in parents]

    disagreement = [child for child in children
                    if work.scrub(child.fields.parent.key) in parents \
                        and "Kernel" not in [item.name for item in child.fields.components]]

    log.logger.info("Found %d Features to process", len(parents))
    log.logger.info("Found %d E-Features", len(all_children))
    log.logger.info("Found %d E-Features to process", len(children))
    log.logger.info("Found %d E-Features not set to Kernel", len(disagreement))

    log.logger.info("")
    log.logger.info("Feature Keys:")
    log.logger.info("")
    # (parents is a dict, so parent is just the key...)
    log.logger.info(", ".join([parent for parent in parents]))
    log.logger.info("")
    log.logger.info("E-Features to process:")
    log.logger.info("")
    log.logger.info(", ".join([child.key for child in children]))
    log.logger.info("")

    # --> Process the E-Features, setting classification to "Functional"
    """
        for e_feature in children:
        if target_preq.fields.issuetype.name not in ['E-Feature']:
            # -- (Can't add classification to E-Feature)
            classification_value = getattr(target_preq.fields, classification)
            classification_value = [v.value for v in classification_value]
            if classification_value is None or \
                    'Unassigned' in classification_value or \
                    'None' in classification_value:
                # -- Unconditional set:
                update_fields[classification] = [{'value': 'Functional Use Case'}]
            else:
                # -- Seems wrong to not catch this condition...
                #    FIXME: This is likely the wrong way to check this...
                if ['Functional Use Case'] != classification_value:
                    log.logger.warning("Item %s Classification was alreaady set to %s",
                                       target_preq.key, getattr(target_preq.fields, classification))
                    log.logger.warning("And is being overwritten")
                    update_fields[classification] = [{'value': 'Functional Use Case'}]

        if len(update_fields) > 0:
            if update:
                # -- only update if we're going to change something...
                log.logger.info("Updating %s with %s", target_preq.key,
                                {**update_fields, **assignee_fields, **lead_fields})
                target_preq.update(notify=False, fields=update_fields)

                try:
                    target_preq.update(notify=False, fields=assignee_fields)
                except JIRAError as e:
                    log.logger.error("Jira error %s", e)

                try:
                    target_preq.update(notify=False, fields=lead_fields)
                except JIRAError as e:
                    log.logger.error("Jira error %s", e)

                updated = True
            else:
                log.logger.info("NO UPDATE; SHOULD update %s with %s", target_preq.key, update_fields)
    """

    # --> Process Features, setting classification to "Functional"

    # -- Process the E-Features first (once we change the parent, we won't be able to find the child!)

    log.logger.info("-----------------------------------------------------------------")
    log.logger.info("%s items were updated ", updates)
    log.logger.info("")

    return


def dispatcher(parser=None, scenario=None, queries=None, config=None, config_file=None, log=log):
    # --> Dispatch to action routine:
    command = scenario['command']
    log.logger.info("Application Starting! Comamnd='%s'" % command)

    if 'help' == command:
        parser.print_help()
    elif 'e_feature_by_parent' == command:
        e_feature_by_parent(parser, scenario, config, queries, config_file, log=log)
    else:
        parser.print_help()
        exit(1)


if __name__ == "__main__":
    log.setup_logging(LOG_CONFIG_FILE, override={'handlers': {'info_file_handler': {'filename': 'set_e_feature_by_parent.log'}}})
    main.main(dispatcher, log=log, config_file=CONFIG_FILE, queries_file=QUERIES_FILE, scenario_file=SCENARIO_FILE)
    exit(0)
