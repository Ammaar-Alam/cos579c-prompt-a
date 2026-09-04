# Prompt A: Does Memory Help?

A minimal grid-navigation benchmark for COS 579C. Each episode places a goal in a 5×5 grid. The agent starts at `(0, 0)` and may call `right` or `down`; every tool result returns the updated coordinate and whether it is the goal.

The memory agent stores the goal coordinate after each episode. The baseline does not. Compare agents by tool calls required to reach the goal across the same episodes, including at least one episode where memory makes performance worse (for example, when the goal changes).

## Run

```bash
python3 grid_agent.py
python3 -m unittest -v
python3 run_experiment.py codex --memory --output results/codex-memory.json
python3 run_experiment.py claude --memory --output results/claude-memory.json
```

`run_experiment.py` invokes `codex exec` or `claude -p` once per move. The goal stays in the harness; each CLI call receives the current coordinate, prior tool results, and (for the memory condition) remembered successful goal coordinates. The harness executes the move and returns the coordinate/goal result to the next call.

Run baseline and memory conditions against the same `episodes.json` file, then compare `calls` and `success` in the JSON outputs. Authentication is handled by the local CLIs.
