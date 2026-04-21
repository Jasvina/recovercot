# Training

This directory holds the first controller-training artifacts for RecoverCoT.

## Current Scope

- lightweight LoRA/QLoRA-oriented config templates;
- run manifests that tie together data splits, output dirs, and evaluation files;
- no framework lock-in yet, so the paper repo stays portable.

## Files

- `configs/controller_lora_template.json` - baseline training hyperparameters for a 7B/8B recoverability controller.
- `scripts/prepare_training_manifest.py` - builds a run manifest from dataset files and output settings.
- `scripts/bootstrap_run_dir.py` - creates a reproducible run directory with manifest snapshots and metadata.
- `scripts/render_hf_sft_command.py` - renders a first HF/TRL-style SFT command from a run manifest.
- `sample_run_manifest.json` - sample manifest generated from the toy pipeline.
- `generated/sample_train_command.sh` - sample rendered training command.
- `generated/sample_recovercot_controller/` - bootstrapped sample run directory.

## Intended Usage

1. Produce validated recoverability records.
2. Convert them to SFT-style training records.
3. Build train/dev/test splits.
4. Generate a run manifest.
5. Bootstrap a run directory and render the first trainer command.
6. Hand the command to the actual trainer launcher in the next stage.

## Current Limitation

The sample run manifest is intentionally degenerate because the toy dataset contains only one task id, so all records fall into the same split bucket. This is acceptable for pipeline validation only; real runs must use multi-task data.
