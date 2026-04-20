# Experiments

This directory holds the first concrete artifacts for RecoverCoT-style recoverability labeling and evaluation.

## Layout

- `prompts/teacher_recoverability_prompt.md` - teacher prompt template for labeling one intermediate state.
- `schemas/recoverability_record.schema.json` - JSON Schema for one recoverability record.
- `examples/sample_recoverability_record.json` - one example record following the schema.
- `examples/sample_recoverability_record.jsonl` - one-line JSONL example for validator testing.
- `scripts/validate_recoverability_jsonl.py` - stdlib-only validator for JSONL label files.

## Expected Workflow

1. Sample intermediate states from successful and failed trajectories.
2. Build candidate recovery actions/checkpoints for each state.
3. Query a teacher model with the prompt template.
4. Save one JSON object per state in JSONL format.
5. Validate the JSONL with the provided script before training.

## Suggested Output File

Use newline-delimited JSON:

```text
labels/train.jsonl
labels/dev.jsonl
labels/test.jsonl
```

Then validate with:

```bash
python3 experiments/scripts/validate_recoverability_jsonl.py labels/train.jsonl
```
