from jira.exceptions import JIRAError
from jira.resources import Issue

class State:
    def __init__(self, name: str, to_label: list):
        self.name = name
        self.to_label = to_label

    def __str__(self):
        return self.name


Open = 'Open'
In_Progress = 'In Progress'
Closed = 'Closed'
Merged = 'Merged'
Rejected = 'Rejected'
Blocked = 'Blocked'
New = 'New'
In_Review = 'In Review'
Candidate = 'Candidate'
Deprecated = 'Deprecated'

aliases = {
    'Start Progress': In_Progress,
    'To Blocked': Blocked,
    'Close': Closed,
    'Closed': Closed,
    'To Close': Closed,
    'Close Issue': Closed,
    'Merge': Merged,
    'To Merged': Merged,
    'Open': Open,
    'Reopen': Open,
    'Reopened': Open,
    'To Reopened': Open,
    'To Open': Open,
    'Reject': Rejected,
    'Rejected': Rejected,
    'To Rejected': Rejected,
}


def normalize(name):
    if name in aliases:
        name = aliases[name]
    return name


def get(scenario, map_name):
    if map_name in scenario:
        map = {normalize(key): normalize(value) for key, value in scenario[map_name].items()}
    else:
        map = {}
    return map


E_Feature_New = State(New, [New])
E_Feature_Open = State(Open, [Open])
E_Feature_Close = State(Closed, [Closed])
E_Feature_Rejected = State(Rejected, [Rejected])
E_Feature_Start_Progress = State(In_Progress, [In_Progress])
E_Feature_In_Progress = State(In_Progress, [In_Progress])
E_Feature_Blocked = State(Blocked, [Blocked])
E_Feature_Merge = State(Merged, [Merged])
E_Feature_Reopen = State(Open, [Open])

Feature_In_Review = State(In_Review, [In_Review])
Feature_Blocked = State(Blocked, [Blocked])
Feature_New = State(New, [New])
Feature_Rejected = State(Rejected, [Rejected])
Feature_Candidate = State(Candidate, [Candidate])
Feature_Deprecated = State(Deprecated, [Deprecated])

UCIS_Open = State(Open, [Open])
UCIS_In_Progress = State(In_Progress, [In_Progress])
UCIS_Reject = State(Rejected, [Rejected])
UCIS_Blocked = State(Blocked, [Blocked])
UCIS_Merged = State(Merged, [Merged])
UCIS_Close = State(Closed, [Closed])


Feature_Targets = {
    (New, New): [],
    (New, Blocked): [Feature_Blocked],
    (New, Rejected): [Feature_Rejected],
    (New, In_Review): [Feature_In_Review],
    (New, Candidate): [Feature_In_Review, Feature_Candidate],
    (New, Deprecated): [Feature_In_Review, Feature_Candidate, Feature_Deprecated],

    (Blocked, New): [Feature_New],
    (Blocked, Blocked): [],
    (Blocked, Rejected): [Feature_Rejected],
    (Blocked, In_Review): [Feature_In_Review],
    (Blocked, Candidate): [Feature_In_Review, Feature_Candidate],
    (Blocked, Deprecated): [Feature_In_Review, Feature_Candidate, Feature_Deprecated],

    (Rejected, New): [Feature_New],
    (Rejected, Blocked): [Feature_Blocked],
    (Rejected, Rejected): [],
    (Rejected, In_Review): [Feature_In_Review],
    (Rejected, Candidate): [Feature_In_Review, Feature_Candidate],
    (Rejected, Deprecated): [Feature_In_Review, Feature_Candidate, Feature_Deprecated],

    (In_Review, New): [Feature_New],
    (In_Review, Blocked): [Feature_Blocked],
    (In_Review, Rejected): [Feature_Rejected],
    (In_Review, In_Review): [],
    (In_Review, Candidate): [Feature_Candidate],
    (In_Review, Deprecated): [Feature_Candidate, Feature_Deprecated],

    (Candidate, New): [Feature_In_Review, Feature_New],
    (Candidate, Blocked): [Feature_In_Review, Feature_Blocked],
    (Candidate, Rejected): [Feature_In_Review, Feature_Rejected],
    (Candidate, In_Review): [Feature_In_Review],
    (Candidate, Candidate): [],
    (Candidate, Deprecated): [Feature_Deprecated],

    (Deprecated, New): [Feature_Candidate, Feature_In_Review, Feature_New],
    (Deprecated, Blocked): [Feature_Candidate, Feature_In_Review, Feature_Blocked],
    (Deprecated, Rejected): [Feature_Candidate, Feature_In_Review, Feature_Rejected],
    (Deprecated, In_Review): [Feature_Candidate, Feature_In_Review],
    (Deprecated, Candidate): [Feature_Candidate],
    (Deprecated, Deprecated): [],
}

