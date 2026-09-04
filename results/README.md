# Does memory help?
### Six episodes · Codex Luna low · Baseline vs. episodic memory

**In this exploratory run, the memory agent solved fewer episodes: 2 of 6 versus 3 of 6.** It used fewer calls overall, but that does not imply better performance when fewer goals were reached.

[Episode comparison](#episode-by-episode) · [When remembering went worse](#when-remembering-went-worse) · [Animated replays](#watch-the-other-episodes) · [Raw baseline](codex-baseline.json) · [Raw memory](codex-memory.json)

> **Exploratory, not a controlled comparison.** CLI startup settings and prompt wording changed between conditions during this recorded run. Both used Luna low and the same ordered goals. The differences below are observed outcomes—not proof that memory caused them.

## The experiment

Each episode starts at **(0, 0)** on a **5 × 5 grid**. Coordinates are `(row, column)`: right increases the column, down increases the row. The agent knows the grid boundaries but not the goal.

The agent chooses one move, then receives its new coordinate and whether it found the goal. A boundary attempt leaves it in place and counts as a call. Episodes end at the goal or after **8 calls**.

| | Baseline | With memory |
| --- | --- | --- |
| Current position and episode history | Yes | Yes |
| Successful goal coordinates from earlier episodes | No | Yes |
| Episodes solved | **3 / 6** | **2 / 6** |
| Calls across all episodes, including failures | 43 | 37 |

The goal is visible in the GIFs for the viewer; the harness does not include it in the decision prompt. With only right/down moves, passing a goal can make it unreachable.

## What memory stores

Memory is a list of goal coordinates found in earlier episodes, supplied in the prompt. It starts empty; only a successful episode adds an entry. It is not a learned model update.

| Point in the memory run | Stored coordinates |
| --- | --- |
| Before episode 1 | `[]` |
| After episode 1; supplied to episodes 2–6 | `[[0, 2]]` |
| After episode 6 | `[[0, 2], [2, 1]]` |

This is a minimal record of past experiences: it retains where a previous episode succeeded, without a full trajectory or episode identifier. The baseline also has within-episode history, but no cross-episode memory.

## Episode by episode

“Not found” means the 8-call budget was exhausted; it is not a successful 8-call solution.

| Episode | Hidden goal | Baseline | With memory | Observed comparison |
| --- | --- | --- | --- | --- |
| 1 | (0, 2) | Not found · 8 calls | Found · 2 calls | Memory condition succeeds, **but memory was empty** |
| 2 | (2, 4) | Found · 6 calls | Not found · 8 calls | Worse outcome with memory |
| 3 | (1, 4) | Found · 5 calls | Not found · 8 calls | Worse outcome with memory |
| 4 | (3, 1) | Not found · 8 calls | Not found · 8 calls | Neither succeeds |
| 5 | (4, 4) | Found · 8 calls | Not found · 8 calls | Worse outcome with memory |
| 6 | (2, 1) | Not found · 8 calls | Found · 3 calls | Better outcome with memory |

Episode 1 already differs while both conditions have empty memory. That makes it especially important not to attribute every difference to remembering.

## When remembering went worse

**Episode 2: goal (2, 4).** The baseline reached the goal in 6 calls. The memory condition had the previous successful goal `(0, 2)` in its prompt, but exhausted 8 calls without reaching the new goal.

| Baseline · found in 6 calls | With memory · not found after 8 calls |
| --- | --- |
| <img src="gifs/codex-baseline-episode-2.gif" width="340" alt="Episode 2 baseline replay: reaches goal (2, 4) in six calls"> | <img src="gifs/codex-memory-episode-2.gif" width="340" alt="Episode 2 memory replay: fails to reach goal (2, 4) within eight calls"> |

This supplies an observed case where the memory condition performed worse. The stored coordinate could be unhelpful once the goal changes, but these outputs do not establish the agent's reasoning or isolate memory as the cause.

## Watch the other episodes

**Reading the replays:** dark = agent, amber = goal, tan = visited, green = agent at goal. The header shows the selected move and current position. GIF timing is illustrative, not measured model latency. Open an image for the full-size replay.

<details>
<summary>Episode 1 — baseline: not found · 8 calls; memory: found · 2 calls</summary>

| Baseline | With memory |
| --- | --- |
| <img src="gifs/codex-baseline-episode-1.gif" width="340" alt="Episode 1 baseline replay"> | <img src="gifs/codex-memory-episode-1.gif" width="340" alt="Episode 1 memory replay"> |

</details>

<details>
<summary>Episode 3 — baseline: found · 5 calls; memory: not found · 8 calls</summary>

| Baseline | With memory |
| --- | --- |
| <img src="gifs/codex-baseline-episode-3.gif" width="340" alt="Episode 3 baseline replay"> | <img src="gifs/codex-memory-episode-3.gif" width="340" alt="Episode 3 memory replay"> |

</details>

<details>
<summary>Episode 4 — baseline: not found · 8 calls; memory: not found · 8 calls</summary>

| Baseline | With memory |
| --- | --- |
| <img src="gifs/codex-baseline-episode-4.gif" width="340" alt="Episode 4 baseline replay"> | <img src="gifs/codex-memory-episode-4.gif" width="340" alt="Episode 4 memory replay"> |

</details>

<details>
<summary>Episode 5 — baseline: found · 8 calls; memory: not found · 8 calls</summary>

| Baseline | With memory |
| --- | --- |
| <img src="gifs/codex-baseline-episode-5.gif" width="340" alt="Episode 5 baseline replay"> | <img src="gifs/codex-memory-episode-5.gif" width="340" alt="Episode 5 memory replay"> |

</details>

<details>
<summary>Episode 6 — baseline: not found · 8 calls; memory: found · 3 calls</summary>

| Baseline | With memory |
| --- | --- |
| <img src="gifs/codex-baseline-episode-6.gif" width="340" alt="Episode 6 baseline replay"> | <img src="gifs/codex-memory-episode-6.gif" width="340" alt="Episode 6 memory replay"> |

</details>

## Reproduce and inspect

From the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 run_experiment.py codex --output results/codex-baseline.json
python3 run_experiment.py codex --memory --output results/codex-memory.json
python3 -c 'from pathlib import Path; from run_all import write_reports; write_reports(Path("results"))'
```

These commands overwrite the corresponding result files and GIFs. Rerun both conditions with unchanged code/settings for a controlled comparison; update this interpretation if the outputs change.

- [Generated summary and GIF gallery](summary.md) — regenerated from the JSON results.
- [HTML report](index.html) — open locally; GitHub's file view displays HTML source.
- [Baseline JSON](codex-baseline.json) and [memory JSON](codex-memory.json) — per-episode outcomes and final remembered coordinates.

Claude attempts failed authentication and are excluded from this comparison.
