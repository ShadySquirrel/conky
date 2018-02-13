#!/usr/bin/python
import os

# Configuration

## List of cloud storages. Save as indexed array in format { 'name': string, 'path': string, 'size': double, "fuse": bool }
## why Fuse marking? Because FUSE based cloud storages can use native conky functions.
storages = [
	{ "name": "Dropbox", "path": "/home/user/Dropbox", "size": 6.88, "fuse": False },
	{ "name": "Google Drive", "path": "/home/user/Google Drive", "size": None, "fuse": True },
	{ "name": "One Drive", "path": "/home/user/OneDrive", "size": 5.00, "fuse": False },
]
## show debug messages
DEBUG=False


# CODE
MODULE= "CloudStorage"

# this one prints debug output
def printd(dstr):
	if DEBUG:
		print("[%s]: %s" % (MODULE, dstr))

# this one gets folder size.
def getFolderSize(folder):
    total_size = os.path.getsize(folder)
    for item in os.listdir(folder):
        itempath = os.path.join(folder, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += getFolderSize(itempath)
    return total_size

def byte2gigabyte(bytesize, rnd):
	import math
	mb = bytesize/math.pow(1024, 2)
	gb = round(mb/1024, 2)

	return gb

# now, loop through storages and do magic stuff.
to_print = "${font Fira Sans:size=8}${color}Service${goto 195}Total${goto 240}Used${goto 285}Free${color}${font}\n"
to_print += "${voffset -8}${goto 35}${hr 1}${color1}\n"
for storage in storages:
	if not storage['fuse']:
		# check if path exists.
		if os.path.isdir(storage['path']):
			total_size = round(storage['size'],2)
			folder_size = byte2gigabyte(getFolderSize(storage['path']),2)

			free_size = round(total_size - folder_size,2)
			used_size = round(total_size - free_size, 2)

			printd("Storage: %s (%s)-> Total: %.2f GB, used %.2f GB, free %.2f GB" % (storage['name'], storage['path'], total_size, used_size, free_size))

			to_print += str("${goto 35}%s${goto 192}%.2fGiB${goto 237}%.2fGiB${goto 282}%.2fGiB" % (storage['name'], total_size, used_size, free_size))
		else:
			printd("Storage %s (%s) not available." % (storage['name'], storage['path']))
			to_print += str("${goto 35}%s${goto 225}Not available." % (storage['name']))
	else:
		printd("Storage %s (%s) is fuse based, using conky functions." % (storage['name'], storage['path']))

		# check if FUSE storage is mounted!!!
		if os.path.ismount(storage['path']):
			to_print += str("${goto 35}%s${goto 192}${fs_size %s}${goto 237}${fs_used %s}${goto 282}${fs_free %s}" % (storage['name'], storage['path'], storage['path'], storage['path']))
		else:
			printd("Storage %s (%s) not mounted." % (storage['name'], storage['path']))
			to_print += str("${goto 35}%s${goto 225}Not available." % (storage['name']))

	index = (storages.index(storage)+1)
	if index < len(storages):
		to_print += "\n"

print(to_print)
