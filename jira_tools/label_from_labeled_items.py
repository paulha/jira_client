from jira_class import Jira, get_query
from re import search


class LabelFromLabeledItems:

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

    def update_labels_field(self, target_preq, target_field="Label", delete_labels=[], add_labels=[]):
        updated = False
        delete_list = [x for x in self.scenario['delete_labels']] \
            if 'delete_labels' in self.scenario else delete_labels.copy()
        add_list = [x for x in self.scenario['add_labels']] \
            if 'add_labels' in self.scenario else add_labels.copy()

        label_field_name = self.jira.get_field_name(target_field)
        label_field = getattr(target_preq.fields, label_field_name)

        result_labels = {x: x for x in label_field} if isinstance(label_field, list) else {}
        original_labels = result_labels.copy()

        # -- Remove labels in delete list from source_labels:
        for regex in delete_list:
            for key, item in result_labels.copy().items():
                if search(regex, item):
                    self.logger.info("Removing label %s (found by regex '%s') from item %s",
                                     key, regex, target_preq.key)
                    del result_labels[key]

        # -- amd insert those in the add list:
        for label in add_list:
            self.logger.info("Adding label %s to item %s", label, target_preq.key)
            result_labels[label] = label

        if result_labels != original_labels:
            update_fields = {'labels': [key for key, item in result_labels.items()]}
            comment_text = ("The Label on %s was updated from %s to %s by {command}.\n" +
                            "\n" +
                            "%s").format_map(self.scenario) \
                           % (target_preq.key,
                              [key for key,value in original_labels.items()],
                              [key for key, value in result_labels.items()],
                              self.scenario['comment'] if self.scenario['comment'] is not None else "")
            if self.update:
                # -- only update if we're going to change something...
                self.logger.info("Updating %s with %s, was %s", target_preq.key,
                                 [key for key, value in result_labels.items()],
                                 [key for key,value in original_labels.items()])
                target_preq.update(notify=False, fields=update_fields)
                self.jira.jira_client.add_comment(target_preq, comment_text)
                updated = True
            else:
                self.logger.info("%s: NO LABEL UPDATE; labels change from from %s, to %s; Comment would be\n%s",
                                 target_preq.key,
                                 [key for key,value in original_labels.items()],
                                 [key for key, value in result_labels.items()],
                                 comment_text)

        if updated:
            self.update_count += 1

        return self.update_count

    def label_from_labeled_items(self):
        """Find the labeled AREQ items and add the label to corresponding target items"""

        self.logger.info("Labeling target platform {tplatform}, source android version {tversion} with {tlabel}".
                         format_map(self.scenario))

        self.logger.info("Update is %s", self.update)
        self.logger.info("=================================================================")

        # -- Query to get the list of source items with the target label
        items_with_label_query = get_query('items_with_label_query', self.queries,
                                           LabelFromLabeledItems.label_from_labeled_items.__name__,
                                           params=self.scenario, log=self.logger)
        items_with_label_query = items_with_label_query.format_map(self.scenario)
        # items_with_label_list = [item for item in self.jira.do_query(items_with_label_query)]
        # -- Note: parent Feature could occur 1 or more times. (Also zero, but that doesn't matter in this case)
        by_parent_key = {item.fields.parent.key: item for item in self.jira.do_query(items_with_label_query)}

        # -- Query to get the (total) list of potential targets
        targets_for_label_query = get_query('targets_for_label_query', self.queries,
                                            LabelFromLabeledItems.label_from_labeled_items.__name__,
                                            params=self.scenario, log=self.logger)
        targets_for_label_query = targets_for_label_query.format_map(self.scenario)
        target_item_list = [item for item in self.jira.do_query(targets_for_label_query)]

        # -- Build a list of E-Features that share a parent Feature that's labeled in the source query
        target_items_with_same_parent = [item for item in target_item_list if item.fields.parent.key in by_parent_key]
        for target in target_items_with_same_parent:
            self.update_labels_field(target, target_field="Labels", add_labels=[self.scenario['tlabel']])
            if self.createmax and self.update_count >= self.createmax:
                break

        self.logger.info("-----------------------------------------------------------------")
        self.logger.info("%s E-Feature labels were updated. ", self.update_count)
        self.logger.info("")

