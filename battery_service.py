import os, sys
from sh import acpi

# we need path to adapter state file, battery now/max file and battery status file
# will probably add more data soon.
paths = {
	"battery_path": "/sys/class/power_supply/BAT1/",
	"adapter": "/sys/class/power_supply/ACAD/online",
	"battery_now": "/sys/class/power_supply/BAT1/charge_now",
	"battery_design": "/sys/class/power_supply/BAT1/charge_full_design",
	"battery_max": "/sys/class/power_supply/BAT1/charge_full",
	"status": "/sys/class/power_supply/BAT1/status",
	"make": "/sys/class/power_supply/BAT1/manufacturer",
	"model": "/sys/class/power_supply/BAT1/model_name",	
	"min_volt": "/sys/class/power_supply/BAT1/voltage_min_design",
	"cur_volt": "/sys/class/power_supply/BAT1/voltage_now",
}
debug = False

#### here be dragons!

# print debug output
def printd(txt):
	flag = "BatteryStats"
	if debug and len(txt) > 0:
		print("[%s] %s" % (flag, txt))

# converts Amp-hour to Watt-hour
def Ah2Wh(amps, volts):
	import math
	
	amps = amps/1000000
	return round((amps*volts)/math.pow(10, 6), 1)

# get battery and charger data. do a preset in case something is missing
adapter_online = False
battery_now = 0
battery_design = 100
battery_max = 100
health = "Unknown"
status = "Unknown"
min_volt = 11
cur_volt = 13
make = "N/A"
model = "N/A"

