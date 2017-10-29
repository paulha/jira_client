from jira.exceptions import JIRAError

class State:
    def __init__(self, name, to_label):
        self.name = name
        self.to_label = to_label

    def __str__(self):
        return self.name


Open = 'Open'
In_Progress = 'In Progress'
Close = 'Close'
# Closed = 'Closed'
# Merge = 'Merge'
Merged = 'Merged'
Reject = 'Reject'
# Rejected = 'Rejected'
Blocked = 'Blocked'
New = 'New'
In_Review = 'In Review'
Candidate = 'Candidate'
Deprecated = 'Deprecated'

aliases = {
    'Start Progress': In_Progress,
    'To Blocked': Blocked,
    'Closed': Close,
    'To Close': Close,
    'Merge': Merged,
    'Open': Open,
    'Reopen': Open,
    'Reopened': Open,
    'To Open': Open,
    'Reject': Reject,
    'Rejected': Reject,
}


def normalize(name):
    if name in aliases:
        name = aliases[name]
    return name


E_Feature_Open = State(Open, [Open, In_Progress])
E_Feature_Close = State(Close, [Close])
E_Feature_Reject = State(Reject, [Reject])
E_Feature_Start_Progress = State(In_Progress, [In_Progress])
E_Feature_In_Progress = State(In_Progress, [In_Progress])
E_Feature_Blocked = State(Blocked, [Blocked])
E_Feature_Merge = State(Merged, [Merged])
E_Feature_Reopen = State(Open, [Open])

Feature_In_Review = State(In_Review, [In_Review])
Feature_Blocked = State(Blocked, [Blocked])
Feature_New = State(New, [New])
Feature_Reject = State(Reject, [Reject])
Feature_Candidate = State(Candidate, [Candidate])
Feature_Deprecated = State(Deprecated, [Deprecated])

UCIS_Open = State(Open, [Open])
UCIS_Start_Progress = State(In_Progress, [In_Progress])
UCIS_Reject = State(Reject, [Reject])
UCIS_Blocked = State(Blocked, [Blocked])
UCIS_Merged = State(Merged, [Merged])
UCIS_Close = State(Close, [Close])
# UCIS_Edit_Closed_Issue = State("Edit Closed Issues", ["Edit Closed Issues"])


Feature_Targets = {
    (New, New): [],
    (New, Blocked): [Feature_Blocked],
    (New, Reject): [Feature_Reject],
    (New, In_Review): [Feature_In_Review],
    (New, Candidate): [Feature_In_Review, Feature_Candidate],
    (New, Deprecated): [Feature_In_Review, Feature_Candidate, Feature_Deprecated],

    (Blocked, New): [Feature_New],
    (Blocked, Blocked): [Feature_Blocked],
    (Blocked, Reject): [Feature_Reject],
    (Blocked, In_Review): [Feature_In_Review],
    (Blocked, Candidate): [Feature_In_Review, Feature_Candidate],
    (Blocked, Deprecated): [Feature_In_Review, Feature_Candidate, Feature_Deprecated],

    (Reject, New): [Feature_New],
    (Reject, Blocked): [Feature_Blocked],
    (Reject, Reject): [],
    (Reject, In_Review): [Feature_In_Review],
    (Reject, Candidate): [Feature_In_Review, Feature_Candidate],
    (Reject, Deprecated): [Feature_In_Review, Feature_Candidate, Feature_Deprecated],

    (In_Review, New): [Feature_New],
    (In_Review, Blocked): [Feature_Blocked],
    (In_Review, Reject): [Feature_Reject],
    (In_Review, In_Review): [],
    (In_Review, Candidate): [Feature_Candidate],
    (In_Review, Deprecated): [Feature_Candidate, Feature_Deprecated],

    (Candidate, New): [Feature_In_Review, Feature_New],
    (Candidate, Blocked): [Feature_In_Review, Feature_Blocked],
    (Candidate, Reject): [Feature_In_Review, Feature_Reject],
    (Candidate, In_Review): [Feature_In_Review],
    (Candidate, Candidate): [],
    (Candidate, Deprecated): [Feature_Deprecated],

    (Deprecated, New): [Feature_Candidate, Feature_In_Review, Feature_New],
    (Deprecated, Blocked): [Feature_Candidate, Feature_In_Review, Feature_Blocked],
    (Deprecated, Reject): [Feature_Candidate, Feature_In_Review, Feature_Reject],
    (Deprecated, In_Review): [Feature_Candidate, Feature_In_Review],
    (Deprecated, Candidate): [Feature_Candidate],
    (Deprecated, Deprecated): [],
}

