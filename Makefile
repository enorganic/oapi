SHELL := bash

install:
	{ rm -R venv || echo "" ; } && \
	{ python3.8 -m venv venv || py -3.8 -m venv venv ; } && \
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	{ pip3 install --upgrade pip || echo "" ; } && \
	pip3 install\
	 -r requirements.txt\
	 -e . && \
	{ mypy --install-types --non-interactive || echo "" ; } && \
	echo "Success!"

ci-install:
	{ python3 -m venv venv || py -3 -m venv venv ; } && \
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	{ python3 -m pip install --upgrade pip || echo "" ; } && \
	python3 -m pip install\
	 -r requirements.txt\
	 -e . && \
	{ mypy --install-types --non-interactive || echo "" ; } && \
	echo "Success!"

# Install dependencies locally where available
editable:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools install-editable --upgrade-strategy eager && \
	make requirements && \
	echo "Success!"

# Cleanup unused packages, and Git-ignored files (such as build files)
clean:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools uninstall-all\
	 -e .\
     -e pyproject.toml\
     -e tox.ini\
     -e requirements.txt && \
	daves-dev-tools clean && \
	echo "Success!"

# Distribute to PYPI
distribute:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools distribute --skip-existing && \
	echo "Success!"

# Upgrade
upgrade:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools requirements freeze\
	 -e pip\
	 -e wheel\
	 -nv '*' . pyproject.toml tox.ini \
	 > .requirements.txt && \
	pip3 install --upgrade --upgrade-strategy eager\
	 -r .requirements.txt && \
	rm .requirements.txt && \
	make requirements

# Update requirement version #'s to match the current environment
requirements:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	daves-dev-tools requirements update\
	 -i more-itertools -aen all\
	 setup.cfg pyproject.toml tox.ini && \
	daves-dev-tools requirements freeze\
	 -nv setuptools -nv filelock -nv platformdirs\
	 -e pip\
	 . pyproject.toml tox.ini daves-dev-tools\
	 > requirements.txt && \
	echo "Success!"

# Run all tests
test:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	[[ "$$(python -V)" = "Python 3.8."* ]] && python3 -m tox -r -p -o || python3 -m tox -r -e pytest

# Download specification schemas
schemas:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	python3 scripts/download_schemas.py && \
	echo "Success!"

# Rebuild the data model (to maintain consistency when/if changes are made
# which affect formatting)
remodel:
	{ . venv/bin/activate || venv/Scripts/activate.bat ; } && \
	python3 scripts/remodel.py && \
	echo "Success!"
