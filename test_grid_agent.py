import unittest

from grid_agent import Agent, Grid


class GridAgentTests(unittest.TestCase):
    def test_tool_returns_coordinate_and_goal(self):
        grid = Grid((0, 1))
        self.assertEqual(grid.move("right"), {"coordinate": (0, 1), "goal": True})

    def test_agents_reach_goal_and_memory_can_hurt(self):
        baseline = Agent()
        memory = Agent(remember_goal=True)
        self.assertEqual(baseline.run((0, 2)), 2)
        self.assertEqual(memory.run((2, 4)), 6)
        self.assertGreater(memory.run((2, 4)), baseline.run((1, 4)))


if __name__ == "__main__":
    unittest.main()
