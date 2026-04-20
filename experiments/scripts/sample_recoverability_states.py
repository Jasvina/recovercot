#!/usr/bin/env python3
"""Sample recoverability states from trajectory JSON or JSONL files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HIGH_VALUE_TAGS = {
    "error_signal",
    "wrong_branch",
    "repeated_failure",
    "search_submit",
    "form_submit",
    "wrong_item",
}


def load_trajectories(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix == ".jsonl":
        items = []
        for line in text.splitlines():
            if line.strip():
                items.append(json.loads(line))
        return items

    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "trajectories" in data:
        return list(data["trajectories"])
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"unsupported trajectory file format: {path}")


def checkpoint_candidates(steps: list[dict[str, Any]], idx: int, limit: int) -> list[dict[str, Any]]:
    candidates = []
    for step in steps[:idx]:
        if not step.get("checkpoint"):
            continue
        checkpoint_id = f"checkpoint_step_{step['step']}"
        summary = step.get("observation", "")[:180]
        candidates.append(
            {
                "checkpoint_id": checkpoint_id,
                "step": step["step"],
                "summary": summary,
            }
        )
    return candidates[-limit:]


def should_sample(step: dict[str, Any], idx: int, total: int) -> bool:
    tags = set(step.get("tags", []))
    if tags & HIGH_VALUE_TAGS:
        return True
    if idx >= total - 2:
        return True
    return False


def build_state(trajectory: dict[str, Any], steps: list[dict[str, Any]], idx: int, history_window: int, checkpoint_limit: int) -> dict[str, Any]:
    step = steps[idx]
    start = max(0, idx - history_window)
    history = []
    for prev in steps[start:idx]:
        history.append(
            {
                "step": prev["step"],
                "action": prev["action"],
                "target": prev["target"],
                "value": prev.get("value"),
                "observation": prev["observation"],
                "tags": prev.get("tags", []),
            }
        )
    return {
        "task_id": trajectory["task_id"],
        "state_id": f"{trajectory['task_id']}_step_{step['step']}",
        "source_step": step["step"],
        "instruction": trajectory["instruction"],
        "site": trajectory["site"],
        "current_url": step["url"],
        "current_observation": step["observation"],
        "recent_history": history,
        "checkpoint_candidates": checkpoint_candidates(steps, idx, checkpoint_limit),
        "trigger_tags": step.get("tags", []),
        "remaining_budget": max(0, int(trajectory.get("max_steps", len(steps))) - int(step["step"])),
        "source_success": bool(trajectory.get("success", False)),
    }


def sample_states(trajectory: dict[str, Any], history_window: int, checkpoint_limit: int) -> list[dict[str, Any]]:
    steps = list(trajectory.get("steps", []))
    total = len(steps)
    states = []
    seen_steps = set()
    for idx, step in enumerate(steps):
        if not should_sample(step, idx, total):
            continue
        if step["step"] in seen_steps:
            continue
        seen_steps.add(step["step"])
        states.append(build_state(trajectory, steps, idx, history_window, checkpoint_limit))
    return states


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", help="path to trajectory .json or .jsonl")
    parser.add_argument("--output", help="optional output JSONL path")
    parser.add_argument("--history-window", type=int, default=3)
    parser.add_argument("--checkpoint-limit", type=int, default=4)
    args = parser.parse_args()

    trajectories = load_trajectories(Path(args.input_path))
    states = []
    for trajectory in trajectories:
        states.extend(sample_states(trajectory, args.history_window, args.checkpoint_limit))

    lines = [json.dumps(state, ensure_ascii=True) for state in states]
    output = "\n".join(lines) + ("\n" if lines else "")
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
