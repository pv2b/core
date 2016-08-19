#!/usr/local/bin/python2.7

import subprocess
import re
import json
import sys
import socket
from collections import OrderedDict

# http://stackoverflow.com/a/81899/5403670
def check_ipv6(n):
    try:
        socket.inet_pton(socket.AF_INET6, n)
        return True
    except socket.error:
        return False

def get_ifconfig(raw_output=False):
    def _ifstart():
        m = re.search(r'\bflags=[0-9a-f]+<(.+)>', line)
        if m:
            iface['flags'] = m.group(1).lower().split(',')
        m = re.search(r'\bmetric (\d+)', line)
        if m:
            iface['metric'] = int(m.group(1))
        m = re.search(r'\bmtu (\d)', line)
        if m:
            iface['mtu'] = int(m.group(1))
    def _parse_ether():
        m = re.search(r'\bether ((?:[0-9a-f]{2}:){5}[0-9a-f]{2})', line)
        if m:
            iface['ether'] = m.group(1)
    def _parse_options():
        m = re.search(r'\boptions=[0-9a-f]+<(.+)>', line)
        if m:
            iface['options'] = m.group(1).lower().split(',')
    def _parse_groups():
        m = re.search(r'\bgroups: (.*)', line)
        if m:
            iface['groups'] = m.group(1).split()
    def _parse_inet6():
        # We ignore the %-part that comes after link-local addresses...
        # Should we do this or just pass this though? Not sure.
        m = re.search(r'\binet6 ([0-9a-f:]+)(%\w+)?\b', line)
        if not m:
            return
        addr = m.group(1)
        # Check that this is actually an IPv6 address, because doing it
        # with a regex is way too hard.
        if not check_ipv6(addr):
            return
        if 'inet6' not in iface:
            iface['inet6'] = OrderedDict()
        inet6 = iface['inet6'][addr] = OrderedDict()
        m = re.search(r'\b--> ([0-9a-f]+)(%\w+)?\b', line)
        if m:
            dstaddr = m.group(1)
            if check_ipv6(dstaddr):
                inet6['dstaddr'] = m.group(1)
        m = re.search(r'\bprefixlen (\d+)\b', line)
        if m:
            inet6['prefixlen'] = int(m.group(1))
        for flag in ['anycast', 'tentative', 'duplicated', 'detached',
                     'deprecated', 'autoconf', 'temporary', 'prefer_source']:
            if re.search(r'\b' + flag + r'\b', line) != None:
                if not 'flags' in inet6:
                    inet6['flags'] = []
                inet6['flags'].add(flag)
        m = re.search(r'\bscopeid (0x[0-9a-f]+)\b', line)
        if m:
            inet6['scopeid'] = int(m.group(1), 16)
        m = re.search(r'\bpltime (\d+|infty)\b', line)
        if m:
            t = m.group(1)
            if t == 'infty':
                t = -1
            else:
                t = int(t)
            inet6['pltime'] = t
        m = re.search(r'\bvltime (\d+|infty)\b', line)
        if m:
            t = m.group(1)
            if t == 'infty':
                t = -1
            else:
                t = int(t)
            inet6['vltime'] = t
        m = re.search(r'\bvhid (\d+)\b', line)
        if m:
            inet6['vhid'] = int(m.group(1))

        
    p = subprocess.Popen(['/sbin/ifconfig', '-av'], stdout=subprocess.PIPE)
    ifaces = OrderedDict()
    iface = None
    re_ifstart = re.compile('^(\w+):')
    re_ifinfo = re.compile('^\t(\w+)')
    for line in p.stdout:
        m = re_ifinfo.match(line)
        if m:
            category = m.group(1)
            parsefuncname = '_parse_' + category
            if parsefuncname in locals():
                locals()[parsefuncname]()
            if raw_output:
                iface['raw_ifconfig'].append(line.strip())
            continue
        m = re_ifstart.match(line)
        if m:
            ifname = m.group(1)
            if ifname in ifaces:
                raise Exception('Duplicate interface name %r!' % ifname)
            iface = ifaces[ifname] = OrderedDict()
            if raw_output:
                iface['raw_ifconfig'] = [line.strip()]
            _ifstart()
    return ifaces

ifaces = get_ifconfig(True)
json.dump(ifaces, sys.stdout, indent=4)
