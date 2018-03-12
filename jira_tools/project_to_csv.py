from jira_class import Jira, get_query


class ProjectToCSV:
    def __init__(self, parser, scenario, config, queries, search, log=None, jira=None):
        self.parser = parser
        self.jira = jira
        self.scenario = scenario
        self.config = config
        self.queries = queries
        self.search = search
        self.logger = log.logger
        self.update_count = 0
        self.added_count = 0
        self.createmax = self.scenario['createmax'] if 'createmax' in self.scenario else 0
        self.verify = self.scenario['verify'] if 'verify' in self.scenario else False
        self.update = self.scenario['update'] if 'update' in self.scenario else False

        # -- Authenticate to Jira server
        self.jira = Jira(self.scenario['name'], self.search, self.logger)
        pass

    def run(self):
        """Iterate platforms, then items found by platform query"""

        for key, platform in self.scenario['platforms'].items():
            self.logger.info(f"Processing {platform['splatform']}")
            query_values = {
                'sproject': '"'+platform['sproject']+'"',
                'splatform': '"'+platform['splatform']+'"',
                'sversion': platform['sversion']
            }
            field_list = platform['fields']

            items_query = get_query('items_query', self.queries, __name__, params=query_values, log=self.logger)
            # items_query = items_query.format_map(query_values)

            with open(platform['splatform'] + '.csv', local_mode) as f:
                f.write(f"{platform['splatform']}\n")
                f.write(f"\n")
                item_count = 0
                print(f"{platform['splatform']},")
                print(",")

                for item in self.jira.do_query(items_query):
                    value_list = []
                    for field_name in field_list:
                        if hasattr(item, field_name):
                            local_value = getattr(item, field_name)
                        elif hasattr(item.fields, field_name):
                            local_value = getattr(item.fields, field_name)
                        else:
                            local_name = self.jira.get_field_name(field_name)
                            if hasattr(item, local_name):
                                local_value = getattr(item, local_name)
                            elif hasattr(item.fields, local_name):
                                local_value = getattr(item.fields, local_name)
                            else:
                                local_value = None

                        value_list.append(local_value)

                    result = ",".join(value_list)

                    f.write(f"{result}\n")
                    item_count += 1

            self.logger.info(f"{item_count} entries written to {platform['splatform']}")

