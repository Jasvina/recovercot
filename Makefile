.PHONY: paper clean validate-sample sample-pipeline build-sample-records eval-sample build-sample-sft benchmark-samples build-sample-manifest bootstrap-sample-run launch-sample-run fetch-public-refs public-webvoyager-examples public-webvoyager-bootstrap-labels public-webvoyager-bootstrap-manifest launch-public-webvoyager-bootstrap-run

paper:
	cd paper && tectonic main.tex

clean:
	rm -f paper/main.pdf paper/main.aux paper/main.bbl paper/main.blg paper/main.log paper/main.out

validate-sample:
	python3 experiments/scripts/validate_recoverability_jsonl.py experiments/examples/sample_recoverability_record.jsonl

sample-pipeline:
	python3 experiments/scripts/sample_recoverability_states.py experiments/examples/sample_trajectory.json --output experiments/generated/sample_sampled_states.jsonl
	python3 experiments/scripts/validate_sampled_states_jsonl.py experiments/generated/sample_sampled_states.jsonl
	python3 experiments/scripts/render_teacher_requests.py experiments/generated/sample_sampled_states.jsonl --output experiments/generated/sample_teacher_requests.jsonl

build-sample-records:
	python3 experiments/scripts/build_recoverability_records.py experiments/generated/sample_sampled_states.jsonl experiments/examples/sample_teacher_outputs.jsonl --output experiments/generated/sample_recoverability_records.jsonl
	python3 experiments/scripts/validate_recoverability_jsonl.py experiments/generated/sample_recoverability_records.jsonl

eval-sample:
	python3 experiments/scripts/evaluate_recoverability_predictions.py experiments/examples/sample_gold_labels.jsonl experiments/examples/sample_pred_labels.jsonl --output experiments/generated/sample_eval_metrics.json

build-sample-sft:
	python3 experiments/scripts/build_sft_training_data.py experiments/generated/sample_sampled_states.jsonl experiments/generated/sample_recoverability_records.jsonl --output experiments/generated/sample_sft_records.jsonl

benchmark-samples:
	python3 experiments/scripts/adapt_benchmark_trajectories.py experiments/examples/raw/webvoyager_like.json --format webvoyager_like --output experiments/generated/webvoyager_like_normalized.jsonl
	python3 experiments/scripts/adapt_benchmark_trajectories.py experiments/examples/raw/mind2web_like.json --format mind2web_like --output experiments/generated/mind2web_like_normalized.jsonl
	python3 experiments/scripts/validate_trajectories_jsonl.py experiments/generated/webvoyager_like_normalized.jsonl
	python3 experiments/scripts/validate_trajectories_jsonl.py experiments/generated/mind2web_like_normalized.jsonl
	python3 experiments/scripts/dataset_stats.py experiments/generated/webvoyager_like_normalized.jsonl --output experiments/generated/webvoyager_like_stats.json
	python3 experiments/scripts/dataset_stats.py experiments/generated/mind2web_like_normalized.jsonl --output experiments/generated/mind2web_like_stats.json
	python3 experiments/scripts/sample_recoverability_states.py experiments/generated/webvoyager_like_normalized.jsonl --output experiments/generated/webvoyager_like_states.jsonl
	python3 experiments/scripts/sample_recoverability_states.py experiments/generated/mind2web_like_normalized.jsonl --output experiments/generated/mind2web_like_states.jsonl
	python3 experiments/scripts/validate_sampled_states_jsonl.py experiments/generated/webvoyager_like_states.jsonl
	python3 experiments/scripts/validate_sampled_states_jsonl.py experiments/generated/mind2web_like_states.jsonl
	python3 experiments/scripts/dataset_stats.py experiments/generated/webvoyager_like_states.jsonl --output experiments/generated/webvoyager_like_state_stats.json
	python3 experiments/scripts/dataset_stats.py experiments/generated/mind2web_like_states.jsonl --output experiments/generated/mind2web_like_state_stats.json

build-sample-manifest:
	python3 experiments/scripts/split_recoverability_dataset.py experiments/generated/sample_sft_records.jsonl --out-dir experiments/generated/sample_sft_splits
	python3 training/scripts/prepare_training_manifest.py --train-file experiments/generated/sample_sft_splits/train.jsonl --dev-file experiments/generated/sample_sft_splits/dev.jsonl --test-file experiments/generated/sample_sft_splits/test.jsonl --config training/configs/controller_lora_template.json --run-name sample_recovercot_controller --output-dir outputs/sample_recovercot_controller --metrics-file experiments/generated/sample_eval_metrics.json --output training/sample_run_manifest.json

