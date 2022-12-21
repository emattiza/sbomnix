# SPDX-FileCopyrightText: 2022 Technology Innovation Institute (TII)
#
# SPDX-License-Identifier: Apache-2.0

export PYTHONPATH := $(PYTHONPATH):$(shell pwd)

define target_success
	@printf "\033[32m==> Target \"$(1)\" passed\033[0m\n\n"
endef

.DEFAULT_GOAL := help

TARGET: ## DESCRIPTION
	@echo "TARGET is here only to provide the header for 'help'"

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[32m%-30s\033[0m %s\n", $$1, $$2}'

install: install-requirements ## Install sbomnix
	pip3 install .
	@if ! sbomnix -h 2>/dev/null; then \
		echo "\033[31mError:\033[0m failed to run sbomnix, maybe it's not in your PATH?"; \
		exit 1; \
	fi
	$(call target_success,$@)

uninstall: clean ## Uninstall sbomnix
	pip3 uninstall -y sbomnix 
	$(call target_success,$@)

install-requirements: ## Install all requirements
	pip3 install -q -r requirements.txt --no-cache-dir
	$(call target_success,$@)

pre-push: test black style pylint reuse-lint  ## Run tests, pycodestyle, pylint, reuse-lint
	$(call target_success,$@)

test: install-requirements ## Run tests
	pytest -vx tests/
	$(call target_success,$@)

black: clean ## Reformat with black
	@for py in $(shell find . -path ./venv -prune -false -o -name "*.py"); \
		do echo "$$py:"; \
		black -q $$py; \
	done
	$(call target_success,$@)

style: clean ## Check with pycodestyle (pep8)
	pycodestyle --max-line-length 90 --exclude='venv/' .
	$(call target_success,$@)

pylint: clean ## Check with pylint
	@for py in $(shell find . -path ./venv -prune -false -o -name "*.py"); do \
		echo "$$py:"; \
		pylint -rn $$py || exit 1 ; \
	done
	$(call target_success,$@)

reuse-lint: clean ## Check with reuse lint
	reuse lint
	$(call target_success,$@)

clean: clean-pyc ## Remove all artifacts
	$(call target_success,$@)

clean-pyc: ## Remove Python artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '.eggs' -exec rm -rf {} +
	rm -fr dist/
	rm -fr build/
