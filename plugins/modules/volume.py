#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:set fileformat=unix shiftwidth=4 softtabstop=4 expandtab:
# kate: end-of-line unix; space-indent on; indent-width 4; remove-trailing-space on;

# Copyright: (c) 2020, Jakob Meng <jakobmeng@web.de>
# Based on community.libvirt.virt_pool module written by Maciej Delmanowski <drybjed@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# TODO: Merge 'volume' and 'volume_snapshot' modules?!

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---

module: volume

short_description: Create/Delete a libvirt storage volume.

description:
    - "This module allows one to create a libvirt storage volume.
       It is based on Ansible module community.libvirt.virt_pool from Maciej Delmanowski <drybjed@gmail.com>."

requirements: []

options:
    pool:
        description:
            - "Name or UUID of the storage pool to create the volume in."
        required: true
        type: str
    name:
        description:
            - "Name of the new volume. For a disk pool, this must match the partition name as determined from the pool's
               source device path and the next available partition. For example, a source device path of /dev/sdb and
               there are no partitions on the disk, then the name must be sdb1 with the next name being sdb2 and so on."
        required: true
        type: str
    capacity:
        description:
            - "Size of the volume to be created, as a scaled integer (see NOTES in `man virsh`), defaulting to size of
               backing volume and defaulting to bytes if there is no suffix.
               Required if C(state) is C(present)."
        required: false
        type: str
    format:
        description:
            - "Used in file based storage pools to specify the volume file format to use; raw, bochs, qcow, qcow2, vmdk,
               qed. Use extended for disk storage pools in order to create an extended partition (other values are
               validity checked but not preserved when libvirtd is restarted or the pool is refreshed)."
        required: false
        type: str
    prealloc_metadata:
        default: false
        description:
            - "Preallocate metadata (for qcow2 images which don't support full allocation). This option creates a sparse
               image file with metadata, resulting in higher performance compared to images with no preallocation and
               only slightly higher initial disk space usage."
        required: false
        type: bool
    state:
        choices: [present, absent]
        default: present
        description:
            - "Should the volume be present or absent."
        type: str

notes:
  - "No modifications are applied to existing volumes; module is skipped if volume exists already."

extends_documentation_fragment:
  - jm1.libvirt.libvirt

author: "Jakob Meng (@jm1)"
'''

EXAMPLES = r'''
- name: Create a volume
  jm1.libvirt.volume:
    pool: "default"
    name: "data.qcow2"
    capacity: 10GB
'''

RETURN = r'''
'''

# NOTE: Synchronize imports with DOCUMENTATION string above and chapter Requirements in roles/server/README.md
from ansible_collections.jm1.libvirt.plugins.module_utils import libvirt as libvirt_utils
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule, human_to_bytes
import traceback


def create(uri,
           pool_name,
           volume_name,
           volume_capacity,
           volume_format,
           prealloc_metadata,
           module):
    with libvirt_utils.Connection(uri, module) as conn:
        pool = conn.storagePoolLookupByName(pool_name)

        if volume_name in pool.listVolumes():
            # volume exists already
            volume = pool.storageVolLookupByName(volume_name)
            volume_type, volume_capacity, volume_allocation = volume.info()
            return False, volume_capacity, volume_format

        cmd = """
            virsh
                --connect '{uri}'
                vol-create-as
                '{pool_name}'
                '{volume_name}'
                '{volume_capacity}'
            """

        if volume_format:
            cmd += "--format '{volume_format}'"

        if prealloc_metadata:
            cmd += '--prealloc-metadata'

        cmd = cmd.replace('\n', ' ')

        cmd = cmd.format(
            uri=uri,
            pool_name=pool_name,
            volume_name=volume_name,
            volume_capacity=volume_capacity,
            volume_format=volume_format)

        rc, stdout, stderr = module.run_command(cmd, check_rc=True)
        return True, volume_capacity, volume_format


def delete(uri,
           pool_name,
           volume_name,
           volume_capacity,
           volume_format,
           prealloc_metadata,
           module):
    with libvirt_utils.Connection(uri, module) as conn:
        pools = conn.listAllStoragePools()
        pool = next((pool for pool in pools if pool.name() == pool_name), None)
        if not pool:
            # pool absent already and hence volume as well
            return False, None, None

        if not volume_name:
            raise ValueError('name is required for deleting volumes')

        if volume_name not in pool.listVolumes():
            # volume absent already
            return False, None, None

        volume = pool.storageVolLookupByName(volume_name)
        volume_type, volume_capacity, volume_allocation = volume.info()
        volume.delete()
        return True, volume_capacity, volume_format


def core(module):
    state = module.params['state']
    uri = module.params['uri']
    pool_name = module.params['pool']
    volume_name = module.params['name']
    volume_capacity = module.params['capacity']
    volume_format = module.params['format']
    prealloc_metadata = module.params['prealloc_metadata']

    if module.check_mode:
        return dict(
            changed=False,
            state=state,
            uri=uri,
            pool=pool_name,
            name=volume_name,
            capacity=volume_capacity,
            format=volume_format,
            prealloc_metadata=prealloc_metadata)

    if state == 'present':
        changed, volume_capacity, volume_format = create(
            uri,
            pool_name,
            volume_name, human_to_bytes(volume_capacity) if volume_capacity else None, volume_format,
            prealloc_metadata,
            module)
    elif state == 'absent':
        changed, volume_capacity, volume_format = delete(
            uri,
            pool_name,
            volume_name, human_to_bytes(volume_capacity) if volume_capacity else None, volume_format,
            prealloc_metadata,
            module)

    return dict(
        changed=changed,
        state=state,
        uri=uri,
        pool=pool_name,
        name=volume_name,
        capacity=volume_capacity,
        format=volume_format,
        prealloc_metadata=prealloc_metadata)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            uri=dict(default='qemu:///system'),
            pool=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            capacity=dict(type='str'),
            format=dict(type='str'),
            prealloc_metadata=dict(type='bool', default=False)
        ),
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['capacity']]
        ]
    )

    libvirt_utils.try_import(module)

    try:
        result = core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
