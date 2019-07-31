.PHONY: lint $(lint_targets)
files = *.ipynb
lint_targets = $(addsuffix .lint, $(files))
lint: $(lint_targets)
$(lint_targets): 
	jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace $(basename $@)
