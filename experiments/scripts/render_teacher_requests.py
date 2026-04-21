#!/usr/bin/env python3
"""Render teacher-labeling requests from sampled recoverability states."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = SCRIPT_DIR.parent


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            items.append(json.loads(line))
    return items


def candidate_list(state: dict[str, Any]) -> list[str]:
    items = ["continue", "branch"]
    for checkpoint in state.get("checkpoint_candidates", []):
        items.append(f"rollback:{checkpoint['checkpoint_id']}")
    items.append("restart")
    return items


def format_prompt(template: str, state: dict[str, Any]) -> str:
    history_lines = []
    for item in state.get("recent_history", []):
        history_lines.append(
            f"- step {item['step']}: action={item['action']} target={item['target']} value={item.get('value')} tags={item.get('tags', [])} observation={item['observation']}"
        )
    checkpoint_lines = []
    for checkpoint in state.get("checkpoint_candidates", []):
        checkpoint_lines.append(
            f"- {checkpoint['checkpoint_id']} (step {checkpoint['step']}): {checkpoint['summary']}"
        )
    candidate_lines = [f"- {name}" for name in candidate_list(state)]

    body = [template.strip(), "", "## Task Instruction", state["instruction"], "", "## Current State"]
    body.extend(
        [
            f"- task_id: {state['task_id']}",
            f"- state_id: {state['state_id']}",
            f"- state_origin: {state.get('state_origin', 'observed')}",
            f"- parent_state_id: {state.get('parent_state_id')}",
            f"- perturbation_type: {state.get('perturbation_type')}",
            f"- perturbation_note: {state.get('perturbation_note')}",
            f"- site: {state['site']}",
            f"- current_url: {state['current_url']}",
            f"- current_observation: {state['current_observation']}",
            f"- trigger_tags: {state.get('trigger_tags', [])}",
            f"- remaining_budget: {state['remaining_budget']}",
        ]
    )
    body.extend(["", "## Recent History"])
    body.extend(history_lines or ["- <empty>"])
    body.extend(["", "## Checkpoint Candidates"])
    body.extend(checkpoint_lines or ["- <none>"])
    body.extend(["", "## Candidate Recovery Options"])
    body.extend(candidate_lines)
    return "\n".join(body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("states_jsonl", help="sampled state JSONL file")
    parser.add_argument("--template", default="experiments/prompts/teacher_recoverability_prompt.md")
    parser.add_argument("--output", help="optional output JSONL path")
    args = parser.parse_args()

    states = load_jsonl(Path(args.states_jsonl))
    template_path = Path(args.template)
    if not template_path.exists():
        template_path = EXPERIMENTS_DIR / "prompts" / "teacher_recoverability_prompt.md"
    template = template_path.read_text(encoding="utf-8")
    rows = []
    for state in states:
        rows.append(
            {
                "task_id": state["task_id"],
                "state_id": state["state_id"],
                "prompt": format_prompt(template, state),
            }
        )

    text = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + ("\n" if rows else "")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
