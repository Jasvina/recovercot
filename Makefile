.PHONY: paper clean

paper:
	cd paper && latexmk -pdf main.tex

clean:
	cd paper && latexmk -C || true
