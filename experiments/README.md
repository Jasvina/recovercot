# Experiments

This directory holds the first concrete artifacts for RecoverCoT-style recoverability labeling and evaluation.

## Layout

- `prompts/teacher_recoverability_prompt.md` - teacher prompt template for labeling one intermediate state.
- `schemas/recoverability_record.schema.json` - JSON Schema for one recoverability record.
- `schemas/trajectory_record.schema.json` - schema for raw or replayed trajectory inputs.
- `schemas/sampled_state_record.schema.json` - schema for sampled intermediate recoverability states.
- `examples/sample_recoverability_record.json` - one example record following the schema.
- `examples/sample_recoverability_record.jsonl` - one-line JSONL example for validator testing.
- `examples/sample_trajectory.json` - one sample trajectory for the preprocessing pipeline.
- `examples/sample_gold_labels.jsonl` - toy gold labels for offline metric testing.
- `examples/sample_pred_labels.jsonl` - toy predictions for offline metric testing.
- `examples/sample_teacher_outputs.jsonl` - toy teacher responses for sampled states.
- `generated/sample_sampled_states.jsonl` - sampled states generated from the sample trajectory.
- `generated/sample_recoverability_records.jsonl` - validated recoverability records built from teacher outputs.
- `generated/sample_teacher_requests.jsonl` - rendered teacher prompts for sampled states.
- `generated/sample_sft_records.jsonl` - SFT-style training records built from sampled states and labels.
- `scripts/validate_recoverability_jsonl.py` - stdlib-only validator for JSONL label files.
- `scripts/validate_sampled_states_jsonl.py` - stdlib-only validator for sampled-state JSONL files.
- `scripts/sample_recoverability_states.py` - heuristic sampler from trajectory data to sampled states.
- `scripts/render_teacher_requests.py` - prompt renderer from sampled states to teacher requests.
- `scripts/evaluate_recoverability_predictions.py` - offline metric calculator for gold vs predicted labels.
- `scripts/build_sft_training_data.py` - converter from sampled states plus labels into SFT-style JSONL.
- `scripts/build_recoverability_records.py` - merges sampled states with teacher outputs into validated recoverability records.

## Expected Workflow

1. Sample intermediate states from successful and failed trajectories.
2. Build candidate recovery actions/checkpoints for each state.
3. Query a teacher model with the prompt template.
4. Save one JSON object per state in JSONL format.
5. Validate the JSONL with the provided script before training.

## Sample End-to-End Run

```bash
python3 experiments/scripts/sample_recoverability_states.py \
  experiments/examples/sample_trajectory.json \
  --output experiments/generated/sample_sampled_states.jsonl

python3 experiments/scripts/validate_sampled_states_jsonl.py \
  experiments/generated/sample_sampled_states.jsonl

python3 experiments/scripts/render_teacher_requests.py \
  experiments/generated/sample_sampled_states.jsonl \
  --output experiments/generated/sample_teacher_requests.jsonl

python3 experiments/scripts/build_recoverability_records.py \
  experiments/generated/sample_sampled_states.jsonl \
  experiments/examples/sample_teacher_outputs.jsonl \
  --output experiments/generated/sample_recoverability_records.jsonl

python3 experiments/scripts/validate_recoverability_jsonl.py \
  experiments/generated/sample_recoverability_records.jsonl

python3 experiments/scripts/evaluate_recoverability_predictions.py \
  experiments/examples/sample_gold_labels.jsonl \
  experiments/examples/sample_pred_labels.jsonl

python3 experiments/scripts/build_sft_training_data.py \
  experiments/generated/sample_sampled_states.jsonl \
  experiments/generated/sample_recoverability_records.jsonl \
  --output experiments/generated/sample_sft_records.jsonl
```

The last command reports offline proxy metrics such as recoverability accuracy, decision accuracy, rollback-target accuracy, rollback-decision precision, and unnecessary rollback rate.

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
