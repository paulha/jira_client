class State:
    def __init__(self, name, to_label):
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

Feature_In_Review = State('In Review', ['In Review'])
Feature_Blocked = State('Blocked', ['Blocked'])
Feature_New = State('New', ['New'])
Feature_Rejected = State('Rejected', ['Reject', 'Rejected'])
Feature_Candidate = State('Candidate', ['Candidate'])
Feature_Deprecated = State('Deprecated', ['Deprecated'])

Feature_map = {
    'New': [Feature_In_Review, Feature_Blocked, Feature_Rejected],
    'Rejected': [Feature_In_Review, Feature_New, Feature_Blocked],
    'Blocked': [Feature_Blocked, Feature_In_Review, Feature_Rejected],
    'In Review': [Feature_Candidate, Feature_Blocked, Feature_New, Feature_Rejected],
    'Candidate': [Feature_In_Review, Feature_Deprecated],
    'Deprecated': [Feature_Candidate]
}

Feature_Targets = {
    (New, New): [],
    (New, Blocked): [Feature_Blocked],
    (New, Rejected): [Feature_Rejected],
    (New, In_Review): [Feature_In_Review],
    (New, Candidate): [Feature_In_Review, Feature_Candidate],
    (New, Deprecated): [Feature_In_Review, Feature_Candidate, Feature_Deprecated],

    (Blocked, New): [Feature_New],
    (Blocked, Blocked): [Feature_Blocked],
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

E_Feature_Open = State('Open', ['Open'])
E_Feature_Closed = State('Closed', ['Close'])
E_Feature_Reject = State('Reject', ['Reject'])
E_Feature_Rejected = State('Rejected', ['Reject'])
E_Feature_Start_Progress = State('Start Progress', ['Start Progress'])
E_Feature_In_Progress = State('In Progress', ['In Progress'])
E_Feature_Blocked = State('Blocked', ['Blocked'])
E_Feature_Merge = State('Merge', ['Merge'])
E_Feature_Merged = State('Merged', ['Merge'])
E_Feature_Reopen = State('Reopen', ['Reopen'])
E_Feature_Update_From_Parent = State("Update From Parent", ["Update From Parent"])

E_Feature_map = {
    # -- NOTE: That transition values depend on the starting state, even when the end state is the same!
    'Open': [E_Feature_Rejected, E_Feature_Update_From_Parent, E_Feature_Start_Progress, E_Feature_Reject],
    'Reject': [E_Feature_Open, E_Feature_Update_From_Parent],
    'Rejected': [E_Feature_Open, E_Feature_Update_From_Parent],
    # -- note: Update From Parent (sometimes!) leaves you in 'Start Progress'
    'Update From Parent': [E_Feature_Start_Progress],
    'Start Progress': [E_Feature_Reject, E_Feature_Blocked, E_Feature_Update_From_Parent, E_Feature_Merge],
    'Blocked': [E_Feature_Reject, E_Feature_Blocked, E_Feature_Update_From_Parent, E_Feature_In_Progress],
    'In Progress': [E_Feature_Blocked, E_Feature_Update_From_Parent, E_Feature_Merge],
    'Merge': [E_Feature_Reject, E_Feature_Closed, E_Feature_Update_From_Parent, E_Feature_Reopen],
    'Merged': [E_Feature_Reject, E_Feature_Closed, E_Feature_Update_From_Parent, E_Feature_Reopen],
    # -- note: this is the same as Start Progress
    'Reopen': [E_Feature_Blocked, E_Feature_Update_From_Parent, E_Feature_Merge, E_Feature_Reject],
    'Close': [E_Feature_Update_From_Parent, E_Feature_Reject],
    'Closed': [E_Feature_Update_From_Parent, E_Feature_Reject],
}


E_Feature_Targets = {
    (Open, Open): [],
    (Open, Closed): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Merged, E_Feature_Closed],
    (Open, Merged): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Merged],
    (Open, Rejected): [E_Feature_Open, E_Feature_Rejected],
    (Open, In_Progress): [E_Feature_Open, E_Feature_In_Progress],
    (Open, Blocked): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Blocked],

    (In_Progress, Open): [E_Feature_Merged, E_Feature_Closed, E_Feature_Open],
    (In_Progress, Closed): [E_Feature_Merged, E_Feature_Closed],
    (In_Progress, Merged): [E_Feature_Merged],
    (In_Progress, Rejected): [E_Feature_Rejected],
    (In_Progress, In_Progress): [],
    (In_Progress, Blocked): [E_Feature_Blocked],

    (Blocked, Open): [E_Feature_Merged, E_Feature_Closed, E_Feature_Open],
    (Blocked, Closed): [E_Feature_Merged, E_Feature_Closed],
    (Blocked, Merged): [E_Feature_Merged],
    (Blocked, Rejected): [E_Feature_Rejected],
    (Blocked, In_Progress): [E_Feature_In_Progress],
    (Blocked, Blocked): [],

    (Merged, Open): [E_Feature_Closed, E_Feature_Open],
    (Merged, Closed): [E_Feature_Closed],
    (Merged, Merged): [],
    (Merged, Rejected): [E_Feature_Rejected],
    (Merged, In_Progress): [E_Feature_In_Progress],
    (Merged, Blocked): [E_Feature_In_Progress, E_Feature_Blocked],

    (Rejected, Open): [E_Feature_Open],
    (Rejected, Closed): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Merged, E_Feature_Closed],
    (Rejected, Merged): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Merged],
    (Rejected, Rejected): [],
    (Rejected, In_Progress): [E_Feature_Open, E_Feature_In_Progress],
    (Rejected, Blocked): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Blocked],

    (Closed, Open): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Merged, E_Feature_Closed],
    (Closed, Closed): [],
    (Closed, Merged): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Merged],
    (Closed, Rejected): [E_Feature_Open, E_Feature_Rejected],
    (Closed, In_Progress): [E_Feature_Open, E_Feature_In_Progress],
    (Closed, Blocked): [E_Feature_Open, E_Feature_In_Progress, E_Feature_Blocked],
}

