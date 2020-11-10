#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim:set fileformat=unix shiftwidth=4 softtabstop=4 expandtab:
# kate: end-of-line unix; space-indent on; indent-width 4; remove-trailing-spaces modified;

# Copyright: (c) 2020, Jakob Meng <jakobmeng@web.de>
# Based on community.libvirt.virt_pool module written by Maciej Delmanowski <drybjed@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.six import iteritems
import copy
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

    def xml_elements_equal(e1, e2):
        """ Test equivalence of (l)xml.etree.ElementTree
            Ref.: https://stackoverflow.com/a/24349916/6490710
        """
        if e1.tag != e2.tag:
            return False
        if e1.text != e2.text:
            return False
        if e1.tail != e2.tail:
            return False
        if e1.attrib != e2.attrib:
            return False
        if len(e1) != len(e2):
            return False
        return all(
            xml_elements_equal(c1, c2) for c1, c2 in zip(
                sorted(e1, key=lambda x: x.tag),
                sorted(e2, key=lambda x: x.tag)
            ))

    def xml_strings_equal(xml1, xml2, ignore_xpaths):
        """ Test equivalence of two xml strings `xml1` and `xml2`, but ignoring nodes that match `ignore_xpaths` """

        parser = etree.XMLParser(remove_comments=True, remove_pis=True, remove_blank_text=True)
        xml1_root = etree.fromstring(xml1, parser)
        xml2_root = etree.fromstring(xml2, parser)

        # drop ignored XML nodes
        for xml_root in [xml1_root, xml2_root]:
            for ignore_xpath in ignore_xpaths:
                ignored_nodes = xml_root.xpath(ignore_xpath)
                if type(ignored_nodes) != list:
                    raise ValueError(
                        "XPath expression '%s' is not supported, it must be point to XML node(s)" % ignore_xpath)

                for ignored_node in ignored_nodes:
                    if type(ignored_node) != etree._Element and type(ignored_node) != etree.ElementTree.Element:
                        raise ValueError(
                            "XPath expression '%s' is not supported, it must be point to XML node(s)" % ignore_xpath)

                    ignored_node.getparent().remove(ignored_node)

        return xml_elements_equal(xml1_root, xml2_root)

    def make_xml_path(xml_root, path):
        """ Create XML node hierarchy, adding child nodes if required, to match the given `path`. """
        if path[0] != '/':
            raise ValueError("XML path '%s' is not absolute" % path)

        path_segments = path[1:].split('/')[1:]  # drop leading slash and root node

        node = xml_root
        for path_segment in path_segments:
            child = node.find(path_segment)
            if child is None:
                child = etree.SubElement(node, path_segment)
            node = child
        return node

    def update_xml_desc(old_xml, new_xml, keep_xpaths):
        """ Add nodes from `old_xml` to `new_xml` as specified in `keep_xpaths`"""

        new_xml_root = etree.fromstring(new_xml)
        old_xml_root = etree.fromstring(old_xml)
        old_xml_tree = old_xml_root.getroottree()

        # drop XML nodes from new xml that should be kept
        for keep_xpath in keep_xpaths:
            keep_nodes = new_xml_root.xpath(keep_xpath)
            if type(keep_nodes) != list:
                    raise ValueError(
                        "XPath expression '%s' is not supported, it must be point to XML node(s)" % keep_xpath)

            for keep_node in keep_nodes:
                keep_node.getparent().remove(keep_node)

        # replace XML nodes in new xml that should be kept with XML nodes from old xml
        for keep_xpath in keep_xpaths:
            for old_node in old_xml_root.xpath(keep_xpath):
                if type(old_node) != etree._Element and type(old_node) != etree.ElementTree.Element:
                        raise ValueError(
                            "XPath expression '%s' is not supported, it must be point to XML node(s)" % keep_xpath)

                old_parent_path = old_xml_tree.getpath(old_node.getparent())
                new_parent_node = make_xml_path(new_xml_root, old_parent_path)
                new_parent_node.append(copy.deepcopy(old_node))

        return to_native(etree.tostring(new_xml_root))
