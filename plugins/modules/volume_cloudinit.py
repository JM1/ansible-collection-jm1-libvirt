#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:set fileformat=unix shiftwidth=4 softtabstop=4 expandtab:
# kate: end-of-line unix; space-indent on; indent-width 4; remove-trailing-space on;

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

module: volume_cloudinit

short_description: Create cloud-init config drives as new volumes in libvirt storage pools.

description:
    - "This module allows one to create cloud-init config drives with Meta-Data, User-Data and Network Configuration as
       new volumes in libvirt storage pools. It is inspired by Ansible module openstack.cloud.os_volume."

requirements:
   - cloud-localds (e.g. in debian package cloud-image-utils)
   - virsh (e.g. in debian package libvirt-clients)

options:
    pool:
        description:
            - "Name or UUID of the storage pool to create the config drive volume in."
        required: true
        type: str
    name:
        description:
            - "Name of the config drive volume."
        required: true
        type: str
    format:
        default: raw
        description:
            - "Disk format (see manpage of qemu-image for allowed disk formats), defaulting to raw."
        required: false
        type: str
    filesystem:
        default: iso
        description:
            - "Filesystem format (vfat or iso), defaulting to iso9660."
        required: false
        type: str
    metadata:
        description:
            - "cloud-init Meta-Data."
        required: false
        type: str
    userdata:
        description:
            - "cloud-init User-Data. Required if C(state) is C(present)."
        type: str
    networkconfig:
        description:
            - "cloud-init Network Configuration."
        required: false
        type: str
    state:
        choices: [present, absent]
        default: present
        description:
            - "Should the config drive be present or absent."
        type: str

notes:
  - "No modifications are applied to existing config drive volumes; module is skipped if volume exists already."

extends_documentation_fragment:
  - jm1.libvirt.libvirt

author: "Jakob Meng (@jm1)"
'''

EXAMPLES = r'''
- jm1.libvirt.volume_cloudinit
    pool: 'default'
    name: 'cloud-init_config-drive.qcow2'
    userdata: |
        #cloud-config

        # user-data configuration file for cloud-init
        # Ref.: https://cloudinit.readthedocs.io/

        hostname: inf.h-brs.de
