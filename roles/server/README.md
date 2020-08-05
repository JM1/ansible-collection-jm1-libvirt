# Ansible Role: jm1.libvirt.server

This role helps to setup virtual machines using libvirt and cloud-init.

**Details**
- Builds a libvirt storage pool for the upcoming volumes
- Fetches a cloud image, e.g. [`debian-*-openstack-amd64.qcow2`](https://cdimage.debian.org/cdimage/openstack/current/)
  and configures it as a libvirt storage volume
- Clones the cloud image volume to get a base storage volume for the OS
- Creates a cloud-init Config Drive with Meta-Data, User-Data and Network Configuration as a new libvirt storage volume
- Defines a libvirt domain (virtual machine) with both the OS storage volume and the cloud-init Config Drive attached

**Tested OS images**
- Cloud image of [`Debian 10 (Buster)` \[`amd64`\]](https://cdimage.debian.org/cdimage/openstack/current/)
- Generic cloud image of [`CentOS 7 (Core)` \[`amd64`\]](https://cloud.centos.org/centos/7/images/)
- Generic cloud image of [`CentOS 8 (Core)` \[`amd64`\]](https://cloud.centos.org/centos/8/x86_64/images/)
- Ubuntu cloud image of [`Ubuntu 20.04 LTS (Focal Fossa)` \[`amd64`\]](https://cloud-images.ubuntu.com/focal/)
    *NOTE*: Ubuntu's cloud image of `Ubuntu 20.04 LTS (Focal Fossa)` uses [Predictable Network Interface Names](
            https://www.freedesktop.org/wiki/Software/systemd/PredictableNetworkInterfaceNames/), hence network
            interfaces do not get simple names such as `eth0` assigned but e.g. `enp1s0` in a UEFI QEMU/KVM machine or
            `ens3` in a BIOS QEMU/KVM machine.

Available on Ansible Galaxy in Collection [jm1.libvirt](https://galaxy.ansible.com/jm1/libvirt).

## Requirements

**NOTE**: You may use role [`jm1.libvirt.setup`](https://github.com/JM1/ansible-collection-libvirt/blob/master/roles/setup/README.md)
to install all necessary software packages listed below.

Python libraries `libvirt` and `lxml` are required by Ansible modules `jm1.libvirt.*`.

| OS                                           | Install Instructions                                                                           |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Debian 10 (Buster)                           | `apt install python-libvirt python-lxml python3-libvirt python3-lxml`                          |
| Red Hat Enterprise Linux (RHEL) 7 / CentOS 7 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install libvirt-python python-lxml`   |
| Red Hat Enterprise Linux (RHEL) 8 / CentOS 8 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install python3-libvirt python3-lxml` |
| Ubuntu 20.04 LTS (Focal Fossa)               | `apt install python3-libvirt python3-lxml`                                                     |

Python library [`backports.tempfile`](https://pypi.org/project/backports.tempfile/) (Python 2 only) is required by Ansible modules `jm1.libvirt.*`.

| OS                                           | Install Instructions                                       |
| -------------------------------------------- | ---------------------------------------------------------- |
| Debian 10 (Buster)                           | `apt install python-backports.tempfile`                    |
| Red Hat Enterprise Linux (RHEL) 7 / CentOS 7 | `yum install python-pip && pip install backports.tempfile` |
| Red Hat Enterprise Linux (RHEL) 8 / CentOS 8 | Not required because of Python 3                           |
| Ubuntu 20.04 LTS (Focal Fossa)               | Not required because of Python 3                           |

`cloud-localds` is required by Ansible module `jm1.libvirt.volume_cloudinit`.

**NOTE:** `cloud-localds` is not available on `Red Hat Enterprise Linux (RHEL) 8` and `CentOS 8`,
hence `jm1.libvirt.volume_cloudinit` cannot be used on these systems!

| OS                                           | Install Instructions                                                          |
| -------------------------------------------- | ----------------------------------------------------------------------------- |
| Debian 10 (Buster)                           | `apt install cloud-image-utils`                                               |
| Red Hat Enterprise Linux (RHEL) 7 / CentOS 7 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install cloud-utils` |
| Red Hat Enterprise Linux (RHEL) 8 / CentOS 8 | :x: Not available :x:                                                         |
| Ubuntu 20.04 LTS (Focal Fossa)               | `apt install cloud-image-utils`                                               |

`virsh` is required by Ansible modules `jm1.libvirt.*`.

| OS                                           | Install Instructions                                                             |
| -------------------------------------------- | -------------------------------------------------------------------------------- |
| Debian 10 (Buster)                           | `apt install libvirt-clients`                                                    |
| Red Hat Enterprise Linux (RHEL) 7 / CentOS 7 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install libvirt-client` |
| Red Hat Enterprise Linux (RHEL) 8 / CentOS 8 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install libvirt-client` |
| Ubuntu 20.04 LTS (Focal Fossa)               | `apt install libvirt-clients`                                                    |

`virt-install` is required by Ansible module `jm1.libvirt.domain`.

| OS                                           | Install Instructions                                                           |
| -------------------------------------------- | ------------------------------------------------------------------------------ |
| Debian 10 (Buster)                           | `apt install virtinst`                                                         |
| Red Hat Enterprise Linux (RHEL) 7 / CentOS 7 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install virt-install` |
| Red Hat Enterprise Linux (RHEL) 8 / CentOS 8 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install virt-install` |
| Ubuntu 20.04 LTS (Focal Fossa)               | `apt install virtinst`                                                         |

## Variables

| Name                     | Default value                                                | Required | Description                                                                                                       |
| ------------------------ | ------------------------------------------------------------ | -------- | ----------------------------------------------------------------------------------------------------------------- |
| `configdrive`            | `{{ inventory_hostname }}_[cidata].{{ configdrive_format }}` | no       | Name of the Config Drive storage volume                                                                           |
| `configdrive_filesystem` | `iso`                                                        | no       | Filesystem format (vfat or iso) of Config Drive (see `man cloud-localds`)                                         |
| `configdrive_format`     | `raw`                                                        | no       | Disk format of Config Drive storage volume (see `man qemu-image` for allowed disk formats)                        |
| `domain`                 | `{{ inventory_hostname }}`                                   | no       | Name of the domain (virtual machine)                                                                              |
| `hardware`               | *depends on `ansible_facts['distribution']`*                 | no       | Hardware of the domain. Accepts all two-dash (with leading `--`) command line arguments of `virt-install`, either as a list of plain arguments or as a dict key-value pairs without the leading `--` and having all dashs replaced by underscores |
| `image`                  | Filename of `image_uri`*                                     | no       | Name of the new storage volume where content of `image_uri` is copied to                                          |
| `image_checksum`         | *depends on `ansible_facts['distribution']`*                 | no       | Image checksum                                                                                                    |
| `image_format`           | Fileextension of `image_uri`                                 | no       | Image file format, e.g. raw or qcow2                                                                              |
| `image_uri`              | *depends on `ansible_facts['distribution']`*                 | no       | Image file path (relative or absolute) or URL                                                                     |
| `metadata`               | None                                                         | no       | cloud-init Meta-Data                                                                                              |
| `networkconfig`          | None                                                         | no       | cloud-init Network Configuration                                                                                  |
| `pool`                   | *depends on `ansible_facts['distribution']`*                 | no       | Name or UUID of the storage pool to create the volumes in                                                         |
| `pool_hardware`          | *depends on `ansible_facts['distribution']`*                 | no       | Hardware of the storage pool, e.g. its type. Accepts all two-dash (with leading `--`) command line arguments of `virsh pool-define-as`, either as a list of plain arguments or as a dict key-value pairs without the leading `--` and having all dashs replaced by underscores |
| `prealloc_metadata`      | False                                                        | no       | Preallocate metadata (for qcow2 images which don't support full allocation)                                       |
| `state`                  | `present`                                                    | no       | Should the volumes and domain be `present` or `absent`                                                            |
| `uri`                    | `qemu:///system`                                             | no       | libvirt connection uri                                                                                            |
| `userdata`               | `#cloud-config\n`                                            | no       | cloud-init User-Data                                                                                              |
| `volume`                 | `{{ inventory_hostname }}.{{ volume_format }}`               | no       | Name of the OS storage volume                                                                                     |
| `volume_capacity`        | *depends on `ansible_facts['distribution']`*                 | no       | Size of the OS storage volume to be created, as a scaled integer (see NOTES in `man virsh`)                       |
| `volume_cow`             | False                                                        | no       | Create a copy-on-write OS storage volume that is linked to the base `image`                                       |
| `volume_format`          | `qcow2`                                                      | no       | Disk format of OS storage volume; raw, bochs, qcow, qcow2, vmdk, qed                                              |

## Dependencies

| Name         | Description                                                                  |
| ------------ | ---------------------------------------------------------------------------- |
| `jm1.common` | Provides `distribution_id` fact which is used to choose OS-specific defaults |

## Example Playbook

```
- hosts: all
  tasks:
    - name: Satisfy software requirements
      import_role:
        name: jm1.libvirt.setup
        
    - name: Build storage pool, fetch cloud image, create storage volumes and define domain (virtual machine)
      import_role:
        name: jm1.libvirt.server
      vars:
        userdata: |
            #cloud-config

            # user-data configuration file for cloud-init
            # Ref.: https://cloudinit.readthedocs.io/

            hostname: {{ inventory_hostname }}
```

For instructions on how to run Ansible playbooks have look at Ansible's
[Getting Started Guide](https://docs.ansible.com/ansible/latest/network/getting_started/first_playbook.html).

## License

GPL3

## Author

Jakob Meng
@jm1 ([github](https://github.com/jm1), [galaxy](https://galaxy.ansible.com/jm1), [web](http://www.jakobmeng.de))
