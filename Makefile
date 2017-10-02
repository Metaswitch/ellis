ROOT ?= ${PWD}
ENV_DIR := $(shell pwd)/_env
PYTHON_BIN := $(shell which python)

DEB_COMPONENT := ellis
DEB_MAJOR_VERSION ?= 1.0${DEB_VERSION_QUALIFIER}
DEB_NAMES := ellis ellis-node clearwater-prov-tools

# As we plan to deploy on 64 bit systems, by default target 64 bit. Disable this to attempt to build on 32 bit
# Note we do not plan to support 32 bit going forward, so this may be removed in the future
X86_64_ONLY=1

.DEFAULT_GOAL = all

FLAKE8_INCLUDE_DIR = src/
COVERAGE_SRC_DIR = src
COVERAGE_EXCL = "**/test/**,**/prov_tools/**,src/metaswitch/ellis/api/static.py,src/metaswitch/ellis/background.py,src/metaswitch/ellis/data/connection.py,src/metaswitch/ellis/main.py,src/metaswitch/ellis/settings.py"
BANDIT_EXCLUDE_LIST = common,src/metaswitch/ellis/test,_env,.wheelhouse,build
CLEAN_SRC_DIR = src
TEST_REQUIREMENTS = common/requirements-test.txt

include build-infra/cw-deb.mk
include build-infra/python.mk

# Ellis wheel

# Add a target that builds the python-common wheel into the correct wheelhouse
${ENV_DIR}/.ellis_build_common_wheel: common/requirements.txt $(shell find common/metaswitch -type f -not -name "*.pyc")
	cd common && WHEELHOUSE=../ellis_wheelhouse make build_common_wheel
	touch $@

# Add dependency to the install-wheels to ensure we also install the python-common wheel
${ENV_DIR}/.ellis-install-wheels: ${ENV_DIR}/.ellis_build_common_wheel

# Set up the variables for Ellis
ellis_SETUP = setup.py
ellis_REQUIREMENTS = requirements.txt common/requirements.txt
ellis_SOURCES = $(shell find src/metaswitch -type f -not -name "*.pyc") $(shell find common/metaswitch -type f -not -name "*.pyc")
ellis_WHEELS = ellis

# Create targets using the common python_component macro
$(eval $(call python_component,ellis))

# Prov-tools wheel

# Add a target that builds the python-common wheel into the correct wheelhouse
${ENV_DIR}/.prov_tools_build_common_wheel: common/requirements.txt $(shell find common/metaswitch -type f -not -name "*.pyc")
	cd common && WHEELHOUSE=../prov_tools_wheelhouse make build_common_wheel
	touch $@

# Add dependency to the install-wheels to ensure we also install the python-common wheel
${ENV_DIR}/.prov_tools-install-wheels: ${ENV_DIR}/.prov_tools_build_common_wheel

# Setup up the variables for prov-tools
prov_tools_SETUP = src/metaswitch/ellis/prov_tools/setup.py
prov_tools_REQUIREMENTS = prov_tools-requirements.txt common/requirements.txt
prov_tools_SOURCES = $(shell find src/metaswitch -type f -not -name "*.pyc") $(shell find common/metaswitch -type f -not -name "*.pyc")

# Create targets using the common python_component macro
$(eval $(call python_component,prov_tools))

.PHONY: all
all: help

.PHONY: help
help:
	@cat docs/development.md

.PHONY: deb
deb: env deb-only

