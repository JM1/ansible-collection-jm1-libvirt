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

module: volume_import

short_description: Import volumes into libvirt storage pools.

description:
    - "This module allows one to import volumes into libvirt storage pools.
       It is based on Ansible module community.libvirt.virt_pool from Maciej Delmanowski <drybjed@gmail.com>."

requirements:
   - lxml
   - backports.tempfile (python 2 only)
   - virsh (e.g. in debian package libvirt-clients)

options:
    pool:
        description:
            - "Name or UUID of the storage pool to create the volume in."
        required: true
        type: str
    name:
        description:
            - "Name of the new volume, defaulting to image name."
        required: false
        type: str
    image:
        description:
            - "Image file path (relative or absolute) or URL. Required if C(state) is C(present)."
        type: str
    checksum:
        description:
            - "Optional image checksum."
        required: false
        type: str
    format:
        description:
            - "Image file format, e.g. raw or qcow2, defaulting to image extension."
        type: str
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
- jm1.libvirt.volume_import
    pool: 'default'
    name: 'debian-10.3.1-20200328-openstack-amd64.qcow2'
    image: 'https://cdimage.debian.org/cdimage/openstack/current/debian-10.3.1-20200328-openstack-amd64.qcow2'
    image_checksum: sha256:c97f8680284734535bdf988b8574e494eeda82fd6ab0720cd02aa5ee0b681263
    image_format: 'qcow2'
'''

RETURN = r'''
name:
    description: Name of the volume
    returned: changed or success
    type: str
    sample: 'debian-10.4.0-openstack-amd64.qcow2'

capacity:
    description: Capacity of the volume
    returned: changed or success
    type: int
    sample: 536392192

format:
    description: Format of the volume (and the image)
    returned: changed or success
    type: str
    sample: 'qcow2'
