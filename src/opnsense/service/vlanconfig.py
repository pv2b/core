#!/usr/local/bin/python2.7

from subprocess import Popen, check_output, CalledProcessError, STDOUT, PIPE
from re import match
from syslog import syslog, LOG_ERR
from sys import exit, stderr

IFCONFIG_PATH = "/sbin/ifconfig"
exitcode = 0

# Call ifconfig and log failures!
def ifconfig(*arguments):
    global exitcode
    if not arguments:
        return
    try:
        check_output([IFCONFIG_PATH] + list(arguments), stderr=STDOUT)
    except CalledProcessError, e:
        errmsg = \
            'vlanconfig.py - Error calling %r, exit code: %d, output %r' % \
            (e.cmd, e.returncode, e.output)
        syslog(LOG_ERR, errmsg)
        print >> stderr, errmsg
        exitcode = 1

# Get the currently configured interfaces
current_interfaces = {}
p = Popen([IFCONFIG_PATH], stdout=PIPE)
for line in p.stdout:
    m = match('^(\w+):', line)
    if m:
        iface = m.group(1)
        continue
    m = match('^\s*vlan: (\d+) parent interface: (\w+)', line)
    if m:
        vlan = m.group(1)
        vlandev = m.group(2)
        current_interfaces[iface] = vlandev, vlan

# Load the desired config from /etc/rc.conf.d/vlan
# FIXME This parser is just barely smart enough to parse what is emitted
#       by our templates, and no more.
rc_conf={}
for line in file('/etc/rc.conf.d/vlan'):
    m = match('^\s*(.+)\s*=\s*"(.+)"\s*(#.*)?$', line)
    if m:
        rc_conf[m.group(1)] = m.group(2)

# Create sets of the interface names (yay set algebra!)
cur = set(current_interfaces.keys())
des = set(rc_conf['cloned_interfaces'].split())

#     cur      des      
#   .--''-...--''--.
# .'####.'  '.      '.
# :#####:    :       :
# :#####:    :       :
# '.####'.  .'      .'
#   '--..-'''--..--'
# 
# Any interfaces that are currently configured, and are not desired should
# be deleted.

for iface in cur - des:
    ifconfig(iface, "destroy")

#     cur      des      
#   .--''-...--''--.
# .'    .'  '.######'.
# :     :    :#######:
# :     :    :#######:
# '.    '.  .'######.'
#   '--..-'''--..--'
# 
# Any interfaces that are desired, but not currently configured, should be
# created.
for iface in des - cur:
    create_args = rc_conf['create_args_' + iface].split()
    ifconfig(iface, "create", *create_args)

#     cur      des      
#   .--''-...--''--.
# .'    .'##'.      '.
# :     :####:       :
# :     :####:       :
# '.    '.##.'      .'
#   '--..-'''--..--'
# 
# Any interfaces that are both desired and configured should be reconfigured
# if any settings are different.
for iface in des & cur:
    cur_config = current_interfaces[iface]
    create_args = rc_conf['create_args_' + iface].split()
    des_vlan = create_args[create_args.index('vlan') + 1]
    des_vlandev = create_args[create_args.index('vlandev') + 1]
    if cur_config != (des_vlan, des_vlandev):
        # FreeBSD requires us to remove current VLAN configuration before
        # changing it, or you get an EBUSY.
        ifconfig(iface, "-vlandev")
        ifconfig(iface, *create_args)

# Now, observe the above Ascii Venn diagrams and note that we've handled each
# interface once and only once. Thank you, Mr. Ascii Venn!

exit(exitcode)
