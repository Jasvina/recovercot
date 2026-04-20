.PHONY: paper clean validate-sample sample-pipeline build-sample-records eval-sample build-sample-sft

paper:
	cd paper && latexmk -pdf main.tex

clean:
	cd paper && latexmk -C || true

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
	python3 experiments/scripts/evaluate_recoverability_predictions.py experiments/examples/sample_gold_labels.jsonl experiments/examples/sample_pred_labels.jsonl

build-sample-sft:
	python3 experiments/scripts/build_sft_training_data.py experiments/generated/sample_sampled_states.jsonl experiments/generated/sample_recoverability_records.jsonl --output experiments/generated/sample_sft_records.jsonl