UCIS_Open = State('Open', ['Open', "Reopen"])
UCIS_Start_Progress = State('Start Progress', ['Start Progress'])
UCIS_Rejected = State('Rejected', ['Rejected', "To Rejected"])
UCIS_Blocked = State('Blocked', ['Blocked', "To Blocked"])
UCIS_Merged = State('Merged', ['Merged', "To Merged"])
UCIS_Closed = State('Closed', ["Edit Closed Issues", "Close Issue"])
UCIS_Edit_Closed_Issue = State("Edit Closed Issues", ["Edit Closed Issues"])

UCIS_map = {
    'Open': [UCIS_Start_Progress, UCIS_Rejected],
    'Start Progress': [UCIS_Blocked, UCIS_Rejected, UCIS_Merged],
    'Rejected': [UCIS_Open],
    'Blocked': [UCIS_Rejected, UCIS_Start_Progress, UCIS_Merged],
    'Merged': [UCIS_Open, UCIS_Closed, UCIS_Rejected],
    'Close': [UCIS_Edit_Closed_Issue, E_Feature_Reject]
}

UCIS_Targets = {
    (Open, Open): [],
    (Open, In_Progress): [UCIS_Start_Progress],
    (Open, Rejected): [UCIS_Rejected],
    (Open, Blocked): [UCIS_Start_Progress, UCIS_Blocked],
    (Open, Merged): [UCIS_Start_Progress, UCIS_Merged],
    (Open, Closed): [UCIS_Start_Progress, UCIS_Merged, UCIS_Closed],

    (In_Progress, Open): [UCIS_Open],
    (In_Progress, In_Progress): [],
    (In_Progress, Rejected): [UCIS_Rejected],
    (In_Progress, Blocked): [UCIS_Blocked],
    (In_Progress, Merged): [UCIS_Merged],
    (In_Progress, Closed): [UCIS_Merged, UCIS_Closed],

    (Rejected, Open): [UCIS_Open],
    (Rejected, In_Progress): [UCIS_Open, UCIS_Start_Progress],
    (Rejected, Rejected): [],
    (Rejected, Blocked): [UCIS_Open, UCIS_Start_Progress, UCIS_Blocked],
    (Rejected, Merged): [UCIS_Open, UCIS_Start_Progress, UCIS_Merged],
    (Rejected, Closed): [UCIS_Open, UCIS_Start_Progress, UCIS_Merged, UCIS_Closed],

    (Blocked, Open): [UCIS_Rejected, UCIS_Open],
    (Blocked, In_Progress): [UCIS_Start_Progress],
    (Blocked, Rejected): [UCIS_Rejected],
    (Blocked, Blocked): [],
    (Blocked, Merged): [UCIS_Merged],
    (Blocked, Closed): [UCIS_Merged, UCIS_Closed],

    (Merged, Open): [UCIS_Closed, UCIS_Open],
    (Merged, In_Progress): [UCIS_Start_Progress],
    (Merged, Rejected): [UCIS_Rejected],
    (Merged, Blocked): [UCIS_Start_Progress, UCIS_Blocked],
    (Merged, Merged): [],
    (Merged, Closed): [UCIS_Closed],

    (Closed, Open): [UCIS_Open],
    (Closed, In_Progress): [UCIS_Open, UCIS_Start_Progress],
    (Closed, Rejected): [UCIS_Rejected],
    (Closed, Blocked): [UCIS_Open, UCIS_Start_Progress, UCIS_Blocked],
    (Closed, Merged): [UCIS_Open, UCIS_Start_Progress, UCIS_Merged],
    (Closed, Closed): [],

}

