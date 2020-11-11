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

module: pool_xml

short_description: Create/Modify/Delete a libvirt storage pool.

description:
    - "This module allows one to create, modify and delete a libvirt storage pool."
    - "For use in addition to M(community.libvirt.virt_pool)."
    - "Compared to M(community.libvirt.virt_pool), this module applies changes to a pool whenever necessary while the
       former has to be called with 'C(command): I(define)' explicitly to apply any changes."

requirements: []

options:
    ignore:
        default:
            - /pool/uuid
        description:
            - "XPath expressions to XML nodes that are ignored when comparing I(xml) to existing pool configuration."
            - "XPath expressions must return XML nodes only, e.g. '/pool/uuid'. Other XPath expressions, such as
               '/pool/uuid/text()' are not supported."
            - "When modifying a pool, ignored XML nodes will be taken from existing pool, i.e. they will not be
               overwritten."
        type: list
    state:
        choices: [present, absent]
        default: present
        description:
            - "Should the pool be present or absent."
            - "If pool does not exist and I(state) is C(present), then the pool will be defined, but not started.
               Use M(community.libvirt.virt_pool) to start the pool."
            - "If pool does exist and I(state) is C(absent), then the pool will not be stopped prior to undefine.
               Use M(community.libvirt.virt_pool) to stop the pool."
        type: str
    xml:
        description:
            - "XML document used to define or modify the pool."
            - "Must be raw XML content using C(lookup). XML cannot be reference to a file."
        required: true
        type: str

notes:
  - "For changes to take effect, a modified pool has to be restarted. To do so, e.g. call M(community.libvirt.virt_pool)
     with 'C(command): I(stop)' and 'C(command): I(start)'."

extends_documentation_fragment:
  - jm1.libvirt.libvirt

author: "Jakob Meng (@jm1)"
'''

EXAMPLES = r'''
- name: Create or modify a storage pool
  jm1.libvirt.pool_xml:
    ignore:
    - '/pool/uuid'
    - '/pool/capacity'
    - '/pool/allocation'
    - '/pool/available'
    state: present
    xml: |
      <pool type='dir'>
        <name>default</name>
        <target>
          <path>/var/lib/libvirt/images</path>
          <permissions>
            <mode>0711</mode>
            <owner>0</owner>
            <group>0</group>
          </permissions>
        </target>
      </pool>
'''

RETURN = r'''
xml:
    description: Full XML dump of libvirt's storage pool config, including ignored XML element tags
    returned: changed or success
    type: str
    sample: |
      <pool type='dir'>
        <name>default</name>
        <uuid>363b4985-8284-49ca-8e71-59cfee876a1a</uuid>
        <capacity unit='bytes'>990801235968</capacity>
        <allocation unit='bytes'>846638727168</allocation>
        <available unit='bytes'>144162508800</available>
        <source>
        </source>
        <target>
          <path>/var/lib/libvirt/images</path>
          <permissions>
            <mode>0711</mode>
            <owner>0</owner>
            <group>0</group>
          </permissions>
        </target>
      </pool>
'''

# NOTE: Synchronize imports with DOCUMENTATION string above and chapter Requirements in roles/server/README.md
from ansible_collections.jm1.libvirt.plugins.module_utils import libvirt as libvirt_utils
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
import traceback

try:
    import libvirt
except ImportError:
    # error handled in libvirt_utils.try_import() below
    pass

try:
    from lxml import etree
except ImportError:
    # error handled in libvirt_utils.try_import() below
    pass


def lookup_uuid(xml):
    uuids = xml.xpath('/pool/uuid')
    if len(uuids) > 1:
        raise ValueError("storage pool config is invalid: xml has more than one 'uuid' element")

    if uuids:
        return uuids[0].text

    return None


def lookup_name(xml):
    names = xml.xpath('/pool/name')
    if len(names) > 1:
        raise ValueError("storage pool config is invalid: xml has more than one 'name' element")

    if names:
        return names[0].text

    return None


def lookup_uuid_and_name(xml):
    uuid = lookup_uuid(xml)
    name = lookup_name(xml)

    if not uuid and not name:
        raise ValueError("storage pool config is invalid: xml requires an 'uuid', an 'name' element or both")

    return uuid, name


def lookup_storage_pool(conn, uuid, name):
    try:
        if uuid:
            return conn.storagePoolLookupByUUIDString(uuid)
        elif name:
            return conn.storagePoolLookupByName(name)
    except libvirt.libvirtError as e:
        if e.get_error_code() != libvirt.VIR_ERR_NO_STORAGE_POOL:
            raise
    return None


def create_or_modify(ignore_xpaths, uri, xml, module):
    xml_root = etree.fromstring(xml)
    uuid, name = lookup_uuid_and_name(xml_root)

    with libvirt_utils.Connection(uri, module) as conn:
        pool = lookup_storage_pool(conn, uuid, name)

        if not pool:
            # create
            pool = conn.storagePoolDefineXML(xml)
            return True, pool.XMLDesc(flags=libvirt.VIR_STORAGE_XML_INACTIVE)
        else:
            # maybe modify
            old_xml = pool.XMLDesc(flags=libvirt.VIR_STORAGE_XML_INACTIVE)

            if libvirt_utils.xml_strings_equal(old_xml, xml, ignore_xpaths):
                # pool does not require update
                return False, old_xml

            xml = libvirt_utils.update_xml_desc(old_xml, xml, ignore_xpaths)
            pool = conn.storagePoolDefineXML(xml)
            return True, pool.XMLDesc(flags=libvirt.VIR_STORAGE_XML_INACTIVE)


def delete(ignore_xpaths, uri, xml, module):
    xml_root = etree.fromstring(xml)
    uuid, name = lookup_uuid_and_name(xml_root)

    with libvirt_utils.Connection(uri, module) as conn:
        pool = lookup_storage_pool(conn, uuid, name)

        if not pool:
            # pool absent already
            return False, None

        xml = pool.XMLDesc(flags=libvirt.VIR_STORAGE_XML_INACTIVE)  # fetch xml before deletion
        pool.undefine()
        return True, xml


def core(module):
    ignore = module.params['ignore']
    state = module.params['state']
    uri = module.params['uri']
    xml = module.params['xml']

    if module.check_mode:
        return dict(
            changed=False,
            ignore=ignore,
            state=state,
            uri=uri,
            xml=xml)

    if state == 'present':
        changed, xml = create_or_modify(ignore, uri, xml, module)
    elif state == 'absent':
        changed, xml = delete(ignore, uri, xml, module)

    return dict(
        changed=changed,
        ignore=ignore,
        state=state,
        uri=uri,
        xml=xml)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ignore=dict(type='list', default=['/pool/uuid']),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            uri=dict(default='qemu:///system'),
            xml=dict(required=True, type='str')
        ),
        supports_check_mode=True
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
