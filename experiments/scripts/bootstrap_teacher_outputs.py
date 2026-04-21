#!/usr/bin/env python3
"""Create bootstrap teacher labels from sampled states when no external teacher is available."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_candidate_scores(state: dict[str, Any], success_trace: bool) -> dict[str, float]:
    remaining_budget = int(state.get("remaining_budget", 0))
    tags = set(state.get("trigger_tags", []))

    if success_trace:
        continue_score = 0.98 if "answer_step" in tags else 0.92
        if remaining_budget <= 1:
            continue_score = 0.76
        elif remaining_budget == 2:
            continue_score = 0.84
        branch_score = max(0.35, continue_score - 0.22)
        restart_score = 0.03
    else:
        continue_score = 0.18 if remaining_budget <= 1 else 0.3
        branch_score = 0.28 if remaining_budget > 1 else 0.12
        restart_score = 0.4 if remaining_budget <= 1 else 0.22

    scores: dict[str, float] = {
        "continue": round(continue_score, 4),
        "branch": round(branch_score, 4),
        "restart": round(restart_score, 4),
    }
    rollback_base = 0.48 if success_trace else 0.62
    for idx, checkpoint in enumerate(state.get("checkpoint_candidates", []), start=1):
        scores[f"rollback:{checkpoint['checkpoint_id']}"] = round(max(0.08, rollback_base - 0.07 * (idx - 1)), 4)
    return scores


def build_label(state: dict[str, Any]) -> dict[str, Any]:
    success_trace = bool(state.get("source_success", False))
    remaining_budget = int(state.get("remaining_budget", 0))
    checkpoints = state.get("checkpoint_candidates", [])
    tags = set(state.get("trigger_tags", []))
    scores = build_candidate_scores(state, success_trace)

    if success_trace:
        recoverability = "weakly_recoverable" if remaining_budget <= 1 else "recoverable"
        decision = "continue"
        rollback_target = None
        if "answer_step" in tags:
            rationale = (
                "This state comes from a known successful trajectory and is already on the task-completing path, "
                "so continuing is the strongest bootstrap label."
            )
        elif remaining_budget <= 1:
            rationale = (
                "The state comes from a successful trajectory, but the remaining budget is tight, so it is labeled "
                "weakly recoverable while still preferring continuation."
            )
        else:
            rationale = (
                "This state appears on a successful trajectory and therefore has a demonstrated continue-to-success path."
            )
    elif checkpoints:
        recoverability = "weakly_recoverable"
        rollback_target = checkpoints[-1]["checkpoint_id"]
        decision = "rollback"
        rationale = (
            "No successful continuation trace is available for this state, so the bootstrap teacher prefers rolling "
            "back to the most recent checkpoint."
        )
    else:
        recoverability = "irrecoverable"
        decision = "restart"
        rollback_target = None
        rationale = (
            "No successful continuation trace or rollback checkpoint is available for this state, so the bootstrap "
            "teacher marks it irrecoverable."
        )

    return {
        "state_id": state["state_id"],
        "recoverability": recoverability,
        "decision": decision,
        "rollback_target": rollback_target,
        "teacher_rationale": rationale,
        "candidate_scores": scores,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("states_jsonl")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rows = [build_label(state) for state in load_jsonl(Path(args.states_jsonl))]
    text = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + ("\n" if rows else "")
    Path(args.output).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