TypeToMap = {
    'UCIS': UCIS_map,
    'Feature': Feature_map,
    'E-Feature': E_Feature_map
}


class StateMachine:
    Open = State('Open', 'to_open')
    Closed = State('Closed', 'close')
    InProgress = State('In Progress', 'in_progress')
    Rejected = State('Rejected', 'reject')
    Blocked = State('Blocked', 'block')
    Merged = State('Merged', 'to_merge')

    state_map = {
        None: [Open],
        Open.name: [InProgress, Rejected],
        Rejected.name: [Open],
        InProgress.name: [Merged, Blocked, Rejected],
        Blocked.name: [InProgress, Merged, Rejected],
        Merged.name: [Closed],
        Closed.name: []  # I think!
    }

    def __init__(self, state_map=state_map, start=None):
        self.current_state = start
        self.transition_map = state_map

    def get_state(self):
        return self.current_state

    def goto_state(self, next_state):
        if self.current_state is None:
            self.current_state = self.transition_map[self.current_state][0]
        if next_state in self.transition_map[self.current_state]:
            self.current_state = next_state
        else:
            raise Exception("Forbidden Transition")
        return self.current_state

    @staticmethod
    def find_map_to_state(start, goal, transition_map, accum=None, visited=[]):
        if start == goal:
            return []
        for trial in transition_map[start]:
            if trial.name in visited:
                continue
            visited.append(trial.name)
            search = [item for item in transition_map[start] if goal == item.name]
            if search:
                return search
            else:
                result = StateMachine.find_map_to_state(trial.name, goal, transition_map, accum, visited)
                if result is not None:
                    result.insert(0, trial)
                    return result
                else:
                    return None

        return None

    @staticmethod
    def transition_to_state(jira, item, goal, log=None):
        # -- TODO: A deterministic algorithm
        # -- TODO: Flag an error if the achieved status is not the same as the desired status
        # -- TODO: Notice that this doesn't always detect when item and goal status are identical
        transition_map = TypeToMap[item.fields.issuetype.name]
        visited = []
        if item.fields.status.name == goal.name:
            state_map = []
        else:
            state_map = StateMachine.find_map_to_state(item.fields.status.name, goal.name, transition_map, visited=visited)

        if state_map is None:
            log.logger.error("Could not find map to goal: Target %s is at %s, goal is %s",
                             item.key, item.fields.status.name, goal.name)
            return False
        else:
            log.logger.info("Target is at %s, goal is %s, expected transitions are %s",
                             item.fields.status.name, goal.name, [item.name for item in state_map])
            for state in state_map:
                available_transitions = {item['name']: item['id'] for item in jira.jira_client.transitions(item)}
                for name in state.to_label:
                    if name in available_transitions:
                        next_id = available_transitions[name]
                        log.logger.info("Attempt transition from %s, to %s", item.fields.status.name, name)
                        jira.jira_client.transition_issue(item, next_id)
                        item = jira.jira_client.issue(item.key)
            log.logger.info("Final status is %s", item.fields.status.name)
        return True if state_map else False
