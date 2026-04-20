#!/usr/bin/env python3
"""Evaluate offline recoverability predictions against gold JSONL labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_KEYS = {"state_id", "recoverability", "decision", "rollback_target"}


def load_jsonl(path: Path) -> dict[str, dict]:
    records = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = line.strip()
        if not text:
            continue
        row = json.loads(text)
        missing = REQUIRED_KEYS - set(row)
        if missing:
            raise ValueError(f"{path}:{lineno}: missing keys {sorted(missing)}")
        records[row["state_id"]] = row
    return records


def safe_div(num: float, den: float) -> float:
    return 0.0 if den == 0 else num / den


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gold_jsonl")
    parser.add_argument("pred_jsonl")
    args = parser.parse_args()

    gold = load_jsonl(Path(args.gold_jsonl))
    pred = load_jsonl(Path(args.pred_jsonl))
    shared_ids = sorted(set(gold) & set(pred))
    missing_pred = sorted(set(gold) - set(pred))
    extra_pred = sorted(set(pred) - set(gold))

    rec_correct = 0
    decision_correct = 0
    rollback_target_correct = 0
    gold_rollbacks = 0
    predicted_rollbacks = 0
    correct_rollback_decisions = 0
    unnecessary_rollbacks = 0

    for state_id in shared_ids:
        g = gold[state_id]
        p = pred[state_id]
        if p["recoverability"] == g["recoverability"]:
            rec_correct += 1
        if p["decision"] == g["decision"]:
            decision_correct += 1
        if g["decision"] == "rollback":
            gold_rollbacks += 1
            if p["decision"] == "rollback" and p["rollback_target"] == g["rollback_target"]:
                rollback_target_correct += 1
        if p["decision"] == "rollback":
            predicted_rollbacks += 1
            if g["decision"] == "rollback":
                correct_rollback_decisions += 1
            else:
                unnecessary_rollbacks += 1

    total = len(shared_ids)
    metrics = {
        "num_gold": len(gold),
        "num_pred": len(pred),
        "num_scored": total,
        "missing_predictions": missing_pred,
        "extra_predictions": extra_pred,
        "recoverability_accuracy": round(safe_div(rec_correct, total), 4),
        "decision_accuracy": round(safe_div(decision_correct, total), 4),
        "rollback_target_accuracy": round(safe_div(rollback_target_correct, gold_rollbacks), 4),
        "rollback_decision_precision": round(safe_div(correct_rollback_decisions, predicted_rollbacks), 4),
        "unnecessary_rollback_rate": round(safe_div(unnecessary_rollbacks, predicted_rollbacks), 4),
    }
    print(json.dumps(metrics, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
