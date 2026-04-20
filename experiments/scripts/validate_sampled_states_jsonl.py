#!/usr/bin/env python3
"""Validate sampled-state JSONL records with stdlib-only checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_KEYS = {
    "task_id",
    "state_id",
    "source_step",
    "instruction",
    "site",
    "current_url",
    "current_observation",
    "recent_history",
    "checkpoint_candidates",
    "trigger_tags",
    "remaining_budget",
    "source_success",
}


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
    if not isinstance(record.get("state_id"), str) or not record.get("state_id"):
        errors.append(f"line {lineno}: state_id must be a non-empty string")
    if not isinstance(record.get("source_step"), int) or record.get("source_step", 0) < 1:
        errors.append(f"line {lineno}: source_step must be a positive integer")
    if not isinstance(record.get("instruction"), str) or not record.get("instruction"):
        errors.append(f"line {lineno}: instruction must be a non-empty string")
    if not isinstance(record.get("site"), str) or not record.get("site"):
        errors.append(f"line {lineno}: site must be a non-empty string")
    if not isinstance(record.get("current_url"), str) or not record.get("current_url"):
        errors.append(f"line {lineno}: current_url must be a non-empty string")
    if not isinstance(record.get("current_observation"), str) or not record.get("current_observation"):
        errors.append(f"line {lineno}: current_observation must be a non-empty string")
    if not isinstance(record.get("recent_history"), list):
        errors.append(f"line {lineno}: recent_history must be a list")
    if not isinstance(record.get("checkpoint_candidates"), list):
        errors.append(f"line {lineno}: checkpoint_candidates must be a list")
    if not isinstance(record.get("trigger_tags"), list):
        errors.append(f"line {lineno}: trigger_tags must be a list")
    if not isinstance(record.get("remaining_budget"), int) or record.get("remaining_budget", -1) < 0:
        errors.append(f"line {lineno}: remaining_budget must be a non-negative integer")
    if not isinstance(record.get("source_success"), bool):
        errors.append(f"line {lineno}: source_success must be a boolean")

    for idx, checkpoint in enumerate(record.get("checkpoint_candidates", []), start=1):
        if not isinstance(checkpoint, dict):
            errors.append(f"line {lineno}: checkpoint {idx} is not an object")
            continue
        for key in ["checkpoint_id", "step", "summary"]:
            if key not in checkpoint:
                errors.append(f"line {lineno}: checkpoint {idx} missing key {key!r}")
        if "checkpoint_id" in checkpoint and (not isinstance(checkpoint["checkpoint_id"], str) or not checkpoint["checkpoint_id"]):
            errors.append(f"line {lineno}: checkpoint {idx} has invalid checkpoint_id")
        if "step" in checkpoint and (not isinstance(checkpoint["step"], int) or checkpoint["step"] < 1):
            errors.append(f"line {lineno}: checkpoint {idx} has invalid step")
        if "summary" in checkpoint and (not isinstance(checkpoint["summary"], str) or not checkpoint["summary"]):
            errors.append(f"line {lineno}: checkpoint {idx} has invalid summary")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_sampled_states_jsonl.py <path/to/file.jsonl>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"error: file not found: {path}")
        return 2

    all_errors: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                record = json.loads(text)
            except json.JSONDecodeError as exc:
                all_errors.append(f"line {lineno}: invalid JSON: {exc}")
                continue
            all_errors.extend(validate_record(record, lineno))

    if all_errors:
        for err in all_errors:
            print(err)
        print(f"validation failed: {len(all_errors)} error(s)")
        return 1

    print(f"validation passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
