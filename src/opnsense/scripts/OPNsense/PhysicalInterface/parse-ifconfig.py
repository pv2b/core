#!/usr/local/bin/python2.7

import subprocess
import re
import json
import sys


_ifconfigRegexes = []
class IfconfigParser(object):
    class _IfconfigRegex(object):
        def __init__(self, *regex_args, **regex_kwargs):
            self.r = re.compile(*regex_args, **regex_kwargs)
        def __call__(self, f):
            _ifconfigRegexes.append((self.r, f))
            del self.r
            return f

    @_IfconfigRegex(r'^(.+): flags=[0-9a-f]+<(.*)>(?: metric (\d+))?(?: mtu (\d+))?$')
    def _parseInterfaceStart(self, m):
        ifname, flags, metric, mtu = m.groups()
        self._iface = self._ifaces[ifname] = {'flags': flags.split(',')}
        if metric:
            self._iface['metric'] = int(metric)
        if mtu:
            self._iface['mtu'] = int(mtu)

    @_IfconfigRegex('^\t'r'options=[0-9a-f]+<(.*)>$')
    def _parseOptions(self, m):
        options, = m.groups()
        self._iface['options'] = options.split(',')

    @_IfconfigRegex('^\t'r'ether ((?:[0-9a-f]{2}:){5}[0-9a-f]{2})$')
    def _parseEther(self, m):
        ether, = m.groups()
        self._iface['ether'] = ether

    # Jamie Zawinski <jwz@netscape.com> wrote on Tue, 12 Aug 1997 13:16:22 -0700:
    # > Some people, when confronted with a problem, think "I know,
    # > I'll use regular expressions."  Now they have two problems.
    #
    # The regex of this is based on a reading of FreeBSD's
    # sbin/ifconfig/af_inet6.c:in6_status() function
    # https://svnweb.freebsd.org/base/releng/10.3/sbin/ifconfig/af_inet6.c?view=markup#l169
    @_IfconfigRegex('^\\\t'r'''inet6
        # IPv6 Address with optional interface part for link-local addresses
        # We don't send back the %-part.
        \ (?P<addr>[0-9a-f:]+)(?:%.+)?
        # Optional destination address
        (?:\ -->\ (?P<dstaddr>[0-9a-f:]+))?
        # Prefix length (mandatory)
        (?:\ prefixlen\ (?P<prefixlen>\d+))
        # Optional flags (space-separated strings)
        (?:\ (?P<flags>.+))?
        # Scope ID (optional)
        (?:\ scopeid\ (?P<scopeid>0x[0-9a-f]+))?
        # pltime and vltime (optional but always appear together)
        # Apparently, there is code in ifconfig (af_inet6.c:sec2str) that is
        # intended to human-format (1d4h0m57s) the lifetimes here. Right now,
        # this seems to be disabled, and it just prints out the number of
        # seconds, but we should handle this anyway. It can also be "infty"
        # representing infinity.
        (?:
            \ pltime\ (?:
                (?P<pltime_infinity>infty)
            |
                (?P<pltime_bareseconds>\d+)
            |
                (?:
                    (?:
                        (?:
                            (?:
                                (?P<pltime_days>\d+)d
                            )?
                            (?P<pltime_hours>\d+)h
                        )?
                        (?P<pltime_minutes>\d+)m
                    )?
                    (?P<pltime_seconds>\d+)s
                )
            )
            \ vltime\ (?:
                (?P<vltime_infinity>infty)
            |
                (?P<vltime_bareseconds>\d+)
            |
                (?:
                    (?:
                        (?:
                            (?:
                                (?P<vltime_days>\d+)d
                            )?
                            (?P<vltime_hours>\d+)h
                        )?
                        (?P<vltime_minutes>\d+)m
                    )?
                    (?P<vltime_seconds>\d+)s
                )
            )
        )?
        # VHID (for CARP, optional)
        (?:\ vhid\ (?P<vhid>\d+))?
        # Seems ifconfig like to leave a trailing space on this line...
        \ ?$
    ''', re.VERBOSE)
    def _parseInet6(self, m):
        # Whew. That was fun!

        # First, we need to consider that there may be more than one
        # address. So let's create the address object and add it to
        # self._iface['inet6'], making an empty list first if needed.
        inet6 = {}
        self._iface.setdefault('inet6', []).append(inet6)
        
        # Okay, with that out of the way, we can start setting stuff on
        # inet6, going in the same order as the regex to keep things
        # as sane as possible given the circumstances.

        g = m.groupdict()

        def _copy(key, convert=str):
            value = g[key]
            if value is not None:
                inet6[key] = value

        _copy('addr')
        _copy('dstaddr')
        _copy('prefixlen', int) # decimal...
        
        # Flags needs some special treatment. They are space-separated.
        if g['flags'] is not None:
            inet6['flags'] = g['flags'].split()

        _copy('scopeid', lambda x:int(x,16)) # hexadecimal...
        
        # Handle pltime and vltime...
        def _handle_ltime(key):
            if g[key+'_infinity'] == 'infty':
                # I would like to have used infinity here, but that's not in
                # the JSON spec, besides, this is an integer not a float.
                inet6[key] = -1
            elif g[key+'_bareseconds'] is not None:
                inet6[key] = int(g[key+'_bareseconds'])
            elif g[key+'_seconds'] is not None:
                inet6[key] = int(g[key+'_days'] or '0')*24*60*60 \
                           + int(g[key+'_hours'] or '0')  *60*60 \
                           + int(g[key+'_minutes'] or '0')   *60 \
                           + int(g[key+'_seconds'] or '0')
            # And if we don't find any of those, we simply don't set it!

        _handle_ltime('pltime')
        _handle_ltime('vltime')

        _copy('vhid', int) # decimal

    def update(self):
        p = subprocess.Popen(['/sbin/ifconfig', '-av'], stdout=subprocess.PIPE)
        self._ifaces = {}
        self._iface = None
        for line in p.stdout:
            for regex, callback in _ifconfigRegexes:
                m = regex.match(line)
                if m:
                    callback(self, m)
                    break
            else:
                self._iface.setdefault('unparsable', []).append(line)
        return self.get()

    def get(self):
        return self._ifaces

ifaces = IfconfigParser().update()
json.dump(ifaces, sys.stdout, indent=4)
for iface in ifaces.values():
    if 'unparsable' in iface:
        for unp in iface['unparsable']:
            sys.stdout.write(unp)