E_Feature_Targets = {
    (Open, Open): [],
    (Open, Close): [E_Feature_In_Progress, E_Feature_Merge, E_Feature_Close],
    (Open, Merged): [E_Feature_In_Progress, E_Feature_Merge],
    (Open, Reject): [E_Feature_Reject],
    (Open, In_Progress): [E_Feature_In_Progress],
    (Open, Blocked): [E_Feature_In_Progress, E_Feature_Blocked],

    (In_Progress, Open): [E_Feature_Merge, E_Feature_Close, E_Feature_Open],
    (In_Progress, Close): [E_Feature_Merge, E_Feature_Close],
    (In_Progress, Merged): [E_Feature_Merge],
    (In_Progress, Reject): [E_Feature_Reject],
    (In_Progress, In_Progress): [],
    (In_Progress, Blocked): [E_Feature_Blocked],

    (Blocked, Open): [E_Feature_Merge, E_Feature_Close, E_Feature_Open],
    (Blocked, Close): [E_Feature_Merge, E_Feature_Close],
    (Blocked, Merged): [E_Feature_Merge],
    (Blocked, Reject): [E_Feature_Reject],
    (Blocked, In_Progress): [E_Feature_In_Progress],
    (Blocked, Blocked): [],

    (Merged, Open): [E_Feature_Close, E_Feature_Open],
    (Merged, Close): [E_Feature_Close],
    (Merged, Merged): [],
    (Merged, Reject): [E_Feature_Reject],
    (Merged, In_Progress): [E_Feature_In_Progress],
    (Merged, Blocked): [E_Feature_In_Progress, E_Feature_Blocked],

    (Reject, Open): [E_Feature_Open],
    (Reject, Close): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Merge, E_Feature_Close],
    (Reject, Merged): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Merge],
    (Reject, Reject): [],
    (Reject, In_Progress): [E_Feature_Open, E_Feature_In_Progress],
    (Reject, Blocked): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Blocked],

    (Close, Open): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Merge, E_Feature_Close],
    (Close, Close): [],
    (Close, Merged): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Merge],
    (Close, Reject): [E_Feature_Open, E_Feature_Reject],
    (Close, In_Progress): [E_Feature_Open, E_Feature_In_Progress],
    (Close, Blocked): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Blocked],
}

