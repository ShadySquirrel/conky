#!/usr/bin/env python

import os, string
from sh import mount, lsblk

## show debug messages
DEBUG=False
demo_mode = True # setting this to true hides partition labels and uses generic dev entries.

# CODE
MODULE= "StorageMonitor"


# this one prints debug output
def printd(dstr):
	if DEBUG:
		print("[%s]: %s" % (MODULE, dstr))

def real_fs(part):
	info = lsblk("-no", "name,fstype", part).strip()
	info = info.split(" ")
	printd(info)
	
	return info[1]

def parse_mounts():
	mountpoints = []
	out = mount().strip().split("\n")
	
	for o in out:
		o1 = o.split(" on ")		
		
		o2 = o1[1].split(" type ")
		short_mount = o2[0].strip().replace("/run/media/igor/", "")
		short_mount = short_mount.replace("/media/", "")
		
		o3 = o2[1].split();
		if o3[0] == "fuseblk":
			fs = real_fs(o1[0].strip())
		else:
			fs = o3[0].strip()
		
		mountpoints.append({"drive": o1[0].strip(), "mount": o2[0].strip(), "short_mount": short_mount, "fs": fs})
	
	return mountpoints

mountpoints = parse_mounts()
to_print = "${goto 35}Disk/Mount pt.${goto 160}Type${goto 195}Total${goto 240}Used${goto 285}Free\n"
to_print += "${voffset -8}${goto 35}${color1}${hr 1}\n"
# loop all sd{a..z} devices
for major in string.ascii_lowercase:
	drive = "/dev/sd%s" % major
	
	# check if /dev/sdX exists
	if os.path.exists(drive):
		has_mounted_parts = False
		# loop all sdX{0-9} devices
		for minor in string.digits:
			partition = "%s%s" % (drive, minor)
			
			# now, check if it's mounted
			if os.path.exists(partition):
				printd("checking %s" % partition)
				mounted = False
				dev = None
				
				for pt in mountpoints:
					if pt['drive'] == partition:
						dev = pt
						mounted = True
						
				printd("is %s mounted? %s" % (partition, str(mounted)))
				
				# if partition is mounted, show info
				if mounted:
					# add descriptive block before, because we don't want to show drives which aren't mounted
					if not has_mounted_parts:
						to_print += "${goto 35}${color1}%s${color} (${color1}${diskio_write %s}${color} in, ${color1}${diskio_read %s}${color} out)\n" % (drive, drive, drive)
						to_print += "${voffset -8}${goto 35}${color0}${hr 1}\n"
						has_mounted_parts = True
					# partition info now...
					if not demo_mode:
						mnt = dev['short_mount'][:100]+"..." if len(dev['short_mount']) > 100 else dev['short_mount']
					else:
						mnt = "sd%s%s" % (major, minor)
					
					to_print += "${goto 35}|-${color1}%s${goto 162}%s${goto 192}${fs_size %s}${goto 237}${fs_used %s}${goto 282}${fs_free %s}${color}\n" % (mnt, dev['fs'][:5], dev['mount'], dev['mount'], dev['mount'])
			else:
				printd("%s doesn't exist" % partition)
		to_print += "${voffset 5}"
	else:
		printd("%s doesn't exist" % drive)

# output
print(to_print)
