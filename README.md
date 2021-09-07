# Ansible Collection for using libvirt

This repo hosts the [`jm1.libvirt`](https://galaxy.ansible.com/jm1/libvirt) Ansible Collection.

The collection includes a variety of Ansible content to help automate the provisioning and maintenance of libvirt clusters.

It is inspired by the [Openstack Ansible modules](https://galaxy.ansible.com/openstack/cloud),
e.g. [`jm1.libvirt.domain`](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/plugins/modules/domain.py) and
[`jm1.libvirt.volume_cloudinit`](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/plugins/modules/volume_cloudinit.py)
resemble [`os_server`](https://docs.ansible.com/ansible/latest/modules/os_server_module.html) to create virtual machines
with [libvirt](https://libvirt.org/) and [cloud-init](https://cloudinit.readthedocs.io/). For example:

```yaml
- hosts: all
  tasks:
    - name: Install software required by jm1.libvirt's roles and modules
      import_role:
        name: jm1.libvirt.setup

    - name: Fetch cloud image, create storage volumes and define domain (virtual machine)
      import_role:
        name: jm1.libvirt.server
      vars:
        userdata: |
            #cloud-config
            hostname: {{ inventory_hostname }}
```

In comparison to the `virt_*` modules of the [community.libvirt Collection](https://galaxy.ansible.com/community/libvirt),
all `jm1.libvirt.*` modules are *idempotent*, that is they can be applied multiple times without changing the result
beyond the initial application. To create libvirt domains (virtual machines), storage pools or volumes you write
[`virsh`](https://libvirt.org/manpages/virsh.html)-like options in Ansible-idiomatic
[YAML lists](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html). For example:

```yaml
- jm1.libvirt.pool
    name: default
    hardware:
        # Commandline arguments of 'virsh pool-define-as' as key-value pairs without
        # the two leading dashs and all other dashs replaced by underscores.
        type: dir
        target: '/var/lib/libvirt/images'
```

No need to write XML documents as with e.g. [`virt`](https://docs.ansible.com/ansible/latest/modules/virt_module.html)
or [`virt_pool`](https://docs.ansible.com/ansible/latest/modules/virt_pool_module.html).

## Included content

Click on the name of a module or role to view that content's documentation:

- **Modules**:
    * [domain](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/plugins/modules/domain.py)
    * [net_xml](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/plugins/modules/net_xml.py)
    * [pool](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/plugins/modules/pool.py)
    * [pool_xml](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/plugins/modules/pool_xml.py)
    * [volume](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/plugins/modules/volume.py)
    * [volume_cloudinit](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/plugins/modules/volume_cloudinit.py)
    * [volume_import](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/plugins/modules/volume_import.py)
    * [volume_snapshot](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/plugins/modules/volume_snapshot.py)
- **Module Utils**:
    * [libvirt](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/plugins/module_utils/libvirt.py)
- **Roles**:
    * [server](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/roles/server/README.md)
    * [setup](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/roles/setup/README.md)

## Requirements and Installation

### Installing necessary software

Content in this collection requires additional roles and collections, e.g. to collect operating system facts. You can
fetch them from Ansible Galaxy using the provided [`requirements.yml`](requirements.yml):

```sh
ansible-galaxy collection install --requirements-file requirements.yml
ansible-galaxy role install --role-file requirements.yml
# or
make install-requirements
```

Content in this collection requires additional tools and libraries, e.g. to interact with libvirt's APIs. You can use
role [`jm1.libvirt.setup`](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/roles/setup/README.md) to 
install necessary software packages:

```yaml
- hosts: all
  roles:
    - jm1.libvirt.setup
```

Or to install these packages locally:

```sh
sudo -s
ansible localhost -m include_role -a name=jm1.libvirt.setup
```

The exact requirements for every module and role are listed in the corresponding documentation.
See the module documentations for the minimal version supported for each module.

### Installing the Collection from Ansible Galaxy

Before using the libvirt Collection, you need to install it with the Ansible Galaxy CLI:

```sh
ansible-galaxy collection install jm1.libvirt
```

You can also include it in a `requirements.yml` file and install it via
`ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: jm1.libvirt
    version: 2021.9.7
```

## Usage and Playbooks

You can either call modules by their Fully Qualified Collection Namespace (FQCN), like `jm1.libvirt.domain`, or you
can call modules by their short name if you list the `jm1.libvirt` collection in the playbook's `collections`,
like so:

```yaml
---
- name: Using jm1.libvirt collection
  hosts: localhost

  collections:
    - jm1.libvirt

  tasks:
    - name: Satisfy software requirements
      import_role:
        name: setup

    - name: Create a new libvirt domain with cloud-init
      domain:
        name: 'vm.inf.h-brs.de'
```

For documentation on how to use individual modules and other content included in this collection, please see the links
in the 'Included content' section earlier in this README.

See [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for more
details.

## Contributing

There are many ways in which you can participate in the project, for example:

- Submit bugs and feature requests, and help us verify them
- Submit pull requests for new modules, roles and other content

We're following the general Ansible contributor guidelines;
see [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html).

If you want to develop new content for this collection or improve what is already here, the easiest way to work on the
collection is to clone this repository (or a fork of it) into one of the configured [`ANSIBLE_COLLECTIONS_PATHS`](
https://docs.ansible.com/ansible/latest/reference_appendices/config.html#collections-paths) and work on it there:
1. Create a directory `ansible_collections/jm1`;
2. In there, checkout this repository (or a fork) as `libvirt`;
3. Add the directory containing `ansible_collections` to your
   [`ANSIBLE_COLLECTIONS_PATHS`](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#collections-paths).

Helpful tools for developing collections are `ansible`, `ansible-doc`, `ansible-galaxy`, `ansible-lint`, `flake8`,
`make` and `yamllint`.

| OS                                           | Install Instructions                                                |
| -------------------------------------------- | ------------------------------------------------------------------- |
| Debian 10 (Buster)                           | Enable [Backports](https://backports.debian.org/Instructions/). `apt install ansible ansible-doc ansible-lint flake8 make yamllint` |
| Debian 11 (Bullseye)                         | `apt install ansible ansible-doc ansible-lint flake8 make yamllint` |
| Red Hat Enterprise Linux (RHEL) 7 / CentOS 7 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install ansible ansible-lint ansible-doc  python-flake8 make yamllint` |
| Red Hat Enterprise Linux (RHEL) 8 / CentOS 8 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install ansible              ansible-doc python3-flake8 make yamllint` |
| Ubuntu 18.04 LTS (Bionic Beaver)             | Enable [Launchpad PPA Ansible by Ansible, Inc.](https://launchpad.net/~ansible/+archive/ubuntu/ansible). `apt install ansible ansible-doc ansible-lint flake8 make yamllint` |
| Ubuntu 20.04 LTS (Focal Fossa)               | `apt install ansible ansible-doc ansible-lint flake8 make yamllint` |

Have a look at the included [`Makefile`](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/Makefile) for
several frequently used commands, to e.g. build and lint a collection.

## More Information

- [Ansible Collection Overview](https://github.com/ansible-collections/overview)
- [Ansible User Guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer Guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Community Code of Conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)

## License

GNU General Public License v3.0 or later

See [LICENSE.md](https://galaxy.ansible.com/jm1/libvirt/blob/master/LICENSE.md) to see the full text.

## Author

Jakob Meng
@jm1 ([github](https://github.com/jm1), [galaxy](https://galaxy.ansible.com/jm1), [web](http://www.jakobmeng.de))
