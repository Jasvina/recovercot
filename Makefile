.PHONY: paper clean validate-sample sample-pipeline eval-sample build-sample-sft

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

eval-sample:
	python3 experiments/scripts/evaluate_recoverability_predictions.py experiments/examples/sample_gold_labels.jsonl experiments/examples/sample_pred_labels.jsonl

build-sample-sft:
	python3 experiments/scripts/build_sft_training_data.py experiments/generated/sample_sampled_states.jsonl experiments/examples/sample_gold_labels.jsonl --output experiments/generated/sample_sft_records.jsonl
