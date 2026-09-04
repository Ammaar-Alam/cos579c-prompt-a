# Prompt A: Does Memory Help?

A minimal grid-navigation benchmark for COS 579C. Each episode places a goal in a 5×5 grid. The agent starts at `(0, 0)` and may call `right` or `down`; every tool result returns the updated coordinate and whether it is the goal.

The memory agent stores the goal coordinate after each episode. The baseline does not. Compare agents by tool calls required to reach the goal across the same episodes, including at least one episode where memory makes performance worse (for example, when the goal changes).

## Run

```bash
python3 grid_agent.py
python3 -m unittest -v
```

The implementation is intentionally deterministic and dependency-free so the benchmark can later be connected to Codex-p4 without changing the environment contract.
