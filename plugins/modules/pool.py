#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:set fileformat=unix shiftwidth=4 softtabstop=4 expandtab:
# kate: end-of-line unix; space-indent on; indent-width 4; remove-trailing-spaces modified;

# Copyright: (c) 2020, Jakob Meng <jakobmeng@web.de>
# Based on community.libvirt.virt_pool module written by Maciej Delmanowski <drybjed@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---

module: pool

short_description: Create/Delete libvirt storage pools.

description:
    - "This module allows one to manage libvirt storage pools.
       It is based on Ansible module community.libvirt.virt_pool from Maciej Delmanowski <drybjed@gmail.com>."

requirements:
   - virsh (e.g. in debian package libvirt-clients)

options:
    name:
        description:
            - "Name or UUID of the storage pool."
        required: true
        type: str
    hardware:
        description:
            - "Hardware of the storage pool. Accepts all two-dash command line arguments (those with a leading '--') of
               'virsh pool-define-as' as a list. Arguments are formatted as key-value pairs without the leading '--' and
               having other dashs replaced by underscores. Arguments without a value (flags), e.g. overwrite, must
               be specified with a value of !!null. For the complete list of supported arguments see 'man virsh'.
               Supported storage pool types are documented at U(https://libvirt.org/formatstorage.html)."
        required: false
        type: list
    state:
        choices: [present, absent]
        default: present
        description:
            - "Should the pool be present or absent."
        type: str

notes:
  - "No modifications are applied to existing pools; module is skipped if pool exists already."

extends_documentation_fragment:
  - jm1.libvirt.libvirt

author: "Jakob Meng (@jm1)"
'''

EXAMPLES = r'''
- jm1.libvirt.pool:
    name: default
    hardware: [{ 'type': 'dir', 'target': '/var/lib/libvirt/images' }]
'''

RETURN = r'''
capacity:
    description: Logical size bytes
    returned: changed or success
    type: int
    sample: 536392192

allocation:
    description: Current allocation bytes
    returned: changed or success
    type: int
    sample: 536392192

available:
    description: Remaining free space bytes
    returned: changed or success
    type: int
    sample: 536392192
'''

# NOTE: Synchronize imports with DOCUMENTATION string above and chapter Requirements in roles/server/README.md
from ansible_collections.jm1.libvirt.plugins.module_utils import libvirt as libvirt_utils
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
import time
import traceback

try:
    import libvirt
except ImportError:
    # error handled in libvirt_utils.try_import() below
    pass


def create(uri,
           pool_name,
           pool_hardware,
           module):

    with libvirt_utils.Connection(uri, module) as conn:
        pools = conn.listAllStoragePools()
        pool = next((pool for pool in pools if pool.name() == pool_name), None)
        if pool:
            # Pool present already
            if not pool.isActive():
                pool.create(0)

            pool_state, pool_capacity, pool_allocation, pool_available = pool.info()
            return False, pool_capacity, pool_allocation, pool_available

        virsh_args = libvirt_utils.to_cli_args(pool_hardware)

        # Remove forbidden args
        for arg in ['--build', '--print-xml']:
            virsh_args = list(filter(lambda x: x != arg, virsh_args))

        # Create, start and build pool
        cmd = """
            virsh
                --connect '{uri}'
                pool-define-as
                --name '{pool_name}'
                {virsh_args}
            """.replace('\n', ' ').format(uri=uri,
                                          pool_name=pool_name,
                                          virsh_args=' '.join(virsh_args))

        module.run_command(cmd, check_rc=True)

        try:
            # Wait until pool has been created
            while True:

                try:
                    pool = conn.storagePoolLookupByName(pool_name)
                    break
                except libvirt.libvirtError as e:
                    if e.get_error_code() != 49:  # VIR_ERR_NO_STORAGE_POOL
                        raise
                time.sleep(1)

            # enum virStoragePoolCreateFlags {
            #     VIR_STORAGE_POOL_CREATE_NORMAL                  = 0 (0x0)         : Create the pool and perform pool build without any flags
            #     VIR_STORAGE_POOL_CREATE_WITH_BUILD              = 1 (0x1; 1 << 0) : Create the pool and perform pool build using the
            #                                                                         VIR_STORAGE_POOL_BUILD_OVERWRITE flag. This is mutually exclusive to
            #                                                                         VIR_STORAGE_POOL_CREATE_WITH_BUILD_NO_OVERWRITE
            #     VIR_STORAGE_POOL_CREATE_WITH_BUILD_OVERWRITE    = 2 (0x2; 1 << 1) : Create the pool and perform pool build using the
            #                                                                         VIR_STORAGE_POOL_BUILD_NO_OVERWRITE flag. This is mutually exclusive to
            #                                                                         VIR_STORAGE_POOL_CREATE_WITH_BUILD_OVERWRITE
            #     VIR_STORAGE_POOL_CREATE_WITH_BUILD_NO_OVERWRITE = 4 (0x4; 1 << 2)
            # }
            #
            # Ref.: https://libvirt.org/html/libvirt-libvirt-storage.html#virStoragePoolCreateFlags
            pool.create(1)
            pool.setAutostart(True)

            pool_state, pool_capacity, pool_allocation, pool_available = pool.info()
            return True, pool_capacity, pool_allocation, pool_available

        # bare 'except' is no issue because we reraise the exception unconditionally below
        except:  # noqa: E722
            try:
                # Destroy (stop) pool if creation failed
                cmd = """
                    virsh
                        --connect '{uri}'
                        pool-destroy
                        '{pool_name}'
                    """.replace('\n', ' ').format(uri=uri, pool_name=pool_name)
                module.run_command(cmd, check_rc=True)

            # bare 'except' is no issue because we reraise the outer exception unconditionally below
            except:  # noqa: E722
                pass

            # Reraise exception from virsh vol-upload command
            raise


def delete(uri,
           pool_name,
           pool_hardware,
           module):

    with libvirt_utils.Connection(uri, module) as conn:
        pools = conn.listAllStoragePools()
        pool = next((pool for pool in pools if pool.name() == pool_name), None)
        if not pool:
            # Pool absent already
            return False, None, None, None

        # pool_state is of type virStoragePoolState:
        #
        # enum virStoragePoolState {
        #     VIR_STORAGE_POOL_INACTIVE     = 0 (0x0) : Not running
        #     VIR_STORAGE_POOL_BUILDING     = 1 (0x1) : Initializing pool, not available
        #     VIR_STORAGE_POOL_RUNNING      = 2 (0x2) : Running normally
        #     VIR_STORAGE_POOL_DEGRADED     = 3 (0x3) : Running degraded
        #     VIR_STORAGE_POOL_INACCESSIBLE = 4 (0x4) : Running, but not accessible
        #     VIR_STORAGE_POOL_STATE_LAST   = 5 (0x5)
        # }
        #
        # Ref.: https://libvirt.org/html/libvirt-libvirt-storage.html#virStoragePoolState
        pool_state, pool_capacity, pool_allocation, pool_available = pool.info()

        # Stop pool
        if pool.isActive():
            pool.destroy()

        # Undefine pool
        pool.undefine()

        return True, pool_capacity, pool_allocation, pool_available


def core(module):
    state = module.params['state']
    uri = module.params['uri']
    pool_name = module.params['name']
    pool_hardware = module.params['hardware']

    if module.check_mode:
        return dict(
            changed=False,
            state=state,
            uri=uri,
            name=pool_name,
            hardware=pool_hardware)

    if state == 'present':
        changed, pool_capacity, pool_allocation, pool_available = create(
            uri,
            pool_name, pool_hardware,
            module)
    elif state == 'absent':
        changed, pool_capacity, pool_allocation, pool_available = delete(
            uri,
            pool_name, pool_hardware,
            module)

    return dict(
        changed=changed,
        state=state,
        uri=uri,
        name=pool_name,
        hardware=pool_hardware,
        capacity=(int(pool_capacity) if pool_capacity is not None else None),
        allocation=(int(pool_allocation) if pool_allocation is not None else None),
        available=(int(pool_available) if pool_available is not None else None)
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            uri=dict(default='qemu:///system'),
            name=dict(required=True, type='str'),
            hardware=dict(type='list')
        ),
        supports_check_mode=True,
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
