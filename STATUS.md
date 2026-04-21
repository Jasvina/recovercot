# Status

Last updated: 2026-04-20
Repository: `git@github.com:Jasvina/recovercot.git`
Branch: `main`

## Current Stage

Stage 4 has started:

1. paper framing and submission skeleton - done
2. data schema / preprocessing / offline metrics scaffold - done
3. teacher-label integration and training-data production - done on sample data
4. benchmark-facing ingestion, stats, and run manifests - in progress
5. model training / result population - next

## Completed This Round

- Added benchmark-facing raw adapters for `webvoyager_like` and `mind2web_like` inputs.
- Added normalized-trajectory validation, dataset stats, and deterministic dataset splitting utilities.
- Added training config and run-manifest scaffolding under `training/`.
- Generated benchmark-style normalized samples, state samples, stats JSONs, and a sample training manifest.

## Already Working

- `make validate-sample`
- `make sample-pipeline`
- `make build-sample-records`
- `make eval-sample`
- `make build-sample-sft`
- `make benchmark-samples`
- `make build-sample-manifest`

## Next Up

- Replace benchmark-like toy adapters with real dataset importers once raw benchmark files are available locally.
- Add trainer launcher glue for the first controller fine-tuning run.
- Populate real train/dev/test splits with multi-task data so the manifest is non-degenerate.

## Monitoring Rule

From this point on, each meaningful chunk should update this file, replace superseded status text, and be pushed to GitHub so progress is visible from the repo itself.
