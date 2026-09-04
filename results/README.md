# Run results

Run `python3 run_all.py` to create the four provider/condition JSON files and `summary.md` here. These files are committed because they are the experiment evidence for Prompt A.

A failed provider still gets a JSON record, so one unavailable CLI does not hide the other results.

## Recorded run

Open [index.html](index.html) locally for the animated report, or read [summary.md](summary.md) on GitHub. All 12 Codex episode GIFs are included.

| Condition | Solved | Calls (including failures) |
| --- | ---: | ---: |
| Codex baseline | 3/6 | 43 |
| Codex memory | 2/6 | 37 |

Memory stores successful goal coordinates across episodes. The memory run finished with `[[0, 2], [2, 1]]`.

Episode 2 is an observed worse outcome with memory: baseline reached `(2, 4)` in 6 calls; memory exhausted 8 calls without reaching it. At that point memory contained `(0, 2)` from episode 1. The GIFs show the actual paths; this observation alone does not prove memory caused the failure.

Fewer total calls do not mean better performance when fewer episodes succeed. This is an exploratory run: Codex startup settings and prompt wording were simplified between the baseline and memory conditions while the run was in progress. Both used Luna low, but rerun with the current code for a controlled comparison. With only right/down moves, passing a goal can also make it unreachable; each episode stops after eight calls. Claude produced authentication failures, not evaluated episodes.
