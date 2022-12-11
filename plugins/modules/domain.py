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

module: domain

short_description: Create/Delete virtual machines using libvirt.

description:
    - "This module allows one to create virtual machines a.k.a. domains using libvirt.
       It is inspired by Ansible module openstack.cloud.os_server from John Dewey <john@dewey.ws> et al."

requirements:
   - virt-install (e.g. in debian package virt-inst)

options:
    name:
        description:
            - "Name of the domain."
        required: true
        type: str
    hardware:
        default:
            - "[
                { 'cpu': 'host' },
                { 'vcpus': '2' },
                { 'memory': '1024' },
                { 'virt_type': 'kvm' },
                { 'graphics': 'spice,listen=none' }
            ]"
        description:
            - "Hardware of the virtual machine. Accepts all two-dash command line arguments (those with a leading '--')
               of 'virt-install' as a list. Arguments are formatted as key-value pairs without the leading '--' and
               having other dashs replaced by underscores. Arguments without a value (flags), e.g. pxe, must be
               specified with a value of !!null. See manpage of virt-install for available arguments."
        required: false
        type: list
    state:
        choices: [present, absent]
        default: present
        description:
            - "Should the domain be present or absent."
        type: str

notes:
  - "No modifications are applied to existing domains; module is skipped if domain exists already."

extends_documentation_fragment:
  - jm1.libvirt.libvirt

author: "Jakob Meng (@jm1)"
'''

EXAMPLES = r'''
- jm1.libvirt.domain:
    name: 'inf.h-brs.de'
'''

RETURN = r'''
'''

# NOTE: Synchronize imports with DOCUMENTATION string above and chapter Requirements in roles/server/README.md
from ansible_collections.jm1.libvirt.plugins.module_utils import libvirt as libvirt_utils
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
import traceback


def create(uri,
           domain_name,
           hardware,
           module):
    with libvirt_utils.Connection(uri, module) as conn:
        domains = conn.listAllDomains()
        domain = next((domain for domain in domains if domain.name() == domain_name), None)
        if domain:
            # domain exists already
            return False

        # Prepare virt-install options
        virt_install_args = libvirt_utils.to_cli_args(hardware)

        # Do not boot domain, just define it
        virt_install_args.extend(['--import', '--noreboot', '--noautoconsole'])

        # Define domain
        cmd = """
            virt-install
                --connect '{uri}'
                --name '{domain_name}'
                {virt_install_args}
            """.replace('\n', ' ').format(uri=uri,
                                          domain_name=domain_name,
                                          virt_install_args=' '.join(virt_install_args))

        module.run_command(cmd, check_rc=True)

        return True


def delete(uri,
           domain_name,
           hardware,
           module):
    with libvirt_utils.Connection(uri, module) as conn:
        domains = conn.listAllDomains()
        domain = next((domain for domain in domains if domain.name() == domain_name), None)
        if not domain:
            # domain absent already
            return False

        # domain_state is of type virDomainState:
        #
        # enum virDomainState {
        #     VIR_DOMAIN_NOSTATE     = 0 (0x0) : no state
        #     VIR_DOMAIN_RUNNING     = 1 (0x1) : the domain is running
        #     VIR_DOMAIN_BLOCKED     = 2 (0x2) : the domain is blocked on resource
        #     VIR_DOMAIN_PAUSED      = 3 (0x3) : the domain is paused by user
        #     VIR_DOMAIN_SHUTDOWN    = 4 (0x4) : the domain is being shut down
        #     VIR_DOMAIN_SHUTOFF     = 5 (0x5) : the domain is shut off
        #     VIR_DOMAIN_CRASHED     = 6 (0x6) : the domain is crashed
        #     VIR_DOMAIN_PMSUSPENDED = 7 (0x7) : the domain is suspended by guest power management
        #     VIR_DOMAIN_LAST        = 8 (0x8) : NB: this enum value will increase over time as new events are added
        #                                            to the libvirt API. It reflects the last state supported by
        #                                            this version of the libvirt API.
        # }
        #
        # Ref.: https://libvirt.org/html/libvirt-libvirt-domain.html#virDomainState

        domain_state, domain_maxMem, domain_memory, domain_nrVirtCpu, domain_cpuTime = domain.info()
        if domain_state > 7:
            raise Exception('Unknown domain state %s' % domain_state)

        if (0 < domain_state and domain_state < 5):
            domain.destroy()

        domain.undefine()
        return True


def core(module):
    state = module.params['state']
    uri = module.params['uri']
    domain_name = module.params['name']
    hardware = module.params['hardware']

    if module.check_mode:
        return dict(
            changed=False,
            state=state,
            uri=uri,
            name=domain_name,
            hardware=hardware)

    if state == 'present':
        changed = create(
            uri,
            domain_name,
            hardware,
            module)
    elif state == 'absent':
        changed = delete(
            uri,
            domain_name,
            hardware,
            module)

    return dict(
        changed=changed,
        state=state,
        uri=uri,
        name=domain_name,
        hardware=hardware)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            uri=dict(default='qemu:///system'),
            name=dict(required=True, type='str'),
            hardware=dict(
                type='list',
                default=[
                    {'cpu': 'host'},
                    {'vcpus': '2'},
                    {'memory': '1024'},
                    {'virt-type': 'kvm'},
                    {'graphics': 'spice,listen=none'}
                ])
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
