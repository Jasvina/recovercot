#!/usr/bin/env python3
"""Summarize trajectory, state, or label JSONL files used in RecoverCoT."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize_trajectories(rows: list[dict[str, Any]]) -> dict[str, Any]:
    step_lengths = [len(row.get("steps", [])) for row in rows]
    tag_counter = Counter()
    success_counter = Counter()
    site_counter = Counter()
    checkpoints = 0
    for row in rows:
        site_counter[row.get("site", "unknown")] += 1
        success_counter["success" if row.get("success") else "failure"] += 1
        for step in row.get("steps", []):
            tag_counter.update(step.get("tags", []))
            checkpoints += int(bool(step.get("checkpoint", False)))
    return {
        "kind": "trajectory",
        "count": len(rows),
        "avg_steps": round(sum(step_lengths) / len(step_lengths), 4) if step_lengths else 0.0,
        "max_steps": max(step_lengths) if step_lengths else 0,
        "success_breakdown": dict(success_counter),
        "site_breakdown": dict(site_counter),
        "total_checkpoints": checkpoints,
        "top_tags": tag_counter.most_common(10),
    }


def summarize_states(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tag_counter = Counter()
    budget_values = []
    checkpoints = []
    for row in rows:
        tag_counter.update(row.get("trigger_tags", []))
        budget_values.append(int(row.get("remaining_budget", 0)))
        checkpoints.append(len(row.get("checkpoint_candidates", [])))
    return {
        "kind": "sampled_state",
        "count": len(rows),
        "avg_remaining_budget": round(sum(budget_values) / len(budget_values), 4) if budget_values else 0.0,
        "avg_checkpoint_candidates": round(sum(checkpoints) / len(checkpoints), 4) if checkpoints else 0.0,
        "top_trigger_tags": tag_counter.most_common(10),
    }


def summarize_labels(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rec_counter = Counter(row.get("recoverability", "unknown") for row in rows)
    dec_counter = Counter(row.get("decision", "unknown") for row in rows)
    return {
        "kind": "label",
        "count": len(rows),
        "recoverability_breakdown": dict(rec_counter),
        "decision_breakdown": dict(dec_counter),
    }


def infer_kind(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "unknown"
    sample = rows[0]
    if "steps" in sample:
        return "trajectory"
    if "current_observation" in sample:
        return "sampled_state"
    if "recoverability" in sample and "candidate_scores" in sample:
        return "label"
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_jsonl")
    parser.add_argument("--output")
    args = parser.parse_args()
    rows = load_jsonl(Path(args.input_jsonl))
    kind = infer_kind(rows)
    if kind == "trajectory":
        summary = summarize_trajectories(rows)
    elif kind == "sampled_state":
        summary = summarize_states(rows)
    elif kind == "label":
        summary = summarize_labels(rows)
    else:
        raise ValueError("unsupported JSONL kind for stats")
    text = json.dumps(summary, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