'''

# NOTE: Synchronize imports with DOCUMENTATION string above and chapter Requirements in roles/server/README.md
from ansible_collections.jm1.libvirt.plugins.module_utils import libvirt as libvirt_utils
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six.moves.urllib.parse import urlsplit
from ansible.module_utils.urls import open_url
import ansible.module_utils.six as six
import os
import re
import shutil
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


def import_from_disk(uri,
                     pool_name,
                     volume_name,
                     image_path,
                     image_format,
                     image_checksum,
                     image_checksum_algorithm,
                     module):
    # Create libvirt storage volume and upload image to volume

    if not os.path.exists(image_path):
        raise Exception('Image path %s does not exist' % image_path)

    if image_checksum:
        # Verify image checksum
        checksum_on_disk = module.digest_from_file(image_path, image_checksum_algorithm)
        if image_checksum != checksum_on_disk:
            raise Exception('Checksum mismatch %s != %s' % (image_checksum, checksum_on_disk))

    with libvirt_utils.Connection(uri, module) as conn:
        pool = conn.storagePoolLookupByName(pool_name)
        if volume_name in pool.listVolumes():
            # Fail if volume exists already
            raise Exception('volume %s exists already in pool %s' % (volume_name, pool_name))

    image_size = os.path.getsize(image_path)

    cmd = """
        virsh
            --connect '{uri}'
            vol-create-as
            '{pool_name}'
            '{volume_name}'
            '{image_size}'
            --format '{image_format}'
        """.replace('\n', ' ').format(
            uri=uri,
            pool_name=pool_name,
            volume_name=volume_name,
            image_size=image_size,
            image_format=image_format)

    module.run_command(cmd, check_rc=True)

    try:
        cmd = """
            virsh
                --connect '{uri}'
                vol-upload
                --pool '{pool_name}'
                '{volume_name}'
                '{image_path}'
            """.replace('\n', ' ').format(
                uri=uri,
                pool_name=pool_name,
                volume_name=volume_name,
                image_path=image_path)

        module.run_command(cmd, check_rc=True)

    # bare 'except' is no issue because we reraise the exception unconditionally below
    except:  # noqa: E722

        try:
            # Remove volume if upload failed
            cmd = """
                virsh
                    --connect '{uri}'
                    vol-delete
                    '{volume_name}'
                    --pool '{pool_name}'
                """.replace('\n', ' ').format(
                    uri=uri,
                    pool_name=pool_name,
                    volume_name=volume_name)

            module.run_command(cmd, check_rc=True)

        # bare 'except' is no issue because we reraise the outer exception unconditionally below
        except:  # noqa: E722
            pass

        # Reraise exception from virsh vol-upload command
        raise

    with libvirt_utils.Connection(uri, module) as conn:
        pool = conn.storagePoolLookupByName(pool_name)
        volume = pool.storageVolLookupByName(volume_name)
        volume_type, volume_capacity, volume_allocation = volume.info()
        return volume_capacity


def import_(uri,
            pool_name,
            volume_name,
            image_path,
            image_format,
            image_checksum,
            image_checksum_algorithm,
            module):

    with libvirt_utils.Connection(uri, module) as conn:
        pool = conn.storagePoolLookupByName(pool_name)
        image_path_scheme = urlsplit(image_path).scheme
        image_path_is_uri = image_path_scheme != 'file' and len(image_path_scheme) > 0

        if image_path_is_uri:
            # Download image, create libvirt storage volume and upload image to volume
            with tempfile.TemporaryDirectory() as dir:
                with open_url(image_path) as r:
                    filename = None

                    cd = r.getheader('Content-Disposition')
                    if cd:
                        try:
                            filename = re.findall("filename=(.+)", cd)[0]
                        except IndexError:
                            filename = None

                    if not filename:
                        filename = os.path.basename(urlsplit(image_path).path)

                    if not filename:
                        filename = volume_name

                    if not volume_name:
                        volume_name = filename

                    if not filename:  # or not volume_name
                        raise ValueError('no volume name given and volume name could not be derived from image')

                    if not image_format:
                        image_format = os.path.splitext(volume_name)[1]

                    if not image_format:
                        raise ValueError('no image format given and format could not be derived from image')

                    if volume_name in pool.listVolumes():
                        # volume exists already
                        volume = pool.storageVolLookupByName(volume_name)
                        volume_type, volume_capacity, volume_allocation = volume.info()
                        volume_format = libvirt_utils.lookup_attribute(volume, '/volume/target/format', 'type')
                        return False, volume_name, volume_capacity, volume_format

                    # Download image
                    local_image_path = os.path.join(dir, filename)
                    with open(local_image_path, 'wb') as f:
                        shutil.copyfileobj(r, f)

                image_size = import_from_disk(
                    uri,
                    pool_name,
                    volume_name,
                    local_image_path, image_format, image_checksum, image_checksum_algorithm,
                    module)

                return True, volume_name, image_size, image_format

        else:  # not image_path_is_uri
            if not volume_name:
                volume_name = os.path.basename(image_path)

            if not volume_name:
                raise ValueError('no volume name given and volume name could not be derived from image path')

            if not image_format:
                image_format = os.path.splitext(volume_name)[1]

            if not image_format:
                raise ValueError('no image format given and format could not be derived from image')

            if volume_name in pool.listVolumes():
                # volume exists already
                volume = pool.storageVolLookupByName(volume_name)
                volume_type, volume_capacity, volume_allocation = volume.info()
                volume_format = libvirt_utils.lookup_attribute(volume, '/volume/target/format', 'type')
                return False, volume_name, volume_capacity, volume_format

            volume_capacity = import_from_disk(
                uri,
                pool_name,
                volume_name,
                image_path, image_format, image_checksum, image_checksum_algorithm,
                module)

            return True, volume_name, volume_capacity, image_format


def delete(uri,
           pool_name,
           volume_name,
           image_path,
           image_format,
           image_checksum,
           image_checksum_algorithm,
           module):

    with libvirt_utils.Connection(uri, module) as conn:
        pools = conn.listAllStoragePools()
        pool = next((pool for pool in pools if pool.name() == pool_name), None)
        if not pool:
            # pool absent already and hence volume as well
            return False, volume_name, None, None

        image_path_scheme = urlsplit(image_path).scheme
        image_path_is_uri = image_path_scheme != 'file' and len(image_path_scheme) > 0

        if image_path_is_uri and not volume_name:
            raise ValueError('name is required for deleting volumes if image is given as an uri')

        if not volume_name:
            volume_name = os.path.basename(image_path)

        if not volume_name:
            raise ValueError('name is required for deleting volumes')

        if volume_name not in pool.listVolumes():
            # volume absent already
            return False, volume_name, None, None

        volume = pool.storageVolLookupByName(volume_name)
        # volume_type is of type virStorageVolType:
        #
        # enum virStorageVolType {
        #     VIR_STORAGE_VOL_FILE    = 0 (0x0) : Regular file based volumes
        #     VIR_STORAGE_VOL_BLOCK   = 1 (0x1) : Block based volumes
        #     VIR_STORAGE_VOL_DIR     = 2 (0x2) : Directory-passthrough based volume
        #     VIR_STORAGE_VOL_NETWORK = 3 (0x3) : Network volumes like RBD (RADOS Block Device)
        #     VIR_STORAGE_VOL_NETDIR  = 4 (0x4) : Network accessible directory that can contain other network volumes
        #     VIR_STORAGE_VOL_PLOOP   = 5 (0x5) : Ploop based volumes
        #     VIR_STORAGE_VOL_LAST    = 6 (0x6)
        # }
        #
        # Ref.: https://libvirt.org/html/libvirt-libvirt-storage.html#virStorageVolType
        volume_type, volume_capacity, volume_allocation = volume.info()
        volume_format = libvirt_utils.lookup_attribute(volume, '/volume/target/format', 'type')
        volume.delete()
        return True, volume_name, volume_capacity, volume_format


def core(module):
    state = module.params['state']
    uri = module.params['uri']
    pool_name = module.params['pool']
    volume_name = module.params['name']
    image_path = module.params['image']
    image_format = module.params['format']
    image_checksum = module.params['checksum']

    if image_checksum:
        try:
            algorithm, checksum = image_checksum.split(':', 1)
        except ValueError:
            module.fail_json(msg="The checksum parameter has to be in format <algorithm>:<checksum>")
    else:
        algorithm = None
        checksum = None

    if module.check_mode:
        return dict(
            changed=False,
            state=state,
            uri=uri,
            pool=pool_name,
            name=volume_name,
            image=image_path,
            format=image_format,
            checksum=image_checksum)

    if state == 'present':
        changed, volume_name, volume_capacity, volume_format = import_(
            uri,
            pool_name,
            volume_name,
            image_path, image_format, checksum, algorithm,
            module)
    elif state == 'absent':
        changed, volume_name, volume_capacity, volume_format = delete(
            uri,
            pool_name,
            volume_name,
            image_path, image_format, checksum, algorithm,
            module)

    return dict(
        changed=changed,
        state=state,
        uri=uri,
        pool=pool_name,
        name=volume_name,
        image=image_path,
        format=volume_format,
        checksum=image_checksum,
        capacity=(int(volume_capacity) if volume_capacity is not None else None)
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            uri=dict(default='qemu:///system'),
            pool=dict(required=True, type='str'),
            name=dict(type='str'),
            image=dict(type='str'),
            format=dict(type='str'),
            checksum=dict(type='str'),
        ),
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['image']]
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