bootstrap-sample-run:
	python3 training/scripts/bootstrap_run_dir.py training/sample_run_manifest.json --run-dir training/generated/sample_recovercot_controller
	python3 training/scripts/render_hf_sft_command.py training/sample_run_manifest.json --output training/generated/sample_recovercot_controller/train_command.sh
	chmod +x training/generated/sample_recovercot_controller/train_command.sh

launch-sample-run:
	python3 training/scripts/launch_manifest.py training/sample_run_manifest.json

fetch-public-refs:
	bash scripts/fetch_public_refs.sh

public-webvoyager-examples:
	python3 experiments/scripts/adapt_benchmark_trajectories.py /Users/weiyi/_external/recovercot_refs/WebVoyager/results/examples --format webvoyager_results_root --output experiments/generated/webvoyager_public_examples_normalized.jsonl
	python3 experiments/scripts/validate_trajectories_jsonl.py experiments/generated/webvoyager_public_examples_normalized.jsonl
	python3 experiments/scripts/dataset_stats.py experiments/generated/webvoyager_public_examples_normalized.jsonl --output experiments/generated/webvoyager_public_examples_stats.json
	python3 experiments/scripts/sample_recoverability_states.py experiments/generated/webvoyager_public_examples_normalized.jsonl --output experiments/generated/webvoyager_public_examples_states.jsonl
	python3 experiments/scripts/validate_sampled_states_jsonl.py experiments/generated/webvoyager_public_examples_states.jsonl
	python3 experiments/scripts/dataset_stats.py experiments/generated/webvoyager_public_examples_states.jsonl --output experiments/generated/webvoyager_public_examples_state_stats.json
	python3 experiments/scripts/split_recoverability_dataset.py experiments/generated/webvoyager_public_examples_states.jsonl --out-dir experiments/generated/webvoyager_public_example_state_splits
	python3 experiments/scripts/render_teacher_requests.py experiments/generated/webvoyager_public_examples_states.jsonl --output experiments/generated/webvoyager_public_example_teacher_requests.jsonl
	python3 experiments/scripts/dataset_stats.py experiments/generated/webvoyager_public_example_teacher_requests.jsonl --output experiments/generated/webvoyager_public_example_teacher_request_stats.json

public-webvoyager-bootstrap-labels:
	python3 experiments/scripts/bootstrap_teacher_outputs.py experiments/generated/webvoyager_public_examples_states.jsonl --output experiments/generated/webvoyager_public_example_bootstrap_teacher_outputs.jsonl
	python3 experiments/scripts/build_recoverability_records.py experiments/generated/webvoyager_public_examples_states.jsonl experiments/generated/webvoyager_public_example_bootstrap_teacher_outputs.jsonl --output experiments/generated/webvoyager_public_example_recoverability_records.jsonl
	python3 experiments/scripts/validate_recoverability_jsonl.py experiments/generated/webvoyager_public_example_recoverability_records.jsonl
	python3 experiments/scripts/dataset_stats.py experiments/generated/webvoyager_public_example_recoverability_records.jsonl --output experiments/generated/webvoyager_public_example_recoverability_stats.json
	python3 experiments/scripts/build_sft_training_data.py experiments/generated/webvoyager_public_examples_states.jsonl experiments/generated/webvoyager_public_example_recoverability_records.jsonl --output experiments/generated/webvoyager_public_example_sft_records.jsonl
	python3 experiments/scripts/split_recoverability_dataset.py experiments/generated/webvoyager_public_example_sft_records.jsonl --out-dir experiments/generated/webvoyager_public_example_sft_splits

public-webvoyager-bootstrap-manifest:
	python3 training/scripts/prepare_training_manifest.py --train-file experiments/generated/webvoyager_public_example_sft_splits/train.jsonl --dev-file experiments/generated/webvoyager_public_example_sft_splits/dev.jsonl --test-file experiments/generated/webvoyager_public_example_sft_splits/test.jsonl --config training/configs/controller_lora_template.json --run-name webvoyager_public_example_controller --output-dir outputs/webvoyager_public_example_controller --metrics-file experiments/generated/webvoyager_public_example_recoverability_stats.json --output training/generated/webvoyager_public_example_run_manifest.json

launch-public-webvoyager-bootstrap-run:
	python3 training/scripts/launch_manifest.py training/generated/webvoyager_public_example_run_manifest.json