'''

RETURN = r'''
'''

# NOTE: Synchronize imports with DOCUMENTATION string above and chapter Requirements in roles/server/README.md
from ansible_collections.jm1.libvirt.plugins.module_utils import libvirt as libvirt_utils
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
import ansible.module_utils.six as six
import os
import traceback

if six.PY2:
    try:
        from backports import tempfile
    except ImportError:
        BACKPORTS_TEMPFILE_IMPORT_ERROR = traceback.format_exc()
        HAS_BACKPORTS_TEMPFILE = False
    else:
        BACKPORTS_TEMPFILE_IMPORT_ERROR = None
        HAS_BACKPORTS_TEMPFILE = True
elif six.PY3:
    import tempfile


def cloud_localds(volume_format,
                  volume_filesystem,
                  ci_metadata_path,
                  ci_userdata_path,
                  ci_networkconfig_path,
                  configdrive_path,
                  module):
    # TODO: Reimplement cloud-localds in Python and drop dependency on cloud-localds,
    #       because it is not available on Red Hat Enterprise Linux 8 and CentOS 8.
    #       Ref.: https://salsa.debian.org/cloud-team/cloud-utils/-/blob/master/bin/cloud-localds

    cmd = 'cloud-localds'
    if volume_format:
        cmd += ' --disk-format "%s"' % volume_format

    if volume_filesystem:
        cmd += ' --filesystem "%s"' % volume_filesystem

    if ci_networkconfig_path:
        cmd += ' --network-config "%s"' % ci_networkconfig_path

    cmd += ' %s' % configdrive_path
    cmd += ' %s' % ci_userdata_path

    if ci_metadata_path:
        cmd += ' %s' % ci_metadata_path

    module.run_command(cmd, check_rc=True)


def create(uri,
           pool_name,
           volume_name,
           volume_format,
           volume_filesystem,
           ci_metadata,
           ci_userdata,
           ci_networkconfig,
           module):

    with libvirt_utils.Connection(uri, module) as conn:
        pool = conn.storagePoolLookupByName(pool_name)

        if volume_name in pool.listVolumes():
            # volume exists already
            return False

        with tempfile.TemporaryDirectory() as dir:
            ci_metadata_path = os.path.join(dir, 'meta-data')
            ci_userdata_path = os.path.join(dir, 'user-data')
            ci_networkconfig_path = os.path.join(dir, 'network-config')

            if ci_metadata:
                with open(ci_metadata_path, 'w') as f:
                    f.write(ci_metadata)
            if ci_userdata:
                with open(ci_userdata_path, 'w') as f:
                    f.write(ci_userdata)
            if ci_networkconfig:
                with open(ci_networkconfig_path, 'w') as f:
                    f.write(ci_networkconfig)

            # Create cloud-init config drive image
            configdrive_path = os.path.join(dir, 'cloud-init_config-drive.img')

            cloud_localds(
                volume_format,
                volume_filesystem,
                ci_metadata_path if ci_metadata else None,
                ci_userdata_path,
                ci_networkconfig_path if ci_networkconfig else None,
                configdrive_path,
                module)

            configdrive_size = os.path.getsize(configdrive_path)

            # Create cloud-init config volume

            cmd = """
                virsh
                    --connect '{uri}'
                    vol-create-as
                    '{pool_name}'
                    '{volume_name}'
                    '{configdrive_size}'
                    --format '{volume_format}'
                """.replace('\n', ' ').format(
                    uri=uri,
                    pool_name=pool_name,
                    volume_name=volume_name,
                    configdrive_size=configdrive_size,
                    volume_format=volume_format)

            module.run_command(cmd, check_rc=True)

            # Upload cloud-init config drive to libvirt storage volume
            cmd = """
                virsh
                    --connect '{uri}'
                    vol-upload
                    --pool '{pool_name}'
                    '{volume_name}'
                    '{configdrive_path}'
                """.replace('\n', ' ').format(
                    uri=uri,
                    pool_name=pool_name,
                    volume_name=volume_name,
                    configdrive_path=configdrive_path)

            module.run_command(cmd, check_rc=True)

        return True


def delete(uri,
           pool_name,
           volume_name,
           volume_format,
           volume_filesystem,
           ci_metadata,
           ci_userdata,
           ci_networkconfig,
           module):

    with libvirt_utils.Connection(uri, module) as conn:
        pools = conn.listAllStoragePools()
        pool = next((pool for pool in pools if pool.name() == pool_name), None)
        if not pool:
            # pool absent already and hence volume as well
            return False

        if volume_name not in pool.listVolumes():
            # volume absent already
            return False

        volume = pool.storageVolLookupByName(volume_name)
        volume.delete()
        return True


def core(module):
    state = module.params['state']
    uri = module.params['uri']
    pool_name = module.params['pool']
    volume_name = module.params['name']
    volume_format = module.params['format']
    volume_filesystem = module.params['filesystem']
    ci_metadata = module.params['metadata']
    ci_userdata = module.params['userdata']
    ci_networkconfig = module.params['networkconfig']

    if module.check_mode:
        return dict(
            changed=False,
            state=state,
            uri=uri,
            pool=pool_name,
            name=volume_name,
            format=volume_format,
            filesystem=volume_filesystem,
            metadata=ci_metadata,
            userdata=ci_userdata,
            networkconfig=ci_networkconfig)

    if state == 'present':
        changed = create(
            uri,
            pool_name,
            volume_name, volume_format, volume_filesystem,
            ci_metadata, ci_userdata, ci_networkconfig,
            module)
    elif state == 'absent':
        changed = delete(
            uri,
            pool_name,
            volume_name, volume_format, volume_filesystem,
            ci_metadata, ci_userdata, ci_networkconfig,
            module)

    return dict(
        changed=changed,
        state=state,
        uri=uri,
        pool=pool_name,
        name=volume_name,
        format=volume_format,
        filesystem=volume_filesystem,
        metadata=ci_metadata,
        userdata=ci_userdata,
        networkconfig=ci_networkconfig)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            uri=dict(default='qemu:///system'),
            pool=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            format=dict(type='str', default='raw'),
            filesystem=dict(type='str', choices=['vfat', 'iso'], default='iso'),
            metadata=dict(type='str'),
            userdata=dict(type='str'),
            networkconfig=dict(type='str')
        ),
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['userdata']]
        ]
    )

    libvirt_utils.try_import(module)

    if six.PY2 and not HAS_BACKPORTS_TEMPFILE:
        module.fail_json(msg=missing_required_lib("backports.tempfile"), exception=BACKPORTS_TEMPFILE_IMPORT_ERROR)

    try:
        result = core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
