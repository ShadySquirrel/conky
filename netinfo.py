#!/usr/bin/python
import os, sys
from sh import ls, cat, ifconfig, wget

# debugging on/off switch
DEBUG = False
MODULE= "NetInfo"

def printd(dstr):
	if DEBUG:
		print("[%s]: %s" % (MODULE, dstr))

def grabInterfaceData(iface, iface_type):
	iface_data = ifconfig(iface)
	w = iface_data.strip().split(":", 1) # to remove interface name from details
	tmp = w[1].strip().split("\n")
	
	i = 0
	ret = {}
	for x in tmp:
		if i > 0: # ignore first line
			line = x.strip().split("  ")
			for d in line:
				data = d.split()
				if data[0] in ["inet", "netmask", "broadcast", "destination", "inet6", "prefixlen", "ether"]:
					ret[data[0]] = data[1]
		i+=1
	
	return ret

def getState(iface):
	state = False
	# do a check only if interface path exists.
	if os.path.isdir("/sys/class/net/%s" % iface):
		s = cat("/sys/class/net/%s/link_mode" % iface).strip()
		s1 = cat("/sys/class/net/%s/operstate" % iface).strip()
		
		if s == "0" and s1 in ["up", "unknown"]:
			state = True
		elif s == "1" and s1 == "up": # damn wifi adapter returns 1, whatever is going on...
			state = True

	return state

def getWanIP(bind_to):
	printd("- Getting WAN ip from %s" % bind_to)
	ip = None
	try:
		ip = wget("--bind-address=%s" % bind_to, "-T 2", "--tries=1", "-qO-","https://api.ipify.org").strip()
		printd("-> WAN IP: %s" % ip)
	except:
		printd("-> Failed getting WAN IP, returning false.")
		ip = False
	
	return ip

# determine interface ICON and TYPE
# - inteface types:
# * en -- ethernet
# * sl -- serial line IP (slip)
# * wl -- wlan
# * ww -- wwan
# define in format interface:[icon, description]
iface_types = { 
	"en": ["d", "Ethernet"], 
	"sl": ["j", "Serial line"],
	"wl": ["k", "Wireless"],
	"ww": ["E", "WAN"],
	"lo": ["y", "Loopback"],
	"tu": ["E", "Virtual (TUN)"],
	"ta": ["E", "Virtual (TAN)"],
	"unk": ["E", "Unknown"]
}

# ignored interfaces
ignored_interfaces = ["lo"]

# interface lists
interfaces = ls("/sys/class/net").split()

printd("Interfaces: %d" % len(interfaces))

iface_text = ""
for i in interfaces:
	if i not in ignored_interfaces and getState(i):
		printd("Interface %s is up, parsing..." % i)
		
		iface_type = i[0:2]
		printd("- Interface type: %s" % iface_type)
		
		iface_desc = []
		if iface_type in iface_types:
			iface_desc = iface_types[iface_type]
		else:
			iface_desc = iface_types["unk"]
		
		printd("- Interface details: [icon, description]: %s" % str(iface_desc))
		
		iface_data = grabInterfaceData(i, iface_type)
		printd(iface_data)
		
		iface_text += "${if_up %s}${color3}${font ConkyColors:size=18}%s${font}${color}${voffset -26}\n" %  (i, iface_desc[0])
		# display adapter info - type, MAC etc.
		iface_text += "${goto 35}Interface: ${color1}%s${color} / Type: ${color1}%s${color}\n" % (i, iface_desc[1])
		if 'ether' in iface_data:
			iface_text += "${goto 35}MAC: ${color1}%s${color}\n" % iface_data['ether']
		# add more data from ifconfig
		if "inet" in iface_data:
			iface_text += "${goto 35}Addr: ${color1}%s${color} / Netmask: ${color1}%s${color}\n" % (iface_data['inet'], iface_data['netmask'])
		if 'broadcast' in iface_data:
			iface_text += "${goto 35}Broadcast: ${color1}%s${color}" % iface_data['broadcast']
		elif 'destination' in iface_data:
			iface_text += "${goto 35}Destination: ${color1}%s${color}" % iface_data['destination']
		
		if 'broadcast' in iface_data or 'destination' in iface_data:
			wanIP = getWanIP(iface_data['inet'])
			if wanIP != False:
				iface_text += " / WAN: ${color1}%s${color}\n" % wanIP
			else:
				iface_text += "\n"
		
		if 'inet6' in iface_data:
			iface_text += "${goto 35}Addr6: ${color1}%s${color} / Addrlen: ${color1}%s${color}\n" % (iface_data['inet6'], iface_data['prefixlen'])
				
		if iface_type == "wl":
			iface_text += "${goto 35}AP: ${color1}${wireless_essid %s}${color} (${color2}${wireless_mode %s})${color}${font} / ${color1}${wireless_link_qual %s}%%${color}${font} / ${color1}${wireless_bitrate %s}${color}${font}\n" % (i, i, i, i)
				
		iface_text += "${goto 35}Download: ${color1}${downspeed %s}${color}${font} / Total: ${color1}${totaldown %s}${color}${font}\n" % (i, i)
		iface_text += "${goto 35}Upload: ${color1}${upspeed %s}${color}${font} / Total: ${color1}${totalup %s}${color}${font}${endif}\n\n" % (i, i)
	else:
		printd("Interface %s is down, not parsing" % i)
print(iface_text)
