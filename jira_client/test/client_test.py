from jira_client import Jira
import urllib3
import sys
from os.path import dirname, realpath, pathsep
import unittest
import yaml as yaml
import utility_funcs.logger_yaml as log

JIRA_CONFIG_PATH = f"{dirname(realpath(sys.argv[0]))}/config.yaml{pathsep}~/.jira/config.yaml"

class MyTestCase(unittest.TestCase):
    environment = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        log.setup_logging()
        config = None
        try:
            with open("environments.yaml", "r") as f:
                config = yaml.load(f)
        except FileNotFoundError as nf:
            log.logger.error("File 'environments.yaml' not found %s", nf)
            exit(-1)

        command = 'test'

        if command not in config:
            log.logger.error(f"configuration '{sys.argv[1]}' was not found")
            exit(-1)

        cls.environment = config['test']

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_open_jira(self):
        urllib3.disable_warnings()
        jira = Jira(self.environment['jira_server'], JIRA_CONFIG_PATH, log=log.logger)
        self.assertIsNotNone(jira, "Jira client returned None, and should not.")


if __name__ == '__main__':
    unittest.main()
