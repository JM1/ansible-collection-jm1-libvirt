# vim:set syntax=make:
# kate: syntax Makefile; tab-indents on; replace-tabs off;

.DEFAULT_GOAL := all

read_yaml_key = $(shell python3 -c "import yaml; print(yaml.load(open('$(1)'))['$(2)'])")

ANSIBLE_COLLECTION_NAME := $(call read_yaml_key,"galaxy.yml","name")
ANSIBLE_COLLECTION_NAMESPACE := $(call read_yaml_key,"galaxy.yml","namespace")
ANSIBLE_COLLECTION_VERSION := $(call read_yaml_key,"galaxy.yml","version")
ANSIBLE_COLLECTION_FILE := $(ANSIBLE_COLLECTION_NAMESPACE)-$(ANSIBLE_COLLECTION_NAME)-$(ANSIBLE_COLLECTION_VERSION).tar.gz
ANSIBLE_COLLECTION_DIR := build

install-required-roles:
	ansible-galaxy role install --role-file requirements.yml
.PHONY: install-required-roles

install-required-collections:
	ansible-galaxy collection install --requirements-file requirements.yml
.PHONY: install-required-collections

install-requirements: install-required-collections install-required-roles
.PHONY: install-requirements

display-module-doc:
	@ansible-doc \
		--type module \
		jm1.libvirt.virt_domain \
		jm1.libvirt.virt_volume_snapshot \
		jm1.libvirt.virt_volume_import \
		jm1.libvirt.virt_volume_cloudinit \
		jm1.libvirt.virt_pool
.PHONY: display-module-doc

# NOTE: Keep linting targets and its options in sync with official Ansible Galaxy linters at
#       https://github.com/ansible/galaxy/blob/master/galaxy/importer/linters/__init__.py

lint-ansible-lint: # lint roles
	@ansible-lint \
		-p \
		'roles/virt_server/' \
		|| { [ "$?" = 2 ] && true; }
# ansible-lint exit code 1 is app exception, 0 is no linter err, 2 is linter err
.PHONY: lint-ansible-lint

lint-flake8: # lint modules, module_utils, plugins and roles
# NOTE: Flake8 project options have been moved to file .flake8 and hence cmd line arg '--isolated' has been dropped
	@flake8 \
		--exit-zero \
		-- \
		.
.PHONY: lint-flake8

lint-yamllint: # lint apbs und roles
	@yamllint \
		-f parsable \
		-c '.yamllint.yml' \
		-- \
		roles/virt_server/
.PHONY: lint-yamllint

lint: lint-ansible-lint lint-flake8 lint-yamllint
.PHONY: lint

$(ANSIBLE_COLLECTION_DIR)/$(ANSIBLE_COLLECTION_FILE):
	@ansible-galaxy collection build --output-path $(ANSIBLE_COLLECTION_DIR)

build-collection: $(ANSIBLE_COLLECTION_DIR)/$(ANSIBLE_COLLECTION_FILE)
.PHONY: build-collection

publish-collection:
	@ansible-galaxy collection publish $(ANSIBLE_COLLECTION_DIR)/$(ANSIBLE_COLLECTION_FILE)
.PHONY: publish-collection

all: lint build-collection
.PHONY: all
