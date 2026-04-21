# Training

This directory holds the first controller-training artifacts for RecoverCoT.

## Current Scope

- lightweight LoRA/QLoRA-oriented config templates;
- run manifests that tie together data splits, output dirs, and evaluation files;
- no framework lock-in yet, so the paper repo stays portable.

## Files

- `configs/controller_lora_template.json` - baseline training hyperparameters for a 7B/8B recoverability controller.
- `scripts/prepare_training_manifest.py` - builds a run manifest from dataset files and output settings.
- `sample_run_manifest.json` - sample manifest generated from the toy pipeline.

## Intended Usage

1. Produce validated recoverability records.
2. Convert them to SFT-style training records.
3. Build train/dev/test splits.
4. Generate a run manifest.
5. Hand the manifest to the actual trainer launcher in the next stage.

## Current Limitation

The sample run manifest is intentionally degenerate because the toy dataset contains only one task id, so all records fall into the same split bucket. This is acceptable for pipeline validation only; real runs must use multi-task data.
