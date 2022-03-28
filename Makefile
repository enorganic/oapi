install:
	make venv && \
	{ venv/Scripts/activate.bat || . venv/bin/activate ; } && \
	python3 -m pip install --upgrade pip && \
	python3 -m pip install\
	 -r requirements.txt\
	 -e . && \
	mypy --install-types --non-interactive ; \
	echo "Installation Finished"

# python 3.6 is used, for the time being, in order to ensure compatibility
venv:
	{ python3.6 -m venv venv || python3 -m venv venv || \
	py -3.6 -m venv venv || py -3 -m venv venv ; }

# Activate our virtual environment
activate:
	{ venv/Scripts/activate.bat || . venv/bin/activate ; }

# Install dependencies locally where available
editable:
	{ venv/Scripts/activate.bat || . venv/bin/activate ; } && \
	daves-dev-tools install-editable --upgrade-strategy eager && \
	make requirements

# Cleanup unused packages, and Git-ignored files (such as build files)
clean:
	{ venv/Scripts/activate.bat || . venv/bin/activate ; } && \
	daves-dev-tools uninstall-all\
	 -e .\
     -e pyproject.toml\
     -e tox.ini\
     -e requirements.txt && \
	daves-dev-tools clean

# Distribute to PYPI
distribute:
	{ venv/Scripts/activate.bat || . venv/bin/activate ; } && \
	daves-dev-tools distribute --skip-existing

# Upgrade
upgrade:
	{ venv/Scripts/activate.bat || . venv/bin/activate ; } && \
	daves-dev-tools requirements freeze\
	 -nv '*' . pyproject.toml tox.ini \
	 > .unversioned_requirements.txt && \
	python3 -m pip install --upgrade --upgrade-strategy eager\
	 -r .unversioned_requirements.txt -e . && \
	rm .unversioned_requirements.txt && \
	make requirements

# Update requirement version #'s to match the current environment
requirements:
	{ venv/Scripts/activate.bat || . venv/bin/activate ; } && \
	daves-dev-tools requirements update\
	 -v\
	 -aen all\
	 setup.cfg pyproject.toml tox.ini && \
	daves-dev-tools requirements freeze\
	 -nv setuptools -nv filelock -nv platformdirs\
	 . pyproject.toml tox.ini daves-dev-tools\
	 > requirements.txt

# Run all tests
test:
	{ venv/Scripts/activate.bat || . venv/bin/activate ; } && tox -r -p

# Download specification schemas
schemas:
	{ venv/Scripts/activate.bat || . venv/bin/activate ; } && \
	python3 scripts/download_schemas.py

# Rebuild the data model (to maintain consistency when/if changes are made
# which affect formatting)
remodel:
	{ venv/Scripts/activate.bat || . venv/bin/activate ; } && \
	python3 scripts/remodel.py
