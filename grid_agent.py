"""Tiny deterministic grid environment and baseline/memory agents."""

from dataclasses import dataclass, field


Coordinate = tuple[int, int]


@dataclass
class Grid:
    goal: Coordinate
    size: int = 5
    position: Coordinate = (0, 0)
    calls: int = 0

    def move(self, direction: str) -> dict[str, object]:
        if direction not in {"right", "down"}:
            raise ValueError("direction must be 'right' or 'down'")
        row, column = self.position
        next_position = (row, column + 1) if direction == "right" else (row + 1, column)
        if not all(0 <= value < self.size for value in next_position):
            raise ValueError("move leaves the grid")
        self.position = next_position
        self.calls += 1
        return {"coordinate": self.position, "goal": self.position == self.goal}


@dataclass
class Agent:
    remember_goal: bool = False
    memory: set[Coordinate] = field(default_factory=set)

    def run(self, goal: Coordinate) -> int:
        grid = Grid(goal)
        # Memory is deliberately simple: it retains observed goal coordinates.
        # A changed goal can make this heuristic worse, which is useful for Prompt A.
        target = next(iter(self.memory), goal) if self.remember_goal and self.memory else goal
        row, column = target
        for _ in range(row):
            result = grid.move("down")
            if result["goal"]:
                break
        else:
            for _ in range(column):
                result = grid.move("right")
                if result["goal"]:
                    break
        if self.remember_goal:
            self.memory.add(goal)
        return grid.calls


def demo() -> None:
    episodes = [(0, 2), (2, 2), (1, 4)]
    baseline = Agent()
    memory = Agent(remember_goal=True)
    print("episode baseline memory")
    for goal in episodes:
        print(goal, baseline.run(goal), memory.run(goal))


if __name__ == "__main__":
    demo()
