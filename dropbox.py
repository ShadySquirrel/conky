#!/usr/bin/python
import os

# VARIABLES
DROPBOX_PATH="/home/user/Dropbox"
DROPBOX_SIZE=6.88 # enter in GB please, grab from website, two decimal places
DEBUG=False

# DO NOT TOUCH PREKIDACH
DB_TOTAL=round(DROPBOX_SIZE,2)

def getFolderSize(folder):
    total_size = os.path.getsize(folder)
    for item in os.listdir(folder):
        itempath = os.path.join(folder, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += getFolderSize(itempath)
    return total_size

size_b = getFolderSize(DROPBOX_PATH)
size_kb = size_b/1024
size_mb = size_kb/1024
size_gb = round(size_mb/1024,2)
free_gb = round(DB_TOTAL-size_gb,2)
free_perc = round((size_gb/DB_TOTAL)*100,1)

# just to make sure calculation is the same as one on the Dropbox applet, print if debug flag is on
if DEBUG:
	print("dropbox used size is",size_gb,"GB")
	print("dropbox total size is",DB_TOTAL,"GB")
	print("dropbox free space is",free_gb,"GB")
	print("dropbox usage in % is",free_perc,"%")

print("${goto 35}Dropbox${goto 120}"+str(DB_TOTAL)+"GiB${goto 175}"+str(size_gb)+"GiB${goto 235}"+str(free_gb)+"GiB${goto 295}")
