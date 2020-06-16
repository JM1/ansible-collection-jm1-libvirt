#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:set fileformat=unix shiftwidth=4 softtabstop=4 expandtab:
# kate: end-of-line unix; space-indent on; indent-width 4; remove-trailing-space on;

# Copyright: (c) 2020, Jakob Meng <jakobmeng@web.de>
# Based on community.libvirt.virt_pool module written by Maciej Delmanowski <drybjed@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.six import iteritems
import traceback

try:
    import libvirt
except ImportError:
    # Error handled in the calling module.
    LIBVIRT_IMPORT_ERROR = traceback.format_exc()
    HAS_LIBVIRT = False
else:
    LIBVIRT_IMPORT_ERROR = None
    HAS_LIBVIRT = True

try:
    from lxml import etree
except ImportError:
    # Error handled in the calling module.
    LXML_IMPORT_ERROR = traceback.format_exc()
    HAS_LXML = False
else:
    LXML_IMPORT_ERROR = None
    HAS_LXML = True


def try_import(module):
    if not HAS_LIBVIRT:
        module.fail_json(msg=missing_required_lib("libvirt"), exception=LIBVIRT_IMPORT_ERROR)

    if not HAS_LXML:
        module.fail_json(msg=missing_required_lib("lxml"), exception=LXML_IMPORT_ERROR)


if HAS_LIBVIRT and HAS_LXML:

    class Connection(object):

        def __init__(self, uri, module):
            self.uri = uri
            self.module = module

        def __enter__(self):
            conn = libvirt.open(self.uri)
            if not conn:
                raise Exception("hypervisor connection failure")
            self.conn = conn
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.conn.close()

        # provide access to methods and variables of virConnect object
        def __getattr__(self, name):
            return getattr(self.conn, name)

    def lookup_attribute(entry, xpath, attribute):
        xml = etree.fromstring(entry.XMLDesc(0))
        try:
            value = xml.xpath(xpath)[0].get(attribute)
        except Exception:
            raise ValueError('attribute %s not found with xpath %s in %s' % (attribute, xpath, entry.XMLDesc(0)))
        return value

    def to_cli_args(list_):
        cli_args = []
        if list_:
            for v in list_:
                if isinstance(v, dict):
                    for key, value in iteritems(v):
                        if value:
                            cli_args.extend(['--%s' % key.replace('_', '-'), value])
                        else:
                            cli_args.extend(['--%s' % key.replace('_', '-')])
                elif isinstance(v, list):
                    cli_args.extend(v)
                else:
                    cli_args.append(v)
        return cli_args
