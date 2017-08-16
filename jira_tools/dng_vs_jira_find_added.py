import sys
from os.path import expanduser, pathsep, dirname, realpath
from openpyxl import load_workbook
from jira_class import Jira, get_query, remove_version_and_platform, strip_non_ascii
import re
from utility_funcs.search import search_for_file

class Utility:

    def _add_to_dict(self, dictionary, key, value, key_name=""):
        if key not in dictionary:
            dictionary[key] = value
        else:
            if key_name not in dictionary[key]['duplicates']:
                dictionary[key]['duplicates'][key_name] = []
            dictionary[key]['duplicates'][key_name].append(value)
            raise KeyError("Duplicate key: '%s': %s" % (key, dictionary[key]))

    def _gather_duplications(self, dictionary, key_name=""):
        return [entry for key, entry in dictionary.items()
                if key_name in entry['duplicates'] and len(entry['duplicates'][key_name]) > 0]

    def add_match(self, this_item, matching_item, key_name):
        matched_by = this_item['matchedby']
        if not key_name in matched_by:
            matched_by[key_name] = []
        this_item[key_name].append(matching_item)


class DNG_File (Utility):
    SUMMARY = 1
    DESCRIPTION = 6

    def __init__(self, filename=None, log=None):
        self.workbook = None
        self.entries = []
        self.dng_by_summary = {}
        self.dng_by_description = {}

        if isinstance(filename, str):
            self.read(filename, log=log)

    def _empty_entry(self):
        return {
            'lineno':       None,
            'summary':      None,
            'description':  None,
            'row':          None,
            'matchedby':    {},
            'duplicates':   {},
        }

    def gather_summary_duplications(self):
        return self._gather_duplications(self.dng_by_summary, "summary")

    def gather_description_duplications(self):
        return self._gather_duplications(self.dng_by_description, "description")

    def read(self, filename, log=None):
        self.workbook = load_workbook(filename)
        sheet1 = self.workbook['Sheet1']
        for row in range(2, sheet1.max_row):
            this_row = sheet1[row]
            entry = self._empty_entry()
            entry['lineno'] = row
            entry['summary'] = this_row[self.SUMMARY].value
            entry['description'] = this_row[self.DESCRIPTION].value
            entry['row'] = this_row
            self.entries.append(entry)
            try:
                self._add_to_dict(self.dng_by_summary, entry['summary'], entry, "summary")
            except KeyError as e:
                pass
                # log.logger.warning("%s", e)

            try:
                self._add_to_dict(self.dng_by_description, entry['description'], entry, "description")
            except KeyError as e:
                pass
                # log.logger.warning("%s", e)

    def get_entries(self):
        return self.entries

class Jira_Project (Jira, Utility):

    def __init__(self, server_alias, config_path, log=None):
        self.items = None
        self.items_by_key = {}
        self.items_by_summary = {}
        self.items_by_description = {}

        super().__init__(server_alias, config_path, log)

    def _empty_item(self):
        return {
            'key':          None,
            'summary':      None,
            'description':  None,
            'item':         None,
            'matchedby':    {},
            'duplicates':   {},
        }

    def gather_key_duplications(self):
        return self._gather_duplications(self.items_by_key, "key")

    def gather_summary_duplications(self):
        return self._gather_duplications(self.items_by_summary, "summary")

    def gather_description_duplications(self):
        return self._gather_duplications(self.items_by_description, "description")

    def read(self, query, log=None):
        self.items = []
        for item in self.do_query(query):
            new_item = self._empty_item()
            new_item['key'] = item.key
            new_item['summary'] = strip_non_ascii(remove_version_and_platform(item.fields.summary))
            new_item['description'] = strip_non_ascii(item.fields.description)
            new_item['item'] = item
            self.items.append(new_item)
            try:
                self._add_to_dict(self.items_by_key, new_item['key'], new_item, "key")
            except KeyError as e:
                pass
                # log.logger.warning("%s", e)

            try:
                self._add_to_dict(self.items_by_summary, new_item['summary'], new_item, "summary")
            except KeyError as e:
                pass
                # log.logger.warning("%s", e)

            try:
                self._add_to_dict(self.items_by_description, new_item['description'], new_item, "description")
            except KeyError as e:
                pass
                # log.logger.warning("%s", e)



