#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:set fileformat=unix shiftwidth=4 softtabstop=4 expandtab:
# kate: end-of-line unix; space-indent on; indent-width 4; remove-trailing-space on;

# Copyright: (c) 2020, Jakob Meng <jakobmeng@web.de>
# Based on community.libvirt.virt_pool module written by Maciej Delmanowski <drybjed@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard libvirt documentation fragment
    DOCUMENTATION = r'''
options:
    uri:
        default: qemu:///system
        description:
            - "libvirt connection uri."
        required: false
        type: str

requirements:
    - libvirt (e.g. in debian package python3-libvirt)
    - lxml (e.g. in debian package python3-lxml)
'''
