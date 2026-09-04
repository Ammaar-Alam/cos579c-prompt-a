"""Run the same hidden-goal episodes through Codex or Claude."""

import argparse
import json
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from grid_agent import Grid
from gif_export import make_episode_gif


ROOT = Path(__file__).parent
MOVE_RE = re.compile(r"\b(right|down)\b", re.IGNORECASE)
DECISION_SCHEMA = json.loads((ROOT / "decision.schema.json").read_text())


def post_event(url: Optional[str], event: dict[str, object]) -> None:
    if not url:
        return
    try:
        request = urllib.request.Request(
            f"{url.rstrip('/')}/event",
            data=json.dumps(event).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(request, timeout=1).close()
    except (urllib.error.URLError, TimeoutError):
        pass


def _find_tool(value: object) -> Optional[str]:
    if isinstance(value, dict):
        if isinstance(value.get("tool"), str):
            return value["tool"]
        for child in value.values():
            found = _find_tool(child)
            if found:
                return found
    if isinstance(value, str):
        try:
            return _find_tool(json.loads(value))
        except json.JSONDecodeError:
            return None
    return None


def parse_direction(output: str) -> str:
    for line in reversed(output.splitlines()):
        try:
            direction = _find_tool(json.loads(line))
        except json.JSONDecodeError:
            direction = None
        if direction in {"right", "down"}:
            return direction
    match = MOVE_RE.search(output)
    if not match:
        raise ValueError(f"agent did not choose right/down: {output!r}")
    return match.group(1).lower()


def ask(provider: str, prompt: str, model: Optional[str], timeout: int) -> str:
    if provider == "codex":
        command = [
            "codex", "exec", "--ignore-user-config", "--ephemeral",
            "--model", model, "--config", 'model_reasoning_effort="low"', "--sandbox", "read-only",
            "--output-schema", str(ROOT / "decision.schema.json"), "--json", "-",
        ]
    else:
        command = [
            "claude", "-p", "--bare", "--effort", "low", "--tools", "",
            "--no-session-persistence", "--output-format", "json",
            "--json-schema", json.dumps(DECISION_SCHEMA),
        ] + (["--model", model] if model else [])
    result = subprocess.run(command, cwd=ROOT, input=prompt, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(detail or f"{provider} exited {result.returncode}")
    return result.stdout


def decision_prompt(position: tuple[int, int], history: list[dict[str, object]], memory: list[list[int]]) -> str:
    return f"""Navigate a hidden goal on a 5-by-5 grid.
Start is always (0, 0). You may choose only right or down. The grid boundary is 0..4 in each coordinate.
Choose exactly one next move. Reply only with JSON: {{"tool":"right"}} or {{"tool":"down"}}. Do not use other tools.
After the move, the environment will report the updated coordinate and whether it is the goal.
Current coordinate: {position}
Previous tool results: {json.dumps(history)}
Observed goal coordinates remembered from earlier episodes: {json.dumps(memory)}
"""


def run(
    provider: str,
    model: Optional[str],
    episodes: list[tuple[int, int]],
    use_memory: bool,
    timeout: int,
    dashboard_url: Optional[str] = None,
    gif_dir: Optional[Path] = None,
) -> list[dict[str, object]]:
    memory: list[list[int]] = []
    results = []
    for index, goal in enumerate(episodes, start=1):
        grid = Grid(goal)
        history: list[dict[str, object]] = []
        trace: list[dict[str, object]] = []
        post_event(dashboard_url, {
            "type": "episode_start", "provider": provider,
            "condition": "memory" if use_memory else "baseline",
            "episode": index, "goal": list(goal), "coordinate": [0, 0],
        })
        while grid.calls < 2 * (grid.size - 1) and grid.position != goal:
            remembered = memory if use_memory else []
            direction = parse_direction(ask(provider, decision_prompt(grid.position, history, remembered), model, timeout))
            result = grid.move(direction)
            history.append(result)
            event = {
                "type": "decision",
                "provider": provider,
                "condition": "memory" if use_memory else "baseline",
                "episode": index,
                "call": grid.calls,
                "from": list(history[-2]["coordinate"]) if len(history) > 1 else [0, 0],
                "tool": direction,
                "coordinate": list(grid.position),
                "goal": result["goal"],
                "error": result.get("error"),
            }
            trace.append(event)
            post_event(dashboard_url, event)
        success = grid.position == goal
        if use_memory and success:
            memory.append(list(goal))
        result_row = {"episode": index, "goal": list(goal), "calls": grid.calls, "success": success}
        if gif_dir:
            gif_name = f"{provider}-{'memory' if use_memory else 'baseline'}-episode-{index}.gif"
            make_episode_gif(trace, goal, gif_dir / gif_name)
            result_row["gif"] = f"gifs/{gif_name}"
        results.append(result_row)
        post_event(dashboard_url, {
            "type": "episode",
            "provider": provider,
            "condition": "memory" if use_memory else "baseline",
            "episode": index,
            "goal": list(goal),
            "calls": grid.calls,
            "success": success,
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("provider", choices=("codex", "claude"))
    parser.add_argument("--model", default=None)
    parser.add_argument("--episodes", type=Path, default=ROOT / "episodes.json")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--memory", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dashboard-url")
    parser.add_argument("--gif-dir", type=Path, default=ROOT / "results" / "gifs")
    args = parser.parse_args()
    model = args.model or ("gpt-5.6-luna" if args.provider == "codex" else None)
    episodes = [tuple(item) for item in json.loads(args.episodes.read_text())]
    results = run(args.provider, model, episodes, args.memory, args.timeout, args.dashboard_url, args.gif_dir)
    payload = {
        "provider": args.provider,
        "model": model or "default",
        "memory": args.memory,
        "remembered_goals": [entry["goal"] for entry in results if args.memory and entry["success"]],
        "episodes": results,
    }
    text = json.dumps(payload, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