E_Feature_Targets = {
    (Open, Open): [],
    (Open, Closed): [E_Feature_In_Progress, E_Feature_Merge, E_Feature_Close],
    (Open, Merged): [E_Feature_In_Progress, E_Feature_Merge],
    (Open, Rejected): [E_Feature_Rejected],
    (Open, In_Progress): [E_Feature_In_Progress],
    (Open, Blocked): [E_Feature_In_Progress, E_Feature_Blocked],

    (In_Progress, Open): [E_Feature_Rejected, E_Feature_Open],
    (In_Progress, Closed): [E_Feature_Merge, E_Feature_Close],
    (In_Progress, Merged): [E_Feature_Merge],
    (In_Progress, Rejected): [E_Feature_Rejected],
    (In_Progress, In_Progress): [],
    (In_Progress, Blocked): [E_Feature_Blocked],

    (Blocked, Open): [E_Feature_Rejected, E_Feature_Open],
    (Blocked, Closed): [E_Feature_Merge, E_Feature_Close],
    (Blocked, Merged): [E_Feature_Merge],
    (Blocked, Rejected): [E_Feature_Rejected],
    (Blocked, In_Progress): [E_Feature_In_Progress],
    (Blocked, Blocked): [],

    (Merged, Open): [E_Feature_Rejected, E_Feature_Open],
    (Merged, Closed): [E_Feature_Close],
    (Merged, Merged): [],
    (Merged, Rejected): [E_Feature_Rejected],
    (Merged, In_Progress): [E_Feature_Rejected, E_Feature_Open, E_Feature_In_Progress],
    (Merged, Blocked): [E_Feature_Rejected, E_Feature_Open, E_Feature_In_Progress, E_Feature_Blocked],

    (Rejected, Open): [E_Feature_Open],
    (Rejected, Closed): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Merge, E_Feature_Close],
    (Rejected, Merged): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Merge],
    (Rejected, Rejected): [],
    (Rejected, In_Progress): [E_Feature_Open, E_Feature_In_Progress],
    (Rejected, Blocked): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Blocked],

    (Closed, Open): [E_Feature_Rejected, E_Feature_Open],
    (Closed, Closed): [],
    (Closed, Merged): [E_Feature_Rejected, E_Feature_Open, E_Feature_In_Progress, E_Feature_Merge],
    (Closed, Rejected): [E_Feature_Rejected],
    (Closed, In_Progress): [E_Feature_Rejected, E_Feature_Open, E_Feature_In_Progress],
    (Closed, Blocked): [E_Feature_Rejected, E_Feature_Open, E_Feature_In_Progress, E_Feature_Blocked],
}

UCIS_Targets = {
    (Open, Open): [],
    (Open, In_Progress): [UCIS_In_Progress],
    (Open, Rejected): [UCIS_Reject],
    (Open, Blocked): [UCIS_In_Progress, UCIS_Blocked],
    (Open, Merged): [UCIS_In_Progress, UCIS_Merged],
    (Open, Closed): [UCIS_In_Progress, UCIS_Merged, UCIS_Close],

    (In_Progress, Open): [UCIS_Reject, UCIS_Open],
    (In_Progress, In_Progress): [],
    (In_Progress, Rejected): [UCIS_Reject],
    (In_Progress, Blocked): [UCIS_Blocked],
    (In_Progress, Merged): [UCIS_Merged],
    (In_Progress, Closed): [UCIS_Merged, UCIS_Close],

    (Rejected, Open): [UCIS_Open],
    (Rejected, In_Progress): [UCIS_Open, UCIS_In_Progress],
    (Rejected, Rejected): [],
    (Rejected, Blocked): [UCIS_Open, UCIS_In_Progress, UCIS_Blocked],
    (Rejected, Merged): [UCIS_Open, UCIS_In_Progress, UCIS_Merged],
    (Rejected, Closed): [UCIS_Open, UCIS_In_Progress, UCIS_Merged, UCIS_Close],

    (Blocked, Open): [UCIS_Reject, UCIS_Open],
    (Blocked, In_Progress): [UCIS_In_Progress],
    (Blocked, Rejected): [UCIS_Reject],
    (Blocked, Blocked): [],
    (Blocked, Merged): [UCIS_Merged],
    (Blocked, Closed): [UCIS_Merged, UCIS_Close],

    (Merged, Open): [UCIS_Reject, UCIS_Open],
    (Merged, In_Progress): [UCIS_Open, UCIS_In_Progress],
    (Merged, Rejected): [UCIS_Reject],
    (Merged, Blocked): [UCIS_Reject, UCIS_Open, UCIS_In_Progress, UCIS_Blocked],
    (Merged, Merged): [],
    (Merged, Closed): [UCIS_Close],

    (Closed, Open): [UCIS_Reject, UCIS_Open],
    (Closed, In_Progress): [UCIS_Reject, UCIS_Open, UCIS_In_Progress],
    (Closed, Rejected): [UCIS_Reject],
    (Closed, Blocked): [UCIS_Reject, UCIS_Open, UCIS_In_Progress, UCIS_Blocked],
    (Closed, Merged): [UCIS_Reject, UCIS_Open, UCIS_In_Progress, UCIS_Merged],
    (Closed, Closed): [],

}

