import unittest

class StateMachine:
    state_map = {
        None: ['Open'],
        'Open': ['In Progress', 'Rejected'],
        'Rejected': ['Open'],
        'In Progress': ['Merged', 'Blocked', 'Rejected'],
        'Blocked': ['In Progress', 'Merged', 'Rejected'],
        'Merged': ['Closed'],
        'Closed': []  # I think!
    }

    def __init__(self, state_map = state_map, start=None):
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

    def seek_state(self, start, goal, accum=None):
        for trial in self.transition_map[start]:
            if goal in self.transition_map[start]:
                return accum if accum is not None else []
            else:
                result = self.seek_state(trial, goal, accum)
                if result is not None:
                    result.insert(0, trial)
                    return result
                else:
                    return None

        return None




class MyTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_init(self):
        machine = StateMachine()
        try:
            state = machine.goto_state('Open')
            self.assertEqual(state, 'Open')
        except Exception as e:
            self.assert_("Raised Exception")

    def test_closed_to_open(self):
        machine = StateMachine(start='Closed')
        try:
            state = machine.goto_state('Open')
            self.assertEqual(state, 'Open')
        except Exception as e:
            self.assert_("Raised Exception")

    def test_blocked_to_open_raises_exception(self):
        machine = StateMachine(start='Blocked')
        try:
            state = machine.goto_state('Open')
            self.assertEqual(state, 'Blocked')
        except Exception as e:
            self.assertRaises(Exception)

    def test_seek_state_1(self):
        machine = StateMachine(start='')
        result = machine.seek_state('Blocked', 'Closed')
        self.assertEqual(result, ['In Progress', 'Merged'])

if __name__ == '__main__':
    unittest.main()
