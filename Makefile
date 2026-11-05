# Convenience targets. Python 3.8+; numpy + pandas only unless noted.
.PHONY: setup setup-starter baseline eval validate
setup:            ## scorer + baseline deps
	pip install -r requirements.txt
setup-starter:    ## + kloppy/matplotlib/jupyter for notebooks
	pip install -r requirements-starter.txt
baseline:         ## regenerate baselines (needs data/)
	python starter/baseline.py
eval:             ## score everything in evaluation/results/ on the public 5 min
	python evaluation/run_evaluation.py
validate:         ## usage: make validate F=evaluation/results/x.csv
	python evaluation/validate_submission.py $(F)