TypeToStateMap = {
    'UCIS': UCIS_Targets,
    'Feature': Feature_Targets,
    'E-Feature': E_Feature_Targets
}


def transition_to_state(jira, item: Issue, goal: State, log=None) -> Issue:
    # -- TODO: In addition to flagging an error when the desired state is not achieved,
    # -- TODO: Add a comment stating both the intended and actual state!
    transition_map = []
    if item.fields.issuetype.name in TypeToStateMap:
        transition_map = TypeToStateMap[item.fields.issuetype.name]
    else:
        log.logger.error("Unable to match item type '%s' to a transition category", item.fields.issuetype.name)
        msg = "Unable to match item type '%s' to a transition category" % item.fields.issuetype.name
        if log is None:
            raise ValueError(msg)
        else:
            log.logger.error(msg)

    state_pair = (normalize(item.fields.status.name), normalize(goal.name))
    if state_pair in transition_map:
        state_list = transition_map[state_pair]
    else:
        state_list = None
        msg = "Unable to match start and end status '%s' to transition list for %s"\
              % (state_pair, item.fields.issuetype.name)
        if log is None:
            raise ValueError(msg)
        else:
            log.logger.error(msg)

    if state_list is None:
        msg = "Could not find map to goal %s: Target %s is at %s, goal is %s"\
              % (state_pair, item.key, item.fields.status.name, goal.name)
        if log is None:
            raise ValueError(msg)
        else:
            log.logger.error(msg)
        return item
    else:
        if log is not None:
            log.logger.info("Target is at %s, goal is %s, expected transitions are %s",
                            item.fields.status.name, goal.name, [item.name for item in state_list])
        for state in state_list:
            available_transitions = {normalize(item['name']): item['id'] for item in jira.jira_client.transitions(item)}
            next_id = None
            for name in state.to_label:
                if name in available_transitions:
                    next_id = available_transitions[name]

            if next_id is not None:
                if log is not None:
                    log.logger.info("Attempt transition from %s, to %s", item.fields.status.name, name)
                try:
                    jira.jira_client.transition_issue(item, next_id)
                    item = jira.jira_client.issue(item.key)
                except JIRAError as j:
                    log.logger.error("JIRA error occured: %s", j.__str__())
                    msg = "JIRA error occured: %s" % j.__str__()
                    if log is None:
                        raise ValueError(msg)
                    else:
                        log.logger.error(msg)

                # -- abort if transition is not successful!
                if normalize(item.fields.status.name) != normalize(state.name):
                    if log is not None:
                        log.logger.error("Status for %s did not transition correctly. Should have been '%s' and is '%s'. %s",
                                         item.key, state.name, item.fields.status.name, available_transitions)
                    break
            else:
                msg = "In pair %s Target state '%s' for '%s' not found in available transitions: %s"\
                      % (state_pair, name, item.fields.issuetype.name, available_transitions)
                if log is None:
                    raise ValueError(msg)
                else:
                    log.logger.error(msg)
        if log is not None:
            log.logger.info("Final status is %s", item.fields.status.name)

        if normalize(item.fields.status.name) != normalize(goal.name):
            if log is not None:
                log.logger.error("Status for %s was not set correctly. Should have been '%s' and is '%s'",
                                 item.key, goal.name, item.fields.status.name)
    return item
