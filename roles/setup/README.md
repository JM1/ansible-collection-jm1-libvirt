# Ansible Role `jm1.libvirt.setup`

This role helps to install necessary tools and libraries for all roles and modules in collection
[jm1.libvirt](https://galaxy.ansible.com/jm1/libvirt).

**NOTE:** This role will *not* fetch and install any Ansible role or collection, because Ansible preloads all modules,
roles and tasks etc. before it executes any of them. Please make sure that all necessary roles and collections are
installed before running Ansible. To do so, you may follow the steps described in [`README.md`](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/README.md)
using the provided [`requirements.yml`](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/requirements.yml).

**NOTE:** Module [`jm1.libvirt.volume_cloudinit`](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/plugins/modules/volume_cloudinit.py)
depends on `cloud-localds`, which is not available on `Red Hat Enterprise Linux (RHEL) 8 / 9` and `CentOS 8 / 9`!

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

Available on Ansible Galaxy in Collection [jm1.libvirt](https://galaxy.ansible.com/jm1/libvirt).

## Requirements

Module `jm1.pkg.meta_pkg` from Collection [`jm1.pkg`](https://galaxy.ansible.com/jm1/pkg) is used to satisfy all package
dependencies of this Collection [jm1.libvirt](https://galaxy.ansible.com/jm1/libvirt). To install `jm1.pkg.meta_pkg` you
may follow the steps described in [`README.md`](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/README.md)
using the provided [`requirements.yml`](https://github.com/JM1/ansible-collection-jm1-libvirt/blob/master/requirements.yml).

## Variables

| Name               | Default value                           | Required | Description                                                                                               |
| ------------------ | --------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------- |
| `distribution_id`  | *depends on operating system*           | false    | List which uniquely identifies a distribution release, e.g. `[ 'Debian', '10' ]` for `Debian 10 (Buster)` |

## Dependencies

| Name            | Description                                                                         |
| --------------- | ----------------------------------------------------------------------------------- |
| `jm1.pkg.setup` | Installs necessary software for module `jm1.pkg.meta_pkg` from collection `jm1.pkg` |

## Example Playbook

```yml
- hosts: all
  become: true
  roles:
  - name: Satisfy software requirements
    role: jm1.libvirt.setup
    tags: ["jm1.libvirt.setup"]
```

For instructions on how to run Ansible playbooks have look at Ansible's
[Getting Started Guide](https://docs.ansible.com/ansible/latest/network/getting_started/first_playbook.html).

## License

GNU General Public License v3.0 or later

See [LICENSE.md](../../LICENSE.md) to see the full text.

## Author

Jakob Meng
@jm1 ([github](https://github.com/jm1), [galaxy](https://galaxy.ansible.com/jm1), [web](http://www.jakobmeng.de))
