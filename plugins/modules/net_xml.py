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

module: net_xml

short_description: Create/Modify/Delete a libvirt virtual network.

description:
    - "This module allows one to create, modify and delete a libvirt virtual network."
    - "For use in addition to M(community.libvirt.virt_net)."
    - "Compared to M(community.libvirt.virt_net), this module applies changes to a network whenever necessary while the
       former has to be called with 'C(command): I(modify)' explicitly to apply any changes."

requirements: []

options:
    ignore:
        default:
            - /network/mac
            - /network/uuid
        description:
            - "XPath expressions to XML nodes that are ignored when comparing I(xml) to existing network configuration."
            - "XPath expressions must return XML nodes only, e.g. '/network/uuid'. Other XPath expressions, such as
               '/network/uuid/text()' are not supported."
            - "When modifying a network, ignored XML nodes will be taken from existing network, i.e. they will not be
               overwritten."
        type: list
    state:
        choices: [present, absent]
        default: present
        description:
            - "Should the network be present or absent."
            - "If network does not exist and I(state) is C(present), then the network will be defined, but not started.
               Use M(community.libvirt.virt_net) to start the network."
            - "If network does exist and I(state) is C(absent), then the network will not be stopped prior to undefine.
               Use M(community.libvirt.virt_net) to stop the network."
        type: str
    xml:
        description:
            - "XML document used to define or modify the network."
            - "Must be raw XML content using C(lookup). XML cannot be reference to a file."
        required: true
        type: str

notes: []

extends_documentation_fragment:
  - jm1.libvirt.libvirt

author: "Jakob Meng (@jm1)"
'''

EXAMPLES = r'''
- name: Create or modify a network
  jm1.libvirt.net_xml:
    state: present
    xml: |
      <network>
        <name>nat-0</name>
        <forward mode='nat'/>
        <bridge name='virbr-nat-0' stp='on' delay='0'/>
        <mac address='52:54:00:50:00:10'/>
        <ip address='192.168.122.1' netmask='255.255.255.0'>
          <dhcp>
            <range start='192.168.122.2' end='192.168.122.254'/>
          </dhcp>
        </ip>
      </network>
'''

RETURN = r'''
xml:
    description: Full XML dump of libvirt's network config, including ignored XML element tags
    returned: changed or success
    type: str
    sample: |
      <network>
        <name>nat-0</name>
        <uuid>363b4985-8284-49ca-8e71-59cfee876a1a</uuid>
        <forward mode='nat'/>
        <bridge name='virbr-nat-0' stp='on' delay='0'/>
        <mac address='52:54:00:50:00:10'/>
        <ip address='192.168.122.1' netmask='255.255.255.0'>
          <dhcp>
            <range start='192.168.122.2' end='192.168.122.254'/>
          </dhcp>
        </ip>
      </network>
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
    uuids = xml.xpath('/network/uuid')
    if len(uuids) > 1:
        raise ValueError("network config is invalid: xml has more than one 'uuid' element")

    if uuids:
        return uuids[0].text

    return None


def lookup_name(xml):
    names = xml.xpath('/network/name')
    if len(names) > 1:
        raise ValueError("network config is invalid: xml has more than one 'name' element")

    if names:
        return names[0].text

    return None


def lookup_uuid_and_name(xml):
    uuid = lookup_uuid(xml)
    name = lookup_name(xml)

    if not uuid and not name:
        raise ValueError("network config is invalid: xml requires an 'uuid', an 'name' element or both")

    return uuid, name


def lookup_network(conn, uuid, name):
    try:
        if uuid:
            return conn.networkLookupByUUIDString(uuid)
        elif name:
            return conn.networkLookupByName(name)
    except libvirt.libvirtError as e:
        if e.get_error_code() != libvirt.VIR_ERR_NO_NETWORK:
            raise
    return None


def create_or_modify(ignore_xpaths, uri, xml, module):
    xml_root = etree.fromstring(xml)
    uuid, name = lookup_uuid_and_name(xml_root)

    with libvirt_utils.Connection(uri, module) as conn:
        network = lookup_network(conn, uuid, name)

        if not network:
            # create
            network = conn.networkDefineXML(xml)
            return True, network.XMLDesc(0)
        else:
            # maybe modify
            old_xml = network.XMLDesc(0)

            if libvirt_utils.xml_strings_equal(old_xml, xml, ignore_xpaths):
                # network does not require update
                return False, old_xml

            xml = libvirt_utils.update_xml_desc(old_xml, xml, ignore_xpaths)
            network = conn.networkDefineXML(xml)
            return True, network.XMLDesc(0)


def delete(ignore_xpaths, uri, xml, module):
    xml_root = etree.fromstring(xml)
    uuid, name = lookup_uuid_and_name(xml_root)

    with libvirt_utils.Connection(uri, module) as conn:
        network = lookup_network(conn, uuid, name)

        if not network:
            # network absent already
            return False, None

        xml = network.XMLDesc(0)  # fetch xml before deletion
        network.undefine()
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
            ignore=dict(type='list', default=['/network/mac', '/network/uuid']),
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
