from utility_funcs.search import get_server_info, search_for_profile
import utility_funcs.logger_yaml as log
import argparse


def main(dispatch, log=log, config_file=None, queries_file=None, scenario_file=None):
    parser = argparse.ArgumentParser(description="This is an OTC tool for working with Jira projects.")
    connection_group=parser.add_argument_group(title="Connection control", description="About the connectionn to the server")
    connection_group.add_argument("-n", "--name", nargs='?', help="Alias for the target host" )
    connection_group.add_argument("-u", "--user", nargs='?', help="User Name (future)" )
    connection_group.add_argument("-p", "--password", nargs='?', help="Password (future)" )
    connection_group.add_argument("--scenario", nargs='?', help="Scenario to select", default='default')
    connection_group.add_argument("--query_set", nargs='?', help="Alternate query group name", default=None)
    project_group=parser.add_argument_group(title="Project control", description="Selecting which projects...")
    project_group.add_argument("--sproject", nargs='?', help="Jira source project")
    project_group.add_argument("--splatform", nargs='?', help="Jira source platform")
    project_group.add_argument("--sversion", nargs='?', help="Jira source android version")
    project_group.add_argument("--tplatform", nargs='?', help="Jira source platform")
    project_group.add_argument("--taversion", nargs='?', help="Android target version")
    project_group.add_argument("--tversion", nargs='?', help="Jira target android version")
    project_group.add_argument("--exists_on", nargs='?', help="Single value for Exists On field")
    project_group.add_argument("--update", default=None, action="store_true", help="Update target")
    project_group.add_argument("--rename", default=None, action="store_true", help="Rename source to target, if target is not found")
    project_group.add_argument("--verify", default=None, action="store_true", help="Verify target")
    parser.add_argument("--createmax", nargs='?', help="Max number of E-Features to create.",type=int)
    parser.add_argument("-c","--comment", nargs='?', help="Comment for created items.")
    parser.add_argument("-i","--input", nargs='?', help="Where to get the input.")
    parser.add_argument("-o","--output", nargs='?', help="Where to store the result.")
    parser.add_argument("-l", "--log_level", choices=['debug', 'info', 'warn', 'error', 'fatal'])

    parser.add_argument("command", default="e_feature_by_parent")

    args = parser.parse_args()

    # todo: Should be combined switches...
    if args.log_level is not None:
        log.logger.setLevel( log.logging.getLevelName(args.log_level.upper()))

    args.command = args.command.lower()

    try:
        scenario = get_server_info(args.scenario, scenario_file)    # possible FileNotFoundError
        if scenario is None:
            raise NameError("Can't locate scenario {scenario} in scenario file.".format_map(vars(args)))
        for switch in vars(args):
            # -- If the switch is set, it should override whatever in in scenario...
            value = getattr(args, switch, None)
            if value is not None:
                scenario[switch] = value
        # -- todo: *this* would be the place to set defaults...

    except FileNotFoundError as f:
        log.logger.fatal("Can't open scenarios file: %s"%f)
        exit(-1)
    except NameError as f:
        log.logger.fatal("Error in scenarios file: %s"%f)
        exit(-1)

    if 'log_level' in scenario:
        log.logger.setLevel(log.logging.getLevelName(scenario['log_level'].upper()))

    log.logger.info("Combined Switches: %s", scenario)

    try:
        config = get_server_info(scenario['name'], config_file)    # possible FileNotFoundError
    except FileNotFoundError as f:
        log.logger.fatal("Can't open configuration file: %s"%f)
        exit(-1)

    try:
        queries = get_server_info(scenario['name'], queries_file)   # possible FileNotFoundError
    except FileNotFoundError as f:
        log.logger.fatal("Can't open queries file: %s", f)
        exit(-1)

    errors = 0
    if config is None:
        errors = 1
        log.logger.fatal("Configuration section for server %s is missing." % (args.name))
        exit(-1)
    if 'username' not in config:
        errors += 1
        log.logger.fatal("username for server %s is missing." % (args.name))
    if 'password' not in config:
        errors += 1
        log.logger.fatal("password for server %s is missing." % (args.name))
    if 'host' not in config:
        errors += 1
        log.logger.fatal("host url for server %s is missing." % (args.name))
    if errors > 0:
        log.logger.fatal("configuration errors were found, exiting." )
        exit(-1)

    # --> Dispatch to action routine:
    dispatch(parser=parser, scenario=scenario, queries=queries, config=config,
               config_file=config_file, log=log)
    """
    command = scenario['command']
    log.logger.info("Application Starting! Comamnd='%s'" % command)

    if 'help' == command:
        parser.print_help()
    elif 'compare_priorities' == command:
        compare_priorities(parser, scenario, config, queries)
    elif 'dump_parents' == command:
        dump_parents(parser, scenario, config, queries)
    elif 'e_feature_scanner' == command:
        e_feature_scanner(parser, scenario, config, CONFIG_FILE, queries)
    elif 'scan_areq_for_preq' == command:
        scan_areq_and_check_for_preq(parser, scenario, config, queries)
    elif 'copy_platform_to_platform' == command:
        copy_platform_to_platform(parser, scenario, config, queries, CONFIG_FILE, log=log)
    elif 'add_label_to_platform_version' == command:
        add_label_to_platform_version(parser, scenario, config, queries, CONFIG_FILE, log=log)
    elif 'find_added_dng_vs_jira' == command:
        find_added_dng_vs_jira(parser, scenario, config, queries, CONFIG_FILE, log=log)
    elif 'areq_superceded_by_preq' == command:
        areq_superceded_by_preq(parser, scenario, config, queries, CONFIG_FILE, log=log)
    else:
        parser.print_help()
        exit(1)
    """

    log.logger.info( "Run completed." )
    return


