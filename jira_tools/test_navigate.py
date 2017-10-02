import unittest
from navigate import StateMachine
from jira.exceptions import JIRAError


class MyTestCase(unittest.TestCase):
    def test_init(self):
        machine = StateMachine()
        try:
            state = machine.goto_state(StateMachine.Open)
            self.assertEqual(state, StateMachine.Open)
        except JIRAError:
            self.assert_("Raised Exception")

    def test_closed_to_open(self):
        machine = StateMachine(start=StateMachine.Closed)
        try:
            state = machine.goto_state(StateMachine.Open)
            self.assertEqual(state, StateMachine.Open)
        except JIRAError:
            self.assert_("Raised Exception")

    def test_blocked_to_open_raises_exception(self):
        machine = StateMachine(start=StateMachine.Blocked)
        try:
            state = machine.goto_state(StateMachine.Open)
            self.assertEqual(state, StateMachine.Blocked)
        except JIRAError:
            self.assertRaises(JIRAError)

    def test_seek_state_1(self):
        machine = StateMachine(start='')
        result = machine.find_map_to_state(StateMachine.Blocked.name, StateMachine.Closed.name)
        self.assertEqual(result, [StateMachine.InProgress, StateMachine.Merged])


if __name__ == '__main__':
    unittest.main()
