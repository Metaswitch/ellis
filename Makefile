ROOT ?= ${PWD}
ENV_DIR := $(shell pwd)/_env
ENV_PYTHON := ${ENV_DIR}/bin/python
PYTHON_BIN := $(shell which python)

DEB_COMPONENT := ellis
DEB_MAJOR_VERSION ?= 1.0${DEB_VERSION_QUALIFIER}
DEB_NAMES := ellis ellis-node clearwater-prov-tools

MAX_LINE_LENGTH ?= 99

# As we plan to deploy on 64 bit systems, by default target 64 bit. Disable this to attempt to build on 32 bit
# Note we do not plan to support 32 bit going forward, so this may be removed in the future
X86_64_ONLY=1

.DEFAULT_GOAL = all

.PHONY: all
all: help

.PHONY: help
help:
	@cat docs/development.md

.PHONY: test
test: setup.py env
	PYTHONPATH=src:common ${ENV_DIR}/bin/python setup.py test -v

${ENV_DIR}/bin/flake8: env
	${ENV_DIR}/bin/pip install flake8

${ENV_DIR}/bin/coverage: env
	${ENV_DIR}/bin/pip install coverage

verify: ${ENV_DIR}/bin/flake8
	${ENV_DIR}/bin/flake8 --select=E10,E11,E9,F src/

style: ${ENV_DIR}/bin/flake8
	${ENV_DIR}/bin/flake8 --select=E,W,C,N --max-line-length=100 src/

explain-style: ${ENV_DIR}/bin/flake8
	${ENV_DIR}/bin/flake8 --select=E,W,C,N --show-pep8 --first --max-line-length=100 src/

EXTRA_COVERAGE="src/metaswitch/ellis/api/static.py,src/metaswitch/ellis/background.py,src/metaswitch/ellis/data/connection.py,src/metaswitch/ellis/main.py,src/metaswitch/ellis/settings.py"

.PHONY: coverage
coverage: ${ENV_DIR}/bin/coverage setup.py
	rm -rf htmlcov/
	${ENV_DIR}/bin/coverage erase
	${ENV_DIR}/bin/coverage run --source src --omit "**/test/**,**/prov_tools/**,$(EXTRA_COVERAGE)"  setup.py test
	${ENV_DIR}/bin/coverage report -m --fail-under 100
	${ENV_DIR}/bin/coverage html

.PHONY: env
env: ${ENV_DIR}/.wheelhouse_installed

BANDIT_EXCLUDE_LIST = common,src/metaswitch/ellis/test,_env,.wheelhouse,build
include build-infra/cw-deb.mk
include build-infra/python.mk

$(ENV_DIR)/bin/python: setup.py common/setup.py
	# Set up a fresh virtual environment
	virtualenv --setuptools --python=$(PYTHON_BIN) $(ENV_DIR)
	$(ENV_DIR)/bin/easy_install -U "setuptools==24"
	$(ENV_DIR)/bin/easy_install distribute

${ENV_DIR}/.wheelhouse_installed : $(ENV_DIR)/bin/python $(shell find src/metaswitch -type f -not -name "*.pyc") $(shell find common/metaswitch -type f -not -name "*.pyc")

	# Ensure we have an up to date version of pip with wheel support
	${PIP} install --upgrade pip==9.0.1
	${PIP} install wheel

	# Generate wheels
	${PYTHON} setup.py bdist_wheel -d .wheelhouse
	cd common && WHEELHOUSE=../.wheelhouse make build_common_wheel

	${PYTHON} src/metaswitch/ellis/prov_tools/setup.py bdist_wheel -d .prov_tools_wheelhouse
	cd common && WHEELHOUSE=../.prov_tools_wheelhouse make build_common_wheel

	# Download the egg files they depend upon
	${PIP} wheel -w .wheelhouse -r requirements.txt -r common/requirements.txt --find-links .wheelhouse
	${PIP} wheel -w .prov_tools_wheelhouse -r prov_tools-requirements.txt -r common/requirements.txt --find-links .prov_tools_wheelhouse

	# Install the downloaded egg files (this should match the postinst)
	${INSTALLER} --find-links .wheelhouse ellis
	${PIP} install -r common/requirements-test.txt

	# Touch the sentinel file
	touch $@

.PHONY: deb
deb: env deb-only

.PHONY: clean
clean: envclean pyclean

.PHONY: pyclean
pyclean:
	-find src -name \*.pyc -exec rm {} \;
	-rm -r src/*.egg-info
	-rm .coverage
	-rm -r htmlcov/

.PHONY: envclean
envclean:
	-rm -r .wheelhouse .prov_tools_wheelhouse build ${ENV_DIR}