UCIS_Targets = {
    (Open, Open): [],
    (Open, In_Progress): [UCIS_Start_Progress],
    (Open, Reject): [UCIS_Reject],
    (Open, Blocked): [UCIS_Start_Progress, UCIS_Blocked],
    (Open, Merged): [UCIS_Start_Progress, UCIS_Merged],
    (Open, Close): [UCIS_Start_Progress, UCIS_Merged, UCIS_Close],

    (In_Progress, Open): [UCIS_Reject, UCIS_Open],
    (In_Progress, In_Progress): [],
    (In_Progress, Reject): [UCIS_Reject],
    (In_Progress, Blocked): [UCIS_Blocked],
    (In_Progress, Merged): [UCIS_Merged],
    (In_Progress, Close): [UCIS_Merged, UCIS_Close],

    (Reject, Open): [UCIS_Open],
    (Reject, In_Progress): [UCIS_Open, UCIS_Start_Progress],
    (Reject, Reject): [],
    (Reject, Blocked): [UCIS_Open, UCIS_Start_Progress, UCIS_Blocked],
    (Reject, Merged): [UCIS_Open, UCIS_Start_Progress, UCIS_Merged],
    (Reject, Close): [UCIS_Open, UCIS_Start_Progress, UCIS_Merged, UCIS_Close],

    (Blocked, Open): [UCIS_Reject, UCIS_Open],
    (Blocked, In_Progress): [UCIS_Start_Progress],
    (Blocked, Reject): [UCIS_Reject],
    (Blocked, Blocked): [],
    (Blocked, Merged): [UCIS_Merged],
    (Blocked, Close): [UCIS_Merged, UCIS_Close],

    (Merged, Open): [UCIS_Reject, UCIS_Open],
    (Merged, In_Progress): [UCIS_Start_Progress],
    (Merged, Reject): [UCIS_Reject],
    (Merged, Blocked): [UCIS_Start_Progress, UCIS_Blocked],
    (Merged, Merged): [],
    (Merged, Close): [UCIS_Close],

    (Close, Open): [UCIS_Open],
    (Close, In_Progress): [UCIS_Open, UCIS_Start_Progress],
    (Close, Reject): [UCIS_Reject],
    (Close, Blocked): [UCIS_Open, UCIS_Start_Progress, UCIS_Blocked],
    (Close, Merged): [UCIS_Open, UCIS_Start_Progress, UCIS_Merged],
    (Close, Close): [],

}

TypeToStateMap = {
    'UCIS': UCIS_Targets,
    'Feature': Feature_Targets,
    'E-Feature': E_Feature_Targets
}


def transition_to_state(jira, item, goal, log=None):
    # -- TODO: In addition to flagging an error when the desired state is not achieved,
    # -- TODO: Add a comment stating both the intended and actual state!
    if item.fields.issuetype.name in TypeToStateMap:
        transition_map = TypeToStateMap[item.fields.issuetype.name]
    else:
        log.logger.error("Unable to match item type '%s' to a transition category", item.fields.issuetype.name)

    state_pair = (normalize(item.fields.status.name), normalize(goal.name))
    if state_pair in transition_map:
        state_list = transition_map[state_pair]
    else:
        state_list = None
        log.logger.error("Unable to match start and end status '%s' to transition list for %s",
                         state_pair, item.fields.issuetype.name)

    if state_list is None:
        log.logger.error("Could not find map to goal: Target %s is at %s, goal is %s",
                         item.key, item.fields.status.name, goal.name)
        return False
    else:
        log.logger.info("Target is at %s, goal is %s, expected transitions are %s",
                        item.fields.status.name, goal.name, [item.name for item in state_list])
        for state in state_list:
            available_transitions = {normalize(item['name']): item['id'] for item in jira.jira_client.transitions(item)}
            next_id = None
            for name in state.to_label:
                if name in available_transitions:
                    next_id = available_transitions[name]

            if next_id is not None:
                log.logger.info("Attempt transition from %s, to %s",
                                item.fields.status.name, name)
                try:
                    jira.jira_client.transition_issue(item, next_id)
                    item = jira.jira_client.issue(item.key)
                except JIRAError as j:
                    log.logger.error("JIRA error occured: %s", j.__str__())

                # -- abort if transition is not successful!
                if normalize(item.fields.status.name) != normalize(state.name):
                    log.logger.error("Status for %s did not transition correctly. Should have been '%s' and is '%s'. %s",
                                     item.key, state.name, item.fields.status.name, available_transitions)
                    break
            else:
                log.logger.error("In pair %s Target state '%s' for '%s' not found in available transitions: %s",
                                 state_pair, name, item.fields.issuetype.name, available_transitions)
        log.logger.info("Final status is %s", item.fields.status.name)

        if normalize(item.fields.status.name) != normalize(goal.name):
            log.logger.error("Status for %s was not set correctly. Should have been '%s' and is '%s'",
                             item.key, goal.name, item.fields.status.name)
    return True if state_list else False
