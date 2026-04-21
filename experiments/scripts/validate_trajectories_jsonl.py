#!/usr/bin/env python3
"""Validate normalized trajectory JSONL records with stdlib-only checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_KEYS = {"task_id", "instruction", "site", "success", "max_steps", "steps"}
STEP_KEYS = {"step", "url", "action_type", "action", "target", "observation", "tags", "checkpoint"}


def validate_record(record: object, lineno: int) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"line {lineno}: record is not a JSON object"]
    missing = REQUIRED_KEYS - set(record)
    extra = set(record) - REQUIRED_KEYS
    if missing:
        errors.append(f"line {lineno}: missing keys: {sorted(missing)}")
    if extra:
        errors.append(f"line {lineno}: unexpected keys: {sorted(extra)}")

    if not isinstance(record.get("task_id"), str) or not record.get("task_id"):
        errors.append(f"line {lineno}: task_id must be a non-empty string")
    if not isinstance(record.get("instruction"), str) or not record.get("instruction"):
        errors.append(f"line {lineno}: instruction must be a non-empty string")
    if not isinstance(record.get("site"), str) or not record.get("site"):
        errors.append(f"line {lineno}: site must be a non-empty string")
    if not isinstance(record.get("success"), bool):
        errors.append(f"line {lineno}: success must be a boolean")
    if not isinstance(record.get("max_steps"), int) or record.get("max_steps", 0) < 1:
        errors.append(f"line {lineno}: max_steps must be a positive integer")

    steps = record.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append(f"line {lineno}: steps must be a non-empty list")
        return errors

    prev_step = 0
    for idx, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            errors.append(f"line {lineno}: step {idx} is not an object")
            continue
        missing_step = STEP_KEYS - set(step)
        if missing_step:
            errors.append(f"line {lineno}: step {idx} missing keys: {sorted(missing_step)}")
        if "step" in step:
            if not isinstance(step["step"], int) or step["step"] < 1:
                errors.append(f"line {lineno}: step {idx} has invalid step number")
            elif step["step"] <= prev_step:
                errors.append(f"line {lineno}: steps are not strictly increasing at step {idx}")
            prev_step = step["step"]
        for key in ["url", "action_type", "action", "target", "observation"]:
            if key in step and (not isinstance(step[key], str) or not step[key]):
                errors.append(f"line {lineno}: step {idx} has invalid {key}")
        if "tags" in step and not isinstance(step["tags"], list):
            errors.append(f"line {lineno}: step {idx} tags must be a list")
        if "checkpoint" in step and not isinstance(step["checkpoint"], bool):
            errors.append(f"line {lineno}: step {idx} checkpoint must be a boolean")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_trajectories_jsonl.py <path/to/file.jsonl>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"error: file not found: {path}")
        return 2
    errors: list[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {lineno}: invalid JSON: {exc}")
            continue
        errors.extend(validate_record(row, lineno))
    if errors:
        for err in errors:
            print(err)
        print(f"validation failed: {len(errors)} error(s)")
        return 1
    print(f"validation passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
