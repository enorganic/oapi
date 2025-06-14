SHELL := bash
.PHONY: docs
MINIMUM_PYTHON_VERSION := 3.9

# Create all environments
install:
	{ hatch --version || pipx install --upgrade hatch || python3 -m pip install --upgrade hatch ; } && \
	hatch env create default && \
	hatch env create docs && \
	hatch env create hatch-static-analysis && \
	hatch env create hatch-test && \
	echo "Installation complete"

# Re-create all environments, from scratch (no reference to pinned
# requirements)
reinstall:
	{ hatch --version || pipx install --upgrade hatch || python3 -m pip install --upgrade hatch ; } && \
	hatch env prune && \
	make && \
	make requirements

distribute:
	hatch build && hatch publish && rm -rf dist

# This will upgrade all requirements, and refresh pinned requirements to
# match
upgrade:
	hatch run dependence freeze\
	 --include-pointer /tool/hatch/envs/default\
	 --include-pointer /project\
	 -nv '*'\
	 pyproject.toml > .requirements.txt && \
	hatch run pip install --upgrade --upgrade-strategy eager\
	 -r .requirements.txt && \
	hatch run docs:dependence freeze\
	 --include-pointer /tool/hatch/envs/docs\
	 --include-pointer /project\
	 -nv '*'\
	 pyproject.toml > .requirements.txt && \
	hatch run docs:pip install --upgrade --upgrade-strategy eager\
	 -r .requirements.txt && \
	hatch run hatch-static-analysis:dependence freeze\
	 --include-pointer /tool/hatch/envs/docs\
	 --include-pointer /project\
	 -nv '*'\
	 pyproject.toml > .requirements.txt && \
	hatch run hatch-static-analysis:pip install --upgrade --upgrade-strategy eager\
	 -r .requirements.txt && \
	hatch run hatch-test.py$(MINIMUM_PYTHON_VERSION):dependence freeze\
	 --include-pointer /tool/hatch/envs/hatch-test\
	 --include-pointer /project\
	 -nv '*'\
	 pyproject.toml > .requirements.txt && \
	hatch run hatch-test.py$(MINIMUM_PYTHON_VERSION):pip install --upgrade --upgrade-strategy eager\
	 -r .requirements.txt && \
	hatch run hatch-test.py3.10:pip install --upgrade --upgrade-strategy eager\
	 -r .requirements.txt && \
	hatch run hatch-test.py3.11:pip install --upgrade --upgrade-strategy eager\
	 -r .requirements.txt && \
	hatch run hatch-test.py3.12:pip install --upgrade --upgrade-strategy eager\
	 -r .requirements.txt && \
	hatch run hatch-test.py3.13:pip install --upgrade --upgrade-strategy eager\
	 -r .requirements.txt && \
	rm .requirements.txt && \
	make requirements

# This will update requirement specifiers to align with the
# package versions installed in each environment, and will align the project
# dependency versions with those installed in the default environment
requirements:
	hatch run dependence update\
	 --include-pointer /tool/hatch/envs/default\
	 --include-pointer /project\
	 pyproject.toml && \
	hatch run docs:dependence update pyproject.toml --include-pointer /tool/hatch/envs/docs && \
	hatch run hatch-test.py$(MINIMUM_PYTHON_VERSION):dependence update pyproject.toml --include-pointer /tool/hatch/envs/hatch-test && \
	hatch run hatch-static-analysis:dependence update pyproject.toml --include-pointer /tool/hatch/envs/hatch-static-analysis && \
	echo "Requirements Updated"

# Test & check linting/formatting (for local use only)
test:
	{ hatch --version || pipx install --upgrade hatch || python3 -m pip install --upgrade hatch ; } && \
	hatch fmt --check && hatch run mypy && hatch test -c -vv && \
	echo "Tests Successful"

# Apply formatting rules and perform static analysis and type checking
format:
	hatch fmt --formatter
	hatch fmt --linter
	hatch run mypy && \
	echo "Formatting Successful"

# Build the documentation and serve it locally
docs:
	hatch run docs:mkdocs build && \
	hatch run docs:mkdocs serve

# Cleanup untracked files
clean:
	git clean -f -e .vscode -e .idea -x .

# Download an updated Open API document and re-generate the client and model
remodel:
	{ hatch --version || pipx install --upgrade hatch || python3 -m pip install --upgrade hatch ; } && \
	hatch run python scripts/remodel.py && \
    echo "Remodel Complete"
