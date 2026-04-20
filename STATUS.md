# Status

Last updated: 2026-04-20
Repository: `git@github.com:Jasvina/recovercot.git`
Branch: `main`

## Current Stage

Stage 3 of the standard research loop is now mostly closed:

1. paper framing and submission skeleton - done
2. data schema / preprocessing / offline metrics scaffold - done
3. teacher-label integration and training-data production - done on sample data
4. real benchmark ingestion - in progress next
5. model training / result population - pending

## Completed This Round

- Added a single-source progress tracker in `STATUS.md`.
- Removed the older planning note `docs_experiment_plan.md` to avoid duplicate progress surfaces.
- Added `sampled states -> teacher outputs -> recoverability records` conversion.
- Added sample teacher outputs and generated validated recoverability records.
- The sample pipeline now reaches all the way to SFT-ready JSONL.

## Already Working

- `make validate-sample`
- `make sample-pipeline`
- `make build-sample-records`
- `make eval-sample`
- `make build-sample-sft`

## Next Up

- Replace toy trajectories with real benchmark-compatible input adapters.
- Add dataset splitting/statistics utilities for real recoverability corpora.
- Start wiring training configs and run manifests for the first controller fine-tuning pass.

## Monitoring Rule

From this point on, each meaningful chunk should update this file, replace superseded status text, and be pushed to GitHub so progress is visible from the repo itself.
