# Ansible Role `jm1.libvirt.server`

This role helps to setup virtual machines using libvirt and cloud-init.

**Details**
- Fetches a cloud image, e.g. [`debian-*-openstack-amd64.qcow2`](https://cdimage.debian.org/cdimage/openstack/current/)
  and configures it as a libvirt storage volume
- Clones the cloud image volume to get a base storage volume for the OS
- Creates a cloud-init Config Drive with Meta-Data, User-Data and Network Configuration as a new libvirt storage volume
- Defines a libvirt domain (virtual machine) with both the OS storage volume and the cloud-init Config Drive attached

**Tested OS images**
- [Cloud image (`amd64`)](https://cdimage.debian.org/images/cloud/buster/daily/) of Debian 10 (Buster)
- [Cloud image (`amd64`)](https://cdimage.debian.org/images/cloud/bullseye/daily/) of Debian 11 (Bullseye)
- [Cloud image (`amd64`)](https://cdimage.debian.org/images/cloud/bookworm/daily/) of Debian 12 (Bookworm)
- [Cloud image (`amd64`)](https://cdimage.debian.org/images/cloud/trixie/daily/) of Debian 13 (Trixie)
- [Cloud image (`amd64`)](https://cloud.centos.org/centos/7/images/) of CentOS 7 (Core)
- [Cloud image (`amd64`)](https://cloud.centos.org/centos/8-stream/x86_64/images/) of CentOS 8 (Stream)
- [Cloud image (`amd64`)](https://cloud.centos.org/centos/9-stream/x86_64/images/) of CentOS 9 (Stream)
- [Cloud image (`amd64`)](https://download.fedoraproject.org/pub/fedora/linux/releases/40/Cloud/x86_64/images/) of Fedora Cloud Base 40
- [Cloud image (`amd64`)](https://cloud-images.ubuntu.com/bionic/current/) of Ubuntu 18.04 LTS (Bionic Beaver)
- [Cloud image (`amd64`)](https://cloud-images.ubuntu.com/focal/) of Ubuntu 20.04 LTS (Focal Fossa)
- [Cloud image (`amd64`)](https://cloud-images.ubuntu.com/jammy/) of Ubuntu 22.04 LTS (Jammy Jellyfish)
- [Cloud image (`amd64`)](https://cloud-images.ubuntu.com/noble/) of Ubuntu 24.04 LTS (Noble Numbat)

*NOTE*: `Ubuntu 20.04 LTS (Focal Fossa)` and later as well as `Debian 11 (Bullseye)` and later use
[Predictable Network Interface Names](
https://www.freedesktop.org/wiki/Software/systemd/PredictableNetworkInterfaceNames/), hence network interfaces do not
get simple names such as `eth0` assigned but e.g. `enp1s0` in a UEFI QEMU/KVM machine or `ens3` in a BIOS QEMU/KVM
machine.

Available on Ansible Galaxy in Collection [jm1.libvirt](https://galaxy.ansible.com/jm1/libvirt).

## Requirements

**NOTE**: You may use role [`jm1.libvirt.setup`](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/roles/setup/README.md)
to install all necessary software packages listed below.

Python libraries `libvirt` and `lxml` are required by Ansible modules `jm1.libvirt.*`.

| OS                                           | Install Instructions                                                                           |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Debian 10 (Buster)                           | `apt install python-libvirt python-lxml python3-libvirt python3-lxml`                          |
| Debian 11 (Bullseye)                         | `apt install python3-libvirt python3-lxml`                                                     |
| Debian 12 (Bookworm)                         | `apt install python3-libvirt python3-lxml`                                                     |
| Debian 13 (Trixie)                           | `apt install python3-libvirt python3-lxml`                                                     |
| Fedora                                       | `dnf install python3-libvirt python3-lxml` |
| Red Hat Enterprise Linux (RHEL) 7 / CentOS 7 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install libvirt-python python-lxml`   |
| Red Hat Enterprise Linux (RHEL) 8 / CentOS 8 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install python3-libvirt python3-lxml` |
| Red Hat Enterprise Linux (RHEL) 9 / CentOS 9 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install python3-libvirt python3-lxml` |
| Ubuntu 20.04 LTS (Focal Fossa)               | `apt install python3-libvirt python3-lxml`                                                     |
| Ubuntu 22.04 LTS (Jammy Jellyfish)           | `apt install python3-libvirt python3-lxml`                                                     |
| Ubuntu 24.04 LTS (Noble Numbat)              | `apt install python3-libvirt python3-lxml`                                                     |

Python library [`backports.tempfile`](https://pypi.org/project/backports.tempfile/) (Python 2 only) is required by Ansible modules `jm1.libvirt.*`.

| OS                                           | Install Instructions                                       |
| -------------------------------------------- | ---------------------------------------------------------- |
| Debian 10 (Buster)                           | `apt install python-backports.tempfile`                    |
| Debian 11 (Bullseye)                         | Not required because of Python 3                           |
| Debian 12 (Bookworm)                         | Not required because of Python 3                           |
| Debian 13 (Trixie)                           | Not required because of Python 3                           |
| Fedora                                       | Not required because of Python 3                           |
| Red Hat Enterprise Linux (RHEL) 7 / CentOS 7 | `yum install python-pip && pip install backports.tempfile` |
| Red Hat Enterprise Linux (RHEL) 8 / CentOS 8 | Not required because of Python 3                           |
| Red Hat Enterprise Linux (RHEL) 9 / CentOS 9 | Not required because of Python 3                           |
| Ubuntu 20.04 LTS (Focal Fossa)               | Not required because of Python 3                           |
| Ubuntu 22.04 LTS (Jammy Jellyfish)           | Not required because of Python 3                           |
| Ubuntu 24.04 LTS (Noble Numbat)              | Not required because of Python 3                           |

`cloud-localds` is required by Ansible module `jm1.libvirt.volume_cloudinit`.

**NOTE:** `cloud-localds` is not available on `Red Hat Enterprise Linux (RHEL) 8 / 9` and `CentOS 8 / 9`,
hence `jm1.libvirt.volume_cloudinit` cannot be used on these systems!

| OS                                           | Install Instructions                                                          |
| -------------------------------------------- | ----------------------------------------------------------------------------- |
| Debian 10 (Buster)                           | `apt install cloud-image-utils`                                               |
| Debian 11 (Bullseye)                         | `apt install cloud-image-utils`                                               |
| Debian 12 (Bookworm)                         | `apt install cloud-image-utils`                                               |
| Debian 13 (Trixie)                           | `apt install cloud-image-utils`                                               |
| Fedora                                       | `dnf install cloud-utils`                                                     |
| Red Hat Enterprise Linux (RHEL) 7 / CentOS 7 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install cloud-utils` |
| Red Hat Enterprise Linux (RHEL) 8 / CentOS 8 | :x: Not available :x:                                                         |
| Red Hat Enterprise Linux (RHEL) 9 / CentOS 9 | :x: Not available :x:                                                         |
| Ubuntu 20.04 LTS (Focal Fossa)               | `apt install cloud-image-utils`                                               |
| Ubuntu 22.04 LTS (Jammy Jellyfish)           | `apt install cloud-image-utils`                                               |
| Ubuntu 24.04 LTS (Noble Numbat)              | `apt install cloud-image-utils`                                               |

`virsh` is required by Ansible modules `jm1.libvirt.*`.

| OS                                           | Install Instructions                                                             |
| -------------------------------------------- | -------------------------------------------------------------------------------- |
| Debian 10 (Buster)                           | `apt install libvirt-clients`                                                    |
| Debian 11 (Bullseye)                         | `apt install libvirt-clients`                                                    |
| Debian 12 (Bookworm)                         | `apt install libvirt-clients`                                                    |
| Debian 13 (Trixie)                           | `apt install libvirt-clients`                                                    |
| Fedora                                       | `dnf install libvirt-client`                                                     |
| Red Hat Enterprise Linux (RHEL) 7 / CentOS 7 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install libvirt-client` |
| Red Hat Enterprise Linux (RHEL) 8 / CentOS 8 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install libvirt-client` |
| Red Hat Enterprise Linux (RHEL) 9 / CentOS 9 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install libvirt-client` |
| Ubuntu 20.04 LTS (Focal Fossa)               | `apt install libvirt-clients`                                                    |
| Ubuntu 22.04 LTS (Jammy Jellyfish)           | `apt install libvirt-clients`                                                    |
| Ubuntu 24.04 LTS (Noble Numbat)              | `apt install libvirt-clients`                                                    |

`virt-install` is required by Ansible module `jm1.libvirt.domain`.

| OS                                           | Install Instructions                                                           |
| -------------------------------------------- | ------------------------------------------------------------------------------ |
| Debian 10 (Buster)                           | `apt install virtinst`                                                         |
| Debian 11 (Bullseye)                         | `apt install virtinst`                                                         |
| Debian 12 (Bookworm)                         | `apt install virtinst`                                                         |
| Debian 13 (Trixie)                           | `apt install virtinst`                                                         |
| Fedora                                       | `dnf install virt-install`                                                     |
| Red Hat Enterprise Linux (RHEL) 7 / CentOS 7 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install virt-install` |
| Red Hat Enterprise Linux (RHEL) 8 / CentOS 8 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install virt-install` |
| Red Hat Enterprise Linux (RHEL) 9 / CentOS 9 | Enable [EPEL](https://fedoraproject.org/wiki/EPEL). `yum install virt-install` |
| Ubuntu 20.04 LTS (Focal Fossa)               | `apt install virtinst`                                                         |
| Ubuntu 22.04 LTS (Jammy Jellyfish)           | `apt install virtinst`                                                         |
| Ubuntu 24.04 LTS (Noble Numbat)              | `apt install virtinst`                                                         |

## Variables

| Name                     | Default value                                              | Required | Description                                                                                                       |
| ------------------------ | ---------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------- |
| `configdrive`            | `{{ inventory_hostname }}_cidata.{{ configdrive_format }}` | false    | Name of the Config Drive storage volume                                                                           |
| `configdrive_filesystem` | `iso`                                                      | false    | Filesystem format (vfat or iso) of Config Drive (see `man cloud-localds`)                                         |
| `configdrive_format`     | `raw`                                                      | false    | Disk format of Config Drive storage volume (see `man qemu-image` for allowed disk formats)                        |
| `distribution_id`        | *depends on operating system*                              | false    | List which uniquely identifies a distribution release, e.g. `[ 'Debian', '10' ]` for `Debian 10 (Buster)`         |
| `domain`                 | `{{ inventory_hostname }}`                                 | false    | Name of the domain (virtual machine)                                                                              |
| `hardware`               | *refer to [`roles/server/defaults/main.yml`](defaults/main.yml)* | false | Hardware of the domain. Accepts all two-dash (with leading `--`) command line arguments of `virt-install`, either as a list of plain arguments or as a dict key-value pairs without the leading `--` and having all dashs replaced by underscores |
| `image`                  | Filename of `image_uri`*                                   | false    | Name of the new storage volume where content of `image_uri` is copied to                                          |
| `image_checksum`         | *depends on `distribution_id`*                             | false    | Image checksum                                                                                                    |
| `image_format`           | Fileextension of `image_uri`                               | false    | Image file format, e.g. raw or qcow2                                                                              |
| `image_uri`              | *depends on `distribution_id`*                             | false    | Image file path (relative or absolute) or URL                                                                     |
| `metadata`               | None                                                       | false    | cloud-init Meta-Data                                                                                              |
| `networkconfig`          | None                                                       | false    | cloud-init Network Configuration                                                                                  |
| `pool`                   | `default`                                                  | false    | Name or UUID of the storage pool to create the volumes in                                                         |
| `prealloc_metadata`      | False                                                      | false    | Preallocate metadata (for qcow2 images which don't support full allocation)                                       |
| `state`                  | `present`                                                  | false    | Should the volumes and domain be `present` or `absent`                                                            |
| `uri`                    | `qemu:///system`                                           | false    | libvirt connection uri                                                                                            |
| `userdata`               | `#cloud-config\n`                                          | false    | cloud-init User-Data                                                                                              |
| `volume`                 | `{{ inventory_hostname }}.{{ volume_format }}`             | false    | Name of the OS storage volume                                                                                     |
| `volume_capacity`        | *depends on `distribution_id`*                             | false    | Size of the OS storage volume to be created, as a scaled integer (see NOTES in `man virsh`)                       |
| `volume_cow`             | False                                                      | false    | Create a copy-on-write OS storage volume that is linked to the base `image`                                       |
| `volume_format`          | `qcow2`                                                    | false    | Disk format of OS storage volume; raw, bochs, qcow, qcow2, vmdk, qed                                              |

## Dependencies

None.

## Example Playbook

```yml
- hosts: all
  become: true
  roles:
  - name: Satisfy software requirements
    role: jm1.libvirt.setup
    tags: ["jm1.libvirt.setup"]

  - name: Fetch cloud image, create storage volumes and define domain (virtual machine)
    role: jm1.libvirt.server
    tags: ["jm1.libvirt.server"]
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

GNU General Public License v3.0 or later

See [LICENSE.md](../../LICENSE.md) to see the full text.

## Author

Jakob Meng
@jm1 ([github](https://github.com/jm1), [galaxy](https://galaxy.ansible.com/jm1), [web](http://www.jakobmeng.de))
