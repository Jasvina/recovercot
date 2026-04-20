#!/usr/bin/env python3
"""Build SFT-style training data from sampled states and labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def state_prompt(state: dict[str, Any]) -> str:
    history_lines = []
    for item in state.get("recent_history", []):
        history_lines.append(
            f"- step {item['step']}: action={item['action']} target={item['target']} observation={item['observation']}"
        )
    checkpoint_lines = []
    for checkpoint in state.get("checkpoint_candidates", []):
        checkpoint_lines.append(
            f"- {checkpoint['checkpoint_id']} (step {checkpoint['step']}): {checkpoint['summary']}"
        )
    parts = [
        "You are a recoverability controller for a web agent.",
        "Decide whether the current state is recoverable, whether the agent should continue, branch, rollback, or restart, and which checkpoint to restore if rollback is needed.",
        "Return valid JSON with keys: recoverability, decision, rollback_target.",
        "",
        f"Task instruction: {state['instruction']}",
        f"Site: {state['site']}",
        f"State id: {state['state_id']}",
        f"Current URL: {state['current_url']}",
        f"Current observation: {state['current_observation']}",
        f"Trigger tags: {state.get('trigger_tags', [])}",
        f"Remaining budget: {state['remaining_budget']}",
        "",
        "Recent history:",
        * (history_lines or ["- <empty>"]),
        "",
        "Checkpoint candidates:",
        * (checkpoint_lines or ["- <none>"]),
    ]
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("states_jsonl")
    parser.add_argument("labels_jsonl")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    states = {row["state_id"]: row for row in load_jsonl(Path(args.states_jsonl))}
    labels = {row["state_id"]: row for row in load_jsonl(Path(args.labels_jsonl))}

    rows = []
    for state_id in sorted(set(states) & set(labels)):
        state = states[state_id]
        label = labels[state_id]
        answer = {
            "recoverability": label["recoverability"],
            "decision": label["decision"],
            "rollback_target": label["rollback_target"],
        }
        rows.append(
            {
                "id": state_id,
                "messages": [
                    {"role": "user", "content": state_prompt(state)},
                    {"role": "assistant", "content": json.dumps(answer, ensure_ascii=True)},
                ],
            }
        )

    out = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + ("\n" if rows else "")
    Path(args.output).write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
