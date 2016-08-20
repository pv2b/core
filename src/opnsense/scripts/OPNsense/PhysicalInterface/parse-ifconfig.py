#!/usr/local/bin/python2.7

import subprocess
import re
import json
import sys
import socket
import struct
from collections import OrderedDict
from DataExtractor import DataExtractor

def get_ifconfig(*args, **kwargs):
    p = subprocess.Popen(['/sbin/ifconfig', '-av'], stdout=subprocess.PIPE)
    return parse_ifconfig(p.stdout, *args, **kwargs)

def parse_ifconfig(stream, output_unprocessed=False):
    def _split_options(optstring):
        optstring = optstring.strip()
        if optstring == '':
            # N.B.: ''.split(',') == [''] # not []
            return []
        else:
            return [opt.strip().lower() for opt in optstring.split(',')]
    def _ifstart():
        #if de.extract(r'\s*\bflags=[0-9a-f]+<(.*)>\b\s*'):
        if de.extract(r'\s*\bflags=[0-9a-f]+<(.*)>\s*\b'):
            iface['flags'] = _split_options(de.matches.group(1))
        if de.extract(r'\s*\bmetric (\d+)\s*\b'):
            iface['metric'] = int(de.matches.group(1))
        if de.extract(r'\s*\bmtu (\d+)\s*\b'):
            iface['mtu'] = int(de.matches.group(1))
    def _ifinfo_ether():
        if de.extract(r'\bether ((?:[0-9a-f]{2}:){5}[0-9a-f]{2})'):
            iface['ether'] = de.matches.group(1)
    def _ifinfo_options():
        if de.extract(r'\boptions=[0-9a-f]+<(.*)>'):
            iface['options'] = _split_options(de.matches.group(1))
    def _ifinfo_groups():
        if de.extract(r'\bgroups: (.*)'):
            iface['groups'] = de.matches.group(1).split()
    def _ifinfo_inet6():
        # We ignore the %-part that comes after link-local addresses...
        # Should we do this or just pass this though? Not sure.
        if not de.extract(r'\binet6 ([0-9a-f:]+)(%\w+)?\b'):
            return
        addr = de.matches.group(1)
        # Check that this is actually an IPv6 address, because doing it
        # with a regex is way too hard. Also, normalize it.
        try:
            n = socket.inet_pton(socket.AF_INET6, addr)
            addr = socket.inet_ntop(socket.AF_INET6, n)
        except:
            # If we fail, pretend like the regex didn't actually match
            de.extractfail()
            return
        if 'inet6' not in iface:
            iface['inet6'] = []
        inet6 = OrderedDict()
        iface['inet6'] += [inet6]
        inet6['addr'] = addr
        if de.extract(r'\b--> ([0-9a-f]+)(%\w+)?\b'):
            dstaddr = de.matches.group(1)
            try:
                n = socket.inet_pton(socket.AF_INET6, dstaddr)
                dstaddr = socket.inet_ntop(socket.AF_INET6, n)
                inet6['dstaddr'] = dstaddr
            except:
                # If we fail, pretend like the regex didn't actually match
                de.extractfail()
        if de.extract(r'\bprefixlen (\d+)\b'):
            inet6['prefixlen'] = int(de.matches.group(1))
        for flag in ['anycast', 'tentative', 'duplicated', 'detached',
                     'deprecated', 'autoconf', 'temporary', 'prefer_source']:
            if de.extract(r'\b' + flag + r'\b'):
                if not 'flags' in inet6:
                    inet6['flags'] = []
                inet6['flags'].add(flag)
        if de.extract(r'\bscopeid (0x[0-9a-f]+)\b'):
            inet6['scopeid'] = int(de.matches.group(1), 16)
        for ltime in ['pltime', 'vltime']:
            if de.extract(r'\b' + ltime + ' (\d+|infty)\b'):
                t = de.matches.group(1)
                if t == 'infty':
                    inet6[ltime] = -1
                else:
                    inet6[ltime] = int(t)
        m = re.search(r'\bvhid (\d+)\b', line)
        if m:
            inet6['vhid'] = int(m.group(1))
    def _ifinfo_nd6():
        if de.extract(r'\bnd6 options=[0-9a-f]+<(.*)>'):
            nd6 = iface['nd6'] = OrderedDict()
            nd6['options'] = _split_options(de.matches.group(1))
    def _ifinfo_status():
        if de.extract('^\tstatus: (.+)$'):
            iface['status'] = de.matches.group(1)
    def _ifinfo_media():
        if de.extract('^\tmedia: (.+)$'):
            iface['media'] = de.matches.group(1)
    def _ifinfo_inet():
        if not de.extract('^\tinet ([0-9\.]+)\s*'):
            return
        addr = de.matches.group(1)
        try:
            n = socket.inet_pton(socket.AF_INET, addr)
            addr = socket.inet_ntop(socket.AF_INET, n)
        except:
            # If we fail, pretend like the regex didn't actually match
            de.extractfail()
            return
        if 'inet' not in iface:
            iface['inet'] = []
        inet = OrderedDict()
        inet['addr'] = addr
        iface['inet'] += [inet]
        if de.extract(r'\s*\bnetmask (0x[0-9a-f]{1,8})\s*\b'):
            # Why does FreeBSD need to throw us a hexadecimal oddball here???
            netmask = struct.pack('!L', int(de.matches.group(1), 16))
            inet['netmask'] = socket.inet_ntoa(netmask)
        if de.extract(r'\s*\bbroadcast ([0-9\.]+)\s*\b'):
            bcast = de.matches.group(1)
            try:
                n = socket.inet_pton(socket.AF_INET, bcast)
                bcast = socket.inet_ntop(socket.AF_INET, n)
                inet['broadcast'] = bcast
            except:
                # If we fail, pretend like the regex didn't actually match
                de.extractfail()
        if de.extract(r'\s*\b--> ([0-9\.]+)\s*\b'):
            dstaddr = de.matches.group(1)
            try:
                n = socket.inet_pton(socket.AF_INET, dstaddr)
                dstaddr = socket.inet_ntop(socket.AF_INET, n)
                inet['dstaddr'] = dstaddr
            except:
                # If we fail, pretend like the regex didn't actually match
                de.extractfail()
    def _ifinfo_syncpeer():
        if not de.extract('^\tsyncpeer: ([0-9\.]+)\s*'):
            return
        addr = de.matches.group(1)
        try:
            n = socket.inet_pton(socket.AF_INET, addr)
            addr = socket.inet_ntop(socket.AF_INET, n)
        except:
            # If we fail, pretend like the regex didn't actually match
            de.extractfail()
            return
        syncpeer = iface['syncpeer'] = OrderedDict()
        syncpeer['addr'] = addr
        if de.extract(r'\bmaxupd: (\d+)\b\s*'):
            syncpeer['maxupd'] = int(de.matches.group(1))
        if de.extract(r'\bdefer: (on|off)\b\s*'):
            syncpeer['defer'] = de.matches.group(1) == 'on'

    iface = None
    ifaces = []
    for line in stream:
        linestrip = line.strip()
        # Completely skip empty lines
        if linestrip == '':
            continue
        de = DataExtractor(line)
        if de.extract('^(\w+):'):
            ifname = de.matches.group(1)
            if ifname in ifaces:
                raise Exception('Duplicate interface name %r!' % ifname)
            iface = OrderedDict()
            ifaces += [iface]
            iface['name'] = ifname
            _ifstart()
        else:
            if de.extract('^\t(\w+)'):
                category = de.matches.group(1)
                parsefuncname = '_ifinfo_' + category
                if parsefuncname in locals():
                    if not iface:
                        # For some reason we're here before our first interface start
                        # So fake it with a dummy nameless interface
                        iface = OrderedDict()
                        ifaces += [iface]
                    locals()[parsefuncname]()
        if output_unprocessed:
            unp = de.unprocessed_stripped()
            if unp:
                if 'unprocessed' not in iface:
                    iface['unprocessed'] = []
                u = OrderedDict()
                u['line'] = linestrip
                u['unprocessed'] = unp
                iface['unprocessed'] += [u]
    return ifaces

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=\
        'Output current FreeBSD interface configuration av JSON')
    parser.add_argument(
        '--unprocessed',
        help='Include unprocessed output in the JSON. Intended as a '\
             'debugging aid.',
        action='store_true'
    )
    parser.add_argument(
        '--stdin',
        help='Reads input from stdin rather than running ifconfig -av. '
             'Useful for testing.',
        action='store_true'
    )
    a = parser.parse_args()
    
    kwargs = { 'output_unprocessed': a.unprocessed }
    if a.stdin:
        ifaces = parse_ifconfig(sys.stdin, **kwargs)
    else:
        ifaces = get_ifconfig(*kwargs)
    json.dump(ifaces, sys.stdout, indent=4)
    print # json.dump does not output a trailing newline
