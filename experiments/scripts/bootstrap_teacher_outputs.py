#!/usr/bin/env python3
"""Create bootstrap teacher labels from sampled states when no external teacher is available."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_score_template(state: dict[str, Any]) -> dict[str, float]:
    scores: dict[str, float] = {
        "continue": 0.18,
        "branch": 0.18,
        "restart": 0.08,
    }
    for idx, checkpoint in enumerate(state.get("checkpoint_candidates", []), start=1):
        scores[f"rollback:{checkpoint['checkpoint_id']}"] = round(max(0.12, 0.55 - 0.08 * (idx - 1)), 4)
    return scores


def bump(scores: dict[str, float], key: str, value: float) -> None:
    if key in scores:
        scores[key] = round(value, 4)


def choose_latest_checkpoint(state: dict[str, Any]) -> str | None:
    checkpoints = state.get("checkpoint_candidates", [])
    if not checkpoints:
        return None
    return checkpoints[-1]["checkpoint_id"]


def label_observed_success(state: dict[str, Any], scores: dict[str, float]) -> tuple[str, str, str | None, str]:
    remaining_budget = int(state.get("remaining_budget", 0))
    tags = set(state.get("trigger_tags", []))
    bump(scores, "continue", 0.98 if "answer_step" in tags else 0.92)
    bump(scores, "branch", 0.63 if remaining_budget > 1 else 0.44)
    bump(scores, "restart", 0.04)

    if remaining_budget <= 1:
        bump(scores, "continue", 0.76)
        recoverability = "weakly_recoverable"
        rationale = (
            "This observed state lies on a successful trajectory, but the remaining budget is tight, so the state is "
            "only weakly recoverable even though continuing still dominates."
        )
    elif "answer_step" in tags:
        recoverability = "recoverable"
        rationale = (
            "This observed state already sits on the task-completing path of a successful trace, making continuation "
            "the strongest bootstrap decision."
        )
    else:
        recoverability = "recoverable"
        rationale = (
            "This observed state appears on a demonstrated successful trajectory, so the bootstrap teacher favors "
            "continuing along the known path."
        )
    return recoverability, "continue", None, rationale


def label_misleading_guidance(state: dict[str, Any], scores: dict[str, float]) -> tuple[str, str, str | None, str]:
    remaining_budget = int(state.get("remaining_budget", 0))
    rollback_target = choose_latest_checkpoint(state)
    bump(scores, "continue", 0.26)
    bump(scores, "branch", 0.84 if remaining_budget > 1 else 0.62)
    bump(scores, "restart", 0.08)
    if rollback_target:
        bump(scores, f"rollback:{rollback_target}", 0.58)
    recoverability = "recoverable" if remaining_budget > 1 else "weakly_recoverable"
    rationale = (
        "The synthetic perturbation indicates misleading local guidance, so the controller should branch away from "
        "the current plan rather than persist with the biased continuation."
    )
    return recoverability, "branch", None, rationale


def label_wrong_branch(state: dict[str, Any], scores: dict[str, float]) -> tuple[str, str, str | None, str]:
    remaining_budget = int(state.get("remaining_budget", 0))
    rollback_target = choose_latest_checkpoint(state)
    bump(scores, "continue", 0.14)
    bump(scores, "branch", 0.36)
    bump(scores, "restart", 0.1 if remaining_budget > 0 else 0.44)

    if rollback_target:
        bump(scores, f"rollback:{rollback_target}", 0.9 if remaining_budget > 0 else 0.52)
        rationale = (
            "The synthetic wrong-branch perturbation suggests the agent navigated into an irrelevant branch, so "
            "rolling back to the latest reusable checkpoint is the safest recovery move."
        )
        return "weakly_recoverable", "rollback", rollback_target, rationale

    rationale = (
        "The state looks like a wrong-branch error but lacks checkpoint support, so branching is the best available "
        "recovery strategy."
    )
    return "weakly_recoverable", "branch", None, rationale


def label_repeated_failure(state: dict[str, Any], scores: dict[str, float]) -> tuple[str, str, str | None, str]:
    remaining_budget = int(state.get("remaining_budget", 0))
    rollback_target = choose_latest_checkpoint(state)
    bump(scores, "continue", 0.09)
    bump(scores, "branch", 0.33 if remaining_budget > 1 else 0.16)
    bump(scores, "restart", 0.24 if remaining_budget > 1 else 0.48)

    if rollback_target:
        bump(scores, f"rollback:{rollback_target}", 0.82 if remaining_budget > 0 else 0.42)
        rationale = (
            "The perturbation marks a repeated local failure pattern, so the controller should stop persisting and "
            "return to the latest checkpointed state."
        )
        return "weakly_recoverable", "rollback", rollback_target, rationale

    if remaining_budget > 1:
        rationale = (
            "Repeated local failure without rollback support still leaves room for a fresh branch, so branching is "
            "preferred over blind continuation."
        )
        return "weakly_recoverable", "branch", None, rationale

    rationale = (
        "Repeated failure plus a near-zero budget makes the state effectively irrecoverable without restarting."
    )
    return "irrecoverable", "restart", None, rationale


def label_budget_pressure(state: dict[str, Any], scores: dict[str, float]) -> tuple[str, str, str | None, str]:
    remaining_budget = int(state.get("remaining_budget", 0))
    rollback_target = choose_latest_checkpoint(state)

    if remaining_budget <= 0:
        bump(scores, "continue", 0.03)
        bump(scores, "branch", 0.04)
        bump(scores, "restart", 0.78)
        if rollback_target:
            bump(scores, f"rollback:{rollback_target}", 0.18)
        rationale = (
            "The synthetic budget-pressure perturbation leaves no meaningful search budget, so restarting is the only "
            "reasonable bootstrap choice."
        )
        return "irrecoverable", "restart", None, rationale

    bump(scores, "continue", 0.38 if state.get("source_success", False) else 0.16)
    bump(scores, "branch", 0.21)
    bump(scores, "restart", 0.18)
    if rollback_target:
        bump(scores, f"rollback:{rollback_target}", 0.66)
        rationale = (
            "Only one recovery step remains, so a rollback to the latest checkpoint is safer than continued local "
            "exploration."
        )
        return "weakly_recoverable", "rollback", rollback_target, rationale

    rationale = (
        "The budget is nearly exhausted but the successful parent trace still offers a narrow continue-to-success path."
    )
    return "weakly_recoverable", "continue", None, rationale


def label_default_failure(state: dict[str, Any], scores: dict[str, float]) -> tuple[str, str, str | None, str]:
    remaining_budget = int(state.get("remaining_budget", 0))
    rollback_target = choose_latest_checkpoint(state)
    bump(scores, "continue", 0.18 if remaining_budget > 1 else 0.08)
    bump(scores, "branch", 0.24 if remaining_budget > 1 else 0.09)
    bump(scores, "restart", 0.2 if remaining_budget > 1 else 0.52)
    if rollback_target:
        bump(scores, f"rollback:{rollback_target}", 0.68)
        rationale = (
            "No successful continuation trace is available here, so the bootstrap teacher defaults to rolling back to "
            "the latest checkpoint."
        )
        return "weakly_recoverable", "rollback", rollback_target, rationale
    rationale = (
        "No successful continuation trace or rollback checkpoint is available, so the state is treated as "
        "irrecoverable under bootstrap labeling."
    )
    return "irrecoverable", "restart", None, rationale


def build_label(state: dict[str, Any]) -> dict[str, Any]:
    perturbation = state.get("perturbation_type")
    success_trace = bool(state.get("source_success", False))
    scores = build_score_template(state)

    if perturbation == "misleading_guidance":
        recoverability, decision, rollback_target, rationale = label_misleading_guidance(state, scores)
    elif perturbation == "wrong_branch":
        recoverability, decision, rollback_target, rationale = label_wrong_branch(state, scores)
    elif perturbation == "repeated_failure":
        recoverability, decision, rollback_target, rationale = label_repeated_failure(state, scores)
    elif perturbation == "budget_pressure":
        recoverability, decision, rollback_target, rationale = label_budget_pressure(state, scores)
    elif success_trace:
        recoverability, decision, rollback_target, rationale = label_observed_success(state, scores)
    else:
        recoverability, decision, rollback_target, rationale = label_default_failure(state, scores)

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