# display text variable
to_print = ""
# check if battery is there
if os.path.isdir(paths["battery_path"]):
	# this one reports just zero or one, so if it's one, set adapter_online to true
	if os.path.isfile(paths["adapter"]):
		with open(paths["adapter"]) as f:
			a_online = f.read()
			if int(a_online) == 1:
				adapter_online = True
			f.close()

	# units for these are nAh (nano!!! amp-hour). I don't have a damn idea why nano...
	if os.path.isfile(paths["battery_now"]):
		with open(paths["battery_now"]) as f:
			battery_now = f.read()
			battery_now = float(battery_now)
			f.close()

	if os.path.isfile(paths["battery_design"]):
		with open(paths["battery_design"]) as f:
			battery_design = f.read()
			battery_design = float(battery_design)
			f.close()

	if os.path.isfile(paths["battery_max"]):
		with open(paths["battery_max"]) as f:
			battery_max = f.read()
			battery_max = float(battery_max)
			f.close()

	# get voltages
	if os.path.isfile(paths["min_volt"]):
		with open(paths["min_volt"]) as f:
			min_volt = f.read()
			min_volt = float(min_volt)
			f.close()

	if os.path.isfile(paths["cur_volt"]):
		with open(paths["cur_volt"]) as f:
			cur_volt = f.read()
			cur_volt = float(cur_volt)
			f.close()

	# this returns battery status: full, discharging, charging
	if os.path.isfile(paths["status"]):
		with open(paths["status"]) as f:
			status = f.read()
			status = status.strip() # have to strip it, it has a newline at the end...
			f.close()
			
	# and this returns make and model
	if os.path.isfile(paths["make"]):
		with open(paths["make"]) as f:
			make = f.read()
			make = make.strip() # have to strip it, it has a newline at the end...
			f.close()

	if os.path.isfile(paths["model"]):
		with open(paths["model"]) as f:
			model = f.read()
			model = model.strip() # have to strip it, it has a newline at the end...
			f.close()
	
	printd("Adapter: %s; Battery: %s, battery now: %.1f, battery design: %.1f, battery max: %.1f; made by %s, model %s" % (str(adapter_online), status, battery_now, battery_design, battery_max, make, model))

	# let's store icons with their appropriate min and max values in arrays, for both cases
	# this is for charging.
	icons_charging = {
		"Q": [0, 20],
		"W": [20, 40],
		"E": [40, 60],
		"R": [60, 80],
		"T": [80, 100]
	}
	
	# this is discharging
	icons_discharging = {
		"1": [0, 20],
		"2": [20, 40],
		"3": [40, 60],
		"4": [60, 80],
		"5": [80, 100]
	}
	
	# arrays are nice, so I'm packing all setting in them
	icons_font = {
		True: { "name": "Poky", "size": "16" },
		False: { "name": "ConkyColors", "size": "18" }
	}
	
	# we'll use this array to determine if battery health is good.
	# some say that broken battery goes between 30 and 45%
	# I'd rather use different scale...
	battery_health = {
		"Excellent": [80, 100],
		"Good": [60, 80],
		"Ok": [45, 60],
		"Bad": [30, 45],
		"Broken": [0, 30]
	}

	# calulations...
	battery_left = round((battery_now/battery_max)*100, 2)
	battery_life = round((battery_max/battery_design)*100, 2)
	
	# determine battery health.
	for h in battery_health:
		hd = battery_health[h]
		
		if battery_life > hd[0] and battery_life <= hd[1]:
			health = h
	
	printd("Determined battery health: %s: %.1f %%" % (health, battery_life))

	# we'll use 100% full icon as fallback
	icon = icons_discharging["1"]
	# let's say we'd preffer discharging icons as default
	icons = icons_discharging
	
	# now depending on the state, change an icon set
	icon_font = icons_font[adapter_online]
	printd("Adapter online? %s -> using %s" % (str(adapter_online), str(icon_font)))
	
	# ... and select charging set if charger is available
	if adapter_online:
		icons = icons_charging
			
	for i in icons:
		min_c = icons[i][0]
		max_c = icons[i][1]
				
		if min_c < battery_left and battery_left <= max_c:
			icon = i
			printd("Determined icon: %s for charge %d%% (min %d, max %d)" % (icon, battery_left, min_c, max_c))

	# set it as None because we may never use it, but need it initialised out of scope.
	remaining = None
	show_timer = False
	# now, in case we're charging or discharging, grab ACPI output to show how long before battery is full/empty
	if status == "Charging" or status == "Discharging":
		acpi_out = acpi("-b").strip() # again, new line...	
		# parse it, we need just timers...
		acpi_out = acpi_out.split(",") # split into blocks
		r = acpi_out[len(acpi_out)-1].strip().split() # grab just time, that is last block
		
		remaining = r[0].strip()
		show_timer = True
		
		printd("Battery is %s, %s remaining!" % (status, remaining))
	
	# time to generate report! #
	
	# set icon
	to_print = "${color3}${font %s:size=%s}%s${font}${color}${voffset -8}" % (icon_font["name"], icon_font["size"], icon)
	
	# show charge data
	if show_timer:
		to_print += "${goto 35}${color}Battery: ${color1}%s${color}  / ${color1}%.1f%%${color} / ${color1}%s ${color}left${font}\n" % (status, battery_left, remaining)
	else:
		to_print += "${goto 35}${color}Battery: ${color1}%s${color} / ${color1}%s%%${color}${font}\n" % (status, battery_left)
	
	# show manufacturer data
	to_print += "${voffset 4}${goto 35}${color}Make: ${color1}%s ${color}/ Model: ${color1}%s${color}${font}\n" % (make, model)
	
	# show capacity in Ah
	to_print += "${goto 35}${color}Capacity: ${color1}%.1f Ah ${color}(${color1}%.1f%%${color}) / ${color1}%.1f Ah ${color}max${font}\n" % (battery_max/100000, battery_life, battery_design/100000)
	
	# show capacity in Wh
	to_print += "${goto 80}${color}${color1}%.1f Wh ${color} / ${color1}%.1f Wh ${color}max${font}\n" % (Ah2Wh(battery_max, min_volt), Ah2Wh(battery_design, min_volt))
	
	# show health status based on battery_health array
	to_print += "${goto 35}${color}Health: ${color1}%s${color}${font}\n" % health
	
	# show voltage
	to_print += "${goto 35}${color}Voltage: ${color1}%.1f V${color} / ${color1}%.1f V${color} min${font}\n" % (cur_volt/1000000, min_volt/1000000)
	
else:
	icon = icons_discharging["1"]
	to_print = "${color3}${font ConkyColors:size=18}%s${font}${color}${voffset -8}${goto 35}${color1}%s${color}${font}" % (icon, "Battery is faulty or not present")
	
# finally, show info on conky. DON'T FORGET TO DISABLE DEBUG FLAG'
print(to_print)
