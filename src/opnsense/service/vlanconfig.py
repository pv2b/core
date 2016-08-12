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

# Get the desired interfaces
desired_interfaces = {}
for line in file('/tmp/vlan_dump'):
    iface, vlandev, vlan = line.split()
    desired_interfaces[iface] = vlandev, vlan

# Create sets of the interface names (yay set algebra!)
cur = set(current_interfaces.keys())
des = set(desired_interfaces.keys())

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
    vlan, vlandev = desired_interfaces[iface]
    ifconfig(iface, "create", "vlandev", vlandev, "vlan", vlan)

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
    des_config = desired_interfaces[iface]
    if cur_config != des_config:
        vlandev, vlan = des_config
        # FreeBSD requires us to remove current VLAN configuration before
        # changing it, or you get an EBUSY.
        ifconfig(iface, "-vlandev")
        ifconfig(iface, "vlandev", vlandev, "vlan", vlan)

# Now, observe the above Ascii Venn diagrams and note that we've handled each
# interface once and only once. Thank you, Mr. Ascii Venn!

exit(exitcode)