def find_added_dng_vs_jira(parser, scenario, config, queries, search, log=None):
    """Scan DNG input, label Jira entries and Note DNG items not in Jira"""

    preq_source_query = get_query('preq_source_query', queries, find_added_dng_vs_jira.__name__, params=scenario, log=log)

    verify = scenario['verify']
    update = scenario['update']
    log.logger.info("Verify is %s and Update is %s", verify, update)
    log.logger.info("=================================================================")

    XLS_FILE = realpath(dirname(realpath(sys.argv[0])) + '/../KSL-I Android.xlsx')
    dng = DNG_File(XLS_FILE, log=log)

    def display_duplications(title, id_key_field, index_field_name, dictionary):
        if len(dictionary) > 0:
            log.logger.warning("")
            log.logger.warning(title)
            log.logger.warning("")
            log.logger.warning("=====================================================================================")
            for item in dictionary:
                dups = [item[id_key_field]]
                for k,d in item['duplicates'].items():
                    for entry in d:
                        dups.append(entry[id_key_field])
                log.logger.warning("Rows %s duplicate %s: %-80s", dups, index_field_name, "'" + item[index_field_name] + "'")

    summary_duplications = dng.gather_summary_duplications()
    display_duplications("Duplications of summary were found in the input worksheet:",
                         "lineno", "summary", summary_duplications)
    description_duplications = dng.gather_description_duplications()
    display_duplications("Duplications of summary were found in the input worksheet:",
                         "lineno", "description", description_duplications)

    # -- Open Jira:
    # jira = Jira(scenario['name'], search, log=log.logger)
    # jira_list = [item for item in jira.do_query(preq_source_query)]

    jira = Jira_Project(scenario['name'], search, log=log.logger)
    jira.read(preq_source_query)
    log.logger.info("Read %d jira entries", len(jira.items))

    jira_key_duplications = jira.gather_key_duplications()
    display_duplications("Duplications of Jira Keys were found in the input project:",
                         "key", "key", jira_key_duplications)

    jira_summary_duplications = jira.gather_summary_duplications()
    display_duplications("Duplications of Jira Summaries were found in the input project:",
                         "key", "summary", jira_summary_duplications)

    jira_description_duplications = jira.gather_description_duplications()
    display_duplications("Duplications of Jira Descriptions were found in the input project:",
                         "key", "description", jira_description_duplications)

    for dng_item in dng.get_entries():
        match_found = False
        if dng_item['summary'] in jira.items_by_summary:
            # found a match!
            jira_item = jira.items_by_summary[dng_item['summary']]
            dng.add_match(dng_item, jira_item, "summary")
            jira.add_match(jira_item, dng_item, "summary")
            log.logger.info("Found a summary match %s to DNG %s", jira_item['key'], dng_item['row'][0].value)
            match_found = True

        if dng_item['description'] in jira.items_by_description:
            # found a match!
            jira_item = jira.items_by_description[dng_item['description']]
            dng.add_match(dng_item, jira_item, "description")
            jira.add_match(jira_item, dng_item, "description")
            log.logger.info("Found a description match %s to DNG %s", jira_item['key'], dng_item['row'][0].value)
            match_found = True

        if not match_found:
            log.logger.info("NO MATCH FOUND -- DNG item: %d: %s", dng_item['row'][0].value, dng_item['row'][1].value)

    source_preq_scanned = 0
    source_areq_scanned = 0
    ucis_created = 0
    e_features_created = 0
    warnings_issued = 0
    verify_failures = 0
    update_failures = 0
    processing_errors = 0

    update_count = 0


    log.logger.info("-----------------------------------------------------------------")
    log.logger.info("%s UCIS source entries were considered. ", source_preq_scanned)
    log.logger.info("%s target UCIS entries were created. ", ucis_created)
    log.logger.info("%s E-Feature source entries were considered. ", source_areq_scanned)
    log.logger.info("%s target E-Features entries were created. ", e_features_created)
    log.logger.info("%s warnings were issued. ", warnings_issued)
    log.logger.info("")

    log.logger.info("%s processing error(s). ", processing_errors)
