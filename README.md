# Prompt A: Does Memory Help?

A minimal grid-navigation benchmark for COS 579C. Each episode places a goal in a 5×5 grid. The agent starts at `(0, 0)` and may call `right` or `down`; every tool result returns the updated coordinate and whether it is the goal.

The memory agent stores the goal coordinate after each episode. The baseline does not. Compare agents by tool calls required to reach the goal across the same episodes, including at least one episode where memory makes performance worse (for example, when the goal changes).

## Run

```bash
python3 grid_agent.py
python3 -m unittest -v
python3 run_all.py
```

`run_all.py` invokes all four conditions against the same `episodes.json` file:

- Codex baseline and memory, using `codex exec --model codex-p4`
- Claude baseline and memory, using `claude -p` (or its `--model` if you run `run_experiment.py` directly)

`run_experiment.py` invokes one CLI decision per move. The goal stays in the harness; each call receives the current coordinate, prior tool results, and (for the memory condition) remembered successful goal coordinates. The harness executes the move and returns the coordinate/goal result to the next call.

Results are written to `results/` and are not committed. Compare `calls` and `success` in the four JSON files. Authentication is handled by the local CLIs.
