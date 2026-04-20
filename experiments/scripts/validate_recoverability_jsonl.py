#!/usr/bin/env python3
"""Validate RecoverCoT JSONL label files with stdlib-only checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_KEYS = {
    "task_id",
    "state_id",
    "instruction",
    "history",
    "checkpoint_ids",
    "recoverability",
    "decision",
    "rollback_target",
    "teacher_rationale",
    "candidate_scores",
}
RECOVERABILITY_VALUES = {"recoverable", "weakly_recoverable", "irrecoverable"}
DECISION_VALUES = {"continue", "branch", "rollback", "restart"}


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

    if record.get("recoverability") not in RECOVERABILITY_VALUES:
        errors.append(
            f"line {lineno}: invalid recoverability: {record.get('recoverability')!r}"
        )
    if record.get("decision") not in DECISION_VALUES:
        errors.append(f"line {lineno}: invalid decision: {record.get('decision')!r}")

    rollback_target = record.get("rollback_target")
    if record.get("decision") == "rollback":
        if not isinstance(rollback_target, str) or not rollback_target:
            errors.append(
                f"line {lineno}: rollback decision requires non-empty rollback_target"
            )
    else:
        if rollback_target is not None:
            errors.append(
                f"line {lineno}: non-rollback decision must have rollback_target = null"
            )

    if not isinstance(record.get("history"), list):
        errors.append(f"line {lineno}: history must be a list")
    if not isinstance(record.get("checkpoint_ids"), list):
        errors.append(f"line {lineno}: checkpoint_ids must be a list")
    if not isinstance(record.get("candidate_scores"), dict) or not record.get("candidate_scores"):
        errors.append(f"line {lineno}: candidate_scores must be a non-empty object")
    else:
        for key, value in record["candidate_scores"].items():
            if not isinstance(key, str):
                errors.append(f"line {lineno}: candidate_scores key is not a string")
                break
            if not isinstance(value, (int, float)):
                errors.append(
                    f"line {lineno}: candidate_scores[{key!r}] must be numeric"
                )

    rationale = record.get("teacher_rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        errors.append(f"line {lineno}: teacher_rationale must be a non-empty string")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_recoverability_jsonl.py <path/to/file.jsonl>")
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
