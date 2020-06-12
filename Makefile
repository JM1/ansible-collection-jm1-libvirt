# vim:set syntax=make:
# kate: syntax Makefile; tab-indents on; replace-tabs off;

.DEFAULT_GOAL := all

install-required-roles:
	ansible-galaxy role install --role-file requirements.yml
.PHONY: install-required-roles

install-required-collections:
	ansible-galaxy collection install --requirements-file requirements.yml
.PHONY: install-required-collections

install-requirements: install-required-collections install-required-roles
.PHONY: install-requirements

all: ;
.PHONY: all
