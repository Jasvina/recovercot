#!/usr/bin/env python3
"""Expand observed recoverability states into synthetic counterfactual variants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def unique_tags(tags: list[str], *extra: str) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for item in list(tags) + list(extra):
        if item and item not in seen:
            merged.append(item)
            seen.add(item)
    return merged


def clone_state(
    state: dict[str, Any],
    variant_suffix: str,
    perturbation_type: str,
    perturbation_note: str,
    *,
    remaining_budget: int | None = None,
    extra_tags: list[str] | None = None,
) -> dict[str, Any]:
    extra_tags = extra_tags or []
    cloned = json.loads(json.dumps(state))
    cloned["state_id"] = f"{state['state_id']}__cf_{variant_suffix}"
    cloned["state_origin"] = "synthetic_counterfactual"
    cloned["parent_state_id"] = state["state_id"]
    cloned["perturbation_type"] = perturbation_type
    cloned["perturbation_note"] = perturbation_note
    cloned["trigger_tags"] = unique_tags(
        cloned.get("trigger_tags", []),
        "synthetic_counterfactual",
        *extra_tags,
    )
    if remaining_budget is not None:
        cloned["remaining_budget"] = max(0, remaining_budget)
    cloned["current_observation"] = (
        f"Counterfactual perturbation: {perturbation_note}\n\nOriginal observation:\n{state['current_observation']}"
    )
    return cloned


def build_variants(state: dict[str, Any]) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    budget = int(state.get("remaining_budget", 0))
    has_checkpoints = bool(state.get("checkpoint_candidates"))
    has_history = bool(state.get("recent_history"))

    if budget >= 2:
        variants.append(
            clone_state(
                state,
                "misleading_guidance",
                "misleading_guidance",
                "The agent recently followed a plausible but misleading hint and should reconsider the local plan.",
                extra_tags=["misleading_guidance", "wrong_branch"],
            )
        )

    if has_checkpoints:
        variants.append(
            clone_state(
                state,
                "wrong_branch",
                "wrong_branch",
                "The latest page transition entered an irrelevant branch, so the best move may require rollback to an earlier checkpoint.",
                extra_tags=["wrong_branch", "branch_change"],
            )
        )

    if has_history:
        variants.append(
            clone_state(
                state,
                "repeated_failure",
                "repeated_failure",
                "The last local strategy has already been tried and failed repeatedly, so persistence is now risky.",
                remaining_budget=max(0, min(budget, 2)),
                extra_tags=["repeated_failure", "error_signal"],
            )
        )

    reduced_budget = 0 if budget == 0 else 1
    variants.append(
        clone_state(
            state,
            "budget_pressure",
            "budget_pressure",
            "Only a tiny recovery budget remains, so low-value exploration is no longer acceptable.",
            remaining_budget=reduced_budget,
            extra_tags=["budget_pressure"],
        )
    )

    return variants


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("states_jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--include-observed",
        action="store_true",
        help="include the original observed states before synthetic variants",
    )
    args = parser.parse_args()

    observed_states = load_jsonl(Path(args.states_jsonl))
    rows: list[dict[str, Any]] = []
    if args.include_observed:
        rows.extend(observed_states)
    for state in observed_states:
        rows.extend(build_variants(state))

    text = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + ("\n" if rows else "")
    Path(args.output).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
