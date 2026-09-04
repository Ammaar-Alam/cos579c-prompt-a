import unittest
from unittest.mock import patch

from grid_agent import Agent, Grid
from run_experiment import parse_direction
from run_experiment import run


class GridAgentTests(unittest.TestCase):
    def test_tool_returns_coordinate_and_goal(self):
        grid = Grid((0, 1))
        self.assertEqual(grid.move("right"), {"coordinate": (0, 1), "goal": True})

    def test_parse_direction(self):
        self.assertEqual(parse_direction("right"), "right")
        self.assertEqual(parse_direction('{"tool":"down"}'), "down")

    def test_dashboard_gets_goal_before_first_decision(self):
        with patch("run_experiment.ask", return_value='{"tool":"right"}') as ask, patch("run_experiment.post_event") as emit:
            run("codex", "test", [(0, 1)], False, 1, "http://127.0.0.1:8765")
        events = [call.args[1] for call in emit.call_args_list]
        self.assertEqual([event["type"] for event in events], ["episode_start", "decision", "episode"])
        self.assertEqual(events[0]["goal"], [0, 1])
        self.assertEqual(events[1]["from"], [0, 0])
        self.assertNotIn('"goal": [0, 1]', ask.call_args.args[1])

    def test_agents_reach_goal_and_memory_can_hurt(self):
        baseline = Agent()
        memory = Agent(remember_goal=True)
        self.assertEqual(baseline.run((0, 2)), 2)
        self.assertEqual(memory.run((2, 4)), 6)
        self.assertGreater(memory.run((2, 4)), baseline.run((1, 4)))


if __name__ == "__main__":
    unittest.main()
