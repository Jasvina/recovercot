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
- `scripts/launch_manifest.py` - bootstraps a run dir, renders the shell command, and can optionally execute it.
- `sample_run_manifest.json` - sample manifest generated from the toy pipeline.
- `generated/sample_recovercot_controller/` - bootstrapped sample run directory.

## Intended Usage

1. Produce validated recoverability records.
2. Convert them to SFT-style training records.
3. Build train/dev/test splits.
4. Generate a run manifest.
5. Bootstrap a run directory and render the first trainer command.
6. Use `launch_manifest.py` for a one-shot dry run or hand the rendered command to the actual trainer launcher.

## One-Shot Launch

```bash
python3 training/scripts/launch_manifest.py training/sample_run_manifest.json
```

This dry run refreshes `training/generated/<run_name>/` and writes a runnable `train_command.sh`.
Add `--execute` only once the local training environment already has the required trainer stack installed.

## Current Limitation

The sample run manifest is intentionally degenerate because the toy dataset contains only one task id, so all records fall into the same split bucket. This is acceptable for pipeline validation only; real runs must use multi-task data.

## Current Non-Toy Bootstrap

The repository now also emits a dry-run manifest for the imported public WebVoyager example slice:

- manifest: `generated/webvoyager_public_example_run_manifest.json`
- run dir: `generated/webvoyager_public_example_controller/`

These artifacts are still based on bootstrap silver labels from successful public traces, so they are suitable for pipeline shakeout and initial training smoke tests, not for the final paper results.
