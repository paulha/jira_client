import unittest

state_map = {
    None: ['Open'],
    'Open': ['In Progress', 'Rejected'],
    'Rejected': ['Open'],
    'In Progress': ['Merged', 'Blocked', 'Rejected'],
    'Blocked': ['In Progress', 'Merged', 'Rejected'],
    'Merged': ['Closed'],
    'Closed': ['Open']      # I think!
}

current_state = None

def get_state():
    return current_state

def goto_state(next_state):
    global current_state
    if current_state is None:
        current_state = state_map[current_state][0]
    if next_state in state_map[current_state]:
        current_state = next_state
    return current_state


class MyTestCase(unittest.TestCase):
    def test_init(self):
        state = goto_state('Open')
        self.assertEqual(state, 'Open')


if __name__ == '__main__':
    unittest.main()
