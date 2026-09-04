# Prompt A: Does Memory Help?

This repository is a small, local benchmark for COS 579C. It compares an agent with no memory against the same agent with simple episodic memory.

## Experiment

Each episode uses a 5×5 grid:

- The agent always starts at `(0, 0)`.
- The goal is hidden from the agent.
- The only available tools are `right` and `down`.
- After every move, the environment returns the new coordinate and `goal: true` or `false`.
- A boundary move is a failed tool call that returns the current coordinate and an error; it is counted and the episode continues.
- The score is the number of tool decisions needed to find the goal.

The baseline receives the current coordinate and previous results. The memory condition additionally receives the successful goal coordinates observed in earlier episodes. Memory is intentionally small and transparent so we can inspect exactly what was given to the model.

The six shared episodes live in [`episodes.json`](episodes.json). Both conditions use the same order. The changing goals provide a case where stale memory can make performance worse.

## Run everything

Prerequisites:

- Python 3.9 or newer
- An authenticated `codex` CLI
- An authenticated `claude` CLI
- Pillow (`python3 -m pip install -r requirements.txt`)

Check the local implementation without calling a model:

```bash
python3 -m unittest -v
```

Run all four conditions:

```bash
python3 run_all.py
```

This runs Codex baseline, Codex memory, Claude baseline, and Claude memory against the same episodes. Codex uses `codex exec --model gpt-5.6-luna` with low reasoning effort. Claude uses `claude -p` and its configured default model. To run one condition with a different model:

```bash
python3 run_experiment.py codex --model gpt-5.6-luna --memory
python3 run_experiment.py claude --memory
```

Results are written to [`results/`](results/) as committed JSON evidence. Each episode also gets an animated decision trace in `results/gifs/`. `run_all.py` writes [`results/summary.md`](results/summary.md) and [`results/index.html`](results/index.html), comparing solved episodes, total calls, remembered goals, failures, and GIF links in a readable page.

## JSON decisions

The model is asked to return exactly one object:

```json
{"tool": "right"}
```

The shared [`decision.schema.json`](decision.schema.json) is passed to both CLIs. Codex uses `--output-schema` and `--json`; Claude uses `--json-schema` and `--output-format json`. The harness parses the structured response, executes the move, then includes the tool result in the next prompt.

## Live dashboard

Start the localhost dashboard:

```bash
python3 dashboard.py
```

Then open <http://127.0.0.1:8765> and press **Start run**. It shows the current 5×5 board and visited path, each model decision and returned coordinate, goal status, and call count for each condition.

The dashboard starts `run_all.py` for you. If you prefer to start the experiment from a second terminal, use:

```bash
# Terminal 1
python3 dashboard.py

# Terminal 2
python3 run_all.py --dashboard-url http://127.0.0.1:8765
```

To watch just one condition in the dashboard:

```bash
python3 run_experiment.py codex --memory --dashboard-url http://127.0.0.1:8765
```

Stop the dashboard with `Ctrl-C` in its terminal.

Press **Clear** when the run is idle to reset the dashboard view. Memory is not persisted: every new `run_all.py` run starts with an empty memory list, and stopping/restarting the dashboard also clears its view. There is no hidden Codex or Claude conversation state because each decision uses a fresh non-interactive CLI call.

## Files

- [`grid_agent.py`](grid_agent.py): the grid tool and deterministic demo.
- [`run_experiment.py`](run_experiment.py): one provider, one condition, and one episode sequence.
- [`run_all.py`](run_all.py): the four-condition experiment.
- [`dashboard.py`](dashboard.py): dependency-free localhost UI and event receiver.
- [`test_grid_agent.py`](test_grid_agent.py): checks for the tool and JSON protocol.
