import sys
from os.path import expanduser, pathsep, dirname, realpath
from openpyxl import load_workbook
from jira_class import Jira
import re
from utility_funcs.search import search_for_file

def find_added_dng_vs_jira(parser, scenario, config, queries, search, log=None):
    """Scan DNG input, label Jira entries and Note DNG items not in Jira"""

    # preq_source_query = get_query('preq_source_query', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    # preq_target_query = get_query('preq_target_query', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    # areq_source_e_feature_query = get_query('areq_source_e_feature', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    # areq_target_e_feature_query = get_query('areq_target_e_feature', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    # target_feature_query = get_query('target_feature_query', queries, copy_platform_to_platform.__name__, params=scenario, log=log)
    # target_summary_format = get_query('target_summary_format', queries, copy_platform_to_platform.__name__, params=scenario, log=log)

    # log.logger.info("Examining source platform {splatform}, source android version {sversion}, target android version {tversion}".format_map(scenario))

    verify = scenario['verify']
    update = scenario['update']
    log.logger.info("Verify is %s and Update is %s", verify, update)
    log.logger.info("=================================================================")

    XLS_FILE = realpath(dirname(realpath(sys.argv[0])) + '/../KSL-I Android.xlsx')
    work_book = load_workbook(XLS_FILE)
    sheet1 = work_book['Sheet1']
    SUMMARY = 1
    DESCRIPTION = 6

    dng_by_summary = {}
    dng_by_description = {}
    line = 1
    for row in sheet1:
        summary = row[SUMMARY].value
        if summary not in dng_by_summary:
            dng_by_summary[summary] = row
        else:
            log.logger.warning("%d: Duplicate row summary at: %s", line, summary)

        description = row[DESCRIPTION].value
        if description not in dng_by_description:
            dng_by_description[description] = row
        else:
            log.logger.warning("%d: Duplicate row description: %s", line, description)
        line += 1

    # -- Open Jira:
    jira = Jira(scenario['name'], search, log=log.logger)


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
