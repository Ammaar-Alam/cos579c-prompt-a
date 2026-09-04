"""Run all provider/condition combinations for Prompt A."""

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=Path, default=ROOT / "episodes.json")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    output_dir = ROOT / "results"
    output_dir.mkdir(exist_ok=True)
    for provider in ("codex", "claude"):
        for memory in (False, True):
            condition = "memory" if memory else "baseline"
            command = [
                sys.executable,
                str(ROOT / "run_experiment.py"),
                provider,
                "--episodes",
                str(args.episodes),
                "--timeout",
                str(args.timeout),
                "--output",
                str(output_dir / f"{provider}-{condition}.json"),
            ]
            if memory:
                command.append("--memory")
            print(f"Running {provider} {condition}...", flush=True)
            subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
