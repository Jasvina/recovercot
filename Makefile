.PHONY: paper clean validate-sample

paper:
	cd paper && latexmk -pdf main.tex

clean:
	cd paper && latexmk -C || true

validate-sample:
	python3 experiments/scripts/validate_recoverability_jsonl.py experiments/examples/sample_recoverability_record.jsonl
