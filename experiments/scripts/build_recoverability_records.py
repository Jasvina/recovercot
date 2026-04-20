#!/usr/bin/env python3
"""Merge sampled states with teacher outputs into full recoverability records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_LABEL_KEYS = {
    "recoverability",
    "decision",
    "rollback_target",
    "teacher_rationale",
    "candidate_scores",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def parse_teacher_row(row: dict[str, Any]) -> dict[str, Any]:
    if "response" in row:
        parsed = json.loads(row["response"])
    else:
        parsed = {k: row[k] for k in EXPECTED_LABEL_KEYS if k in row}
    missing = EXPECTED_LABEL_KEYS - set(parsed)
    if missing:
        raise ValueError(f"teacher row for state {row.get('state_id')} missing keys: {sorted(missing)}")
    return parsed


def build_record(state: dict[str, Any], label: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": state["task_id"],
        "state_id": state["state_id"],
        "instruction": state["instruction"],
        "history": state["recent_history"],
        "checkpoint_ids": [item["checkpoint_id"] for item in state.get("checkpoint_candidates", [])],
        "recoverability": label["recoverability"],
        "decision": label["decision"],
        "rollback_target": label["rollback_target"],
        "teacher_rationale": label["teacher_rationale"],
        "candidate_scores": label["candidate_scores"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("states_jsonl")
    parser.add_argument("teacher_outputs_jsonl")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    states = {row["state_id"]: row for row in load_jsonl(Path(args.states_jsonl))}
    teacher_rows = load_jsonl(Path(args.teacher_outputs_jsonl))

    records = []
    for row in teacher_rows:
        state_id = row["state_id"]
        if state_id not in states:
            raise ValueError(f"teacher output references unknown state_id: {state_id}")
        label = parse_teacher_row(row)
        records.append(build_record(states[state_id], label))

    text = "\n".join(json.dumps(record, ensure_ascii=True) for record in records) + ("\n" if records else "")
    Path(args.output).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
