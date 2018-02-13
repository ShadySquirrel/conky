#!/usr/bin/env python

import os, sys, dbus, string

# CONFIG

## show debug messages
DEBUG=False

## output configuration
'''
 available fields: status, artist, album, track, title, year, time, genre,
				   bitrate, samplerate, filepath, format
	- Note that 'filename' value is used when Title is unknown.

 max_length: maximum allowed length of displayed fields.
 
 Important: no templating possible, for now. You can just select values,
			order in which they are displyed is hardcoded. Sorry.
'''
output_contents = {
	'fields': [ "status", "artist", "album", "track", "title", "year", "time", "genre",
				   "bitrate", "samplerate", "format"],
	'max_length': 40
}

# CODE
MODULE= "ClementineMonitor"

# predefine contents of track_info.
track_info = { "status": 'Unknown/Error/Fail', "artist": None , 
				"album": None, "track": None, "title": None,
				"year": None, "time": 0, "genre": None, "bitrate": 0,
				"samplerate": 0, "file": None, 
}

# predefine contents of file_info
file_info = { "path": None, "filename": None, "format": None }

# this one prints debug output
def printd(dstr):
	if DEBUG:
		print("[%s]: %s" % (MODULE, dstr))

# this one determines now playing status
def npStatus(state):
	'''
	states are marked as: 0 - playing, 1 - paused, 2 - stopped.
	so just use a darn simple tuple, array, whatever is it called with
	appropriate indexes.
	'''
	states = ["Playing", "Paused", "Stopped"]
	return states[state]

def parseTime(time):
	mins, secs = divmod(time, 60)
	hrs, mins = divmod(mins, 60)
	
	print_hours = False
	# quick format of time display...
	# show hours only if they actually exist, add prefix zero to all
	# values under 10.	
	if hrs > 0:
		print_hours = True
		if hrs < 10:
			hrs = "0%d" % hrs
			
	if mins < 10:
		mins = "0%d" % mins
	if secs < 10:
		secs = "0%d" % secs
		
	# time elements are now strings, so...
	value = "00:00:00"
	
	if print_hours:
		value = "%s:%s:%s" % (hrs, mins, secs)
	else:
		value = "%s:%s" % (mins, secs)
	
	return value

def parsePath(file_path):
	# decide if it's a file, a stream or pure failure
	if file_path.find("file://") != -1:
		file_info['path'] = file_path.replace("file://", "")
		splt = file_path.split("/")
		file_info['filename'], file_info['format'] = os.path.splitext(splt[-1])
		file_info['format'] = (file_info['format'].replace(".", "")).upper()
	
	elif len(file_path) > 0:
		file_info['path'] = file_path

	return file_info
	
def getTrackInfo(props, state):
	# now populate known fields.
	track_info["status"] = npStatus(state)
	
	if 'artist' in props:
		track_info['artist'] = props['artist']
	
	if 'album' in props:
		track_info['album'] = props['album']
	
	if 'tracknumber' in props:
		track_info['track'] = props['tracknumber']
	
	if 'title' in props:
		track_info['title'] = props['title']
	
	if 'year' in props:
		track_info['year'] = props['year']
	
	if 'time' in props or 'mtime' in props:
		if 'time' in props:
			track_info['time'] = parseTime(props['time'])
		elif 'mtime' in props:
			# divide by 1000 because this is in miliseconds. you don't need that kind of precision here.
			track_info['time'] = parseTime(props['mtime']/1000)
	
	if 'genre' in props:		
		track_info['genre'] = props['genre']
	
	if 'audio-bitrate' in props:
		track_info['bitrate'] = props['audio-bitrate']
	
	if 'audio-samplerate' in props:
		track_info['samplerate'] = props['audio-samplerate']
	
	if 'location' in props:
		track_info['file'] = parsePath(props['location'])
	
	return track_info	

def formatField(text, linebreak=False):
	max_length = output_contents['max_length']
	
	out = text
	
	size = len(out)
	
	printd("Maximum string length: %d, current string: %d" % (max_length, size))
	
	if  size > max_length:
		if not linebreak:
			# not a line break, just strip extra characters.
			out = "%s..." % text[:max_length]
		else:
			# we need to break this one into multiple lines now.
			import math
			breaks = math.ceil(size/max_length)
			
			printd("Requires %d lines")
			i = 1
			# empty the out line.
			out = ""
			while i <= breaks:
				if i == 1:
					out += "%s" % text[:max_length]
				else:
					out +=  "\n${goto 35}%s" % text[(i-1)*max_length:i*max_length]
				i += 1
	
	return out
		
def generateNowPlaying(track_info):
	''' status, artist, album, track, title, year, time, genre,
				   bitrate, samplerate, filepath, filename, format, bpm'''
	try:
		out = output_contents['fields']
		file_info = track_info['file']
		
		if len(out) > 0:
			# start with empty string... we'll just skip missing tags and simply not show them.
			to_print = ""
			
			# first line: status, track name or filename, if track is missing.
			if "status" in out:
				to_print += "${goto 35}%s: " % track_info['status']
			
			if "title" in out:
				if track_info['title'] != None:
					to_print += "${color1}%s${color}" % formatField(track_info['title'])
				else:
					if file_info['filename'] != None:
						to_print += "${color1}%s${color}" % formatField(file_info['filename'])
					else:
						to_print += "${color1}Unknown title${color}"
			
			# break into new line.
			to_print += "\n"
			
			# second line - artist
			if "artist" in out:
				if track_info['artist'] != None:
					to_print += "${goto 35}by ${color1}%s${color}\n" % formatField(track_info['artist'])
				
			# third line - Album and year
			if "album" in out:
				if track_info['album'] != None:
					to_print += "${goto 35}from ${color1}%s${color}" % (formatField(track_info['album']))
					
					# it's useless to print year if we don't have an album, what do you think?
					if track_info['year'] != None: 
						to_print += " (${color1}%s${color})" % track_info['year']
					
					# new line break goes here because of all previous logic :)
					to_print += "\n"
			
			# fourth line - genre
			if "genre" in out:
				if track_info['genre'] != None:
					to_print += "${goto 35}Genre: ${color1}%s${color}\n" % formatField(track_info['genre'])
			
			# fifth line - track#, time, bitrate, samplerate, format.
			line5sep = False
					
			if "track" in out:
				if track_info['track'] != None:
					to_print += "${goto 35}"
					line5sep = True
					to_print += "Track\#: ${color1}%s${color}" % track_info['track']
			
			if 'time' in out:
				if track_info['time'] != None:
					if line5sep:
						to_print += " / "
					else:
						to_print += "${goto 35}"
						line5sep = True
					to_print += "Length: ${color1}%s${color}" % track_info['time']
			
			# fifth-a line, have to break it.
			line5asep = False
			if 'format' in out:
				if file_info['format'] != None:
					to_print += "\n${goto 35}Format: "
					line5asep = True
					to_print += "${color1}%s${color}" % file_info['format']
				
			if 'bitrate' in out:
				if track_info['bitrate'] != None:
					if line5asep:
						to_print += " / "
					else:
						to_print += "\n${goto 35}Format: "
						line5asep = True
					to_print += "${color1}%d kbps${color}" % track_info['bitrate']
			
			if 'samplerate' in out:
				if track_info['samplerate'] != None:
					if line5asep:
						to_print += " / "
					else:
						to_print += "\n${goto 35}Format: "
					to_print += "${color1}%d kHz${color}" % track_info['samplerate']
			
			# sixth line
			if 'filepath' in out:
				to_print += "\n${goto 35}File: ${color1}%s${color}" % formatField(file_info['path'], True)
						
			# add offset at the end of output
			to_print += "${voffset 12}"
		else:
			to_print = "${goto 35}${color1}Hey pall, I need you to configure this\n"
			to_print += "${goto 35}Check this file: %s${voffset 12}" % os.path.abspath(__file__)

		return True, to_print
	
	except Exception as e:
		printd("generateNowPlaying errored: %s" % str(e))
		return False, str(e)

try:
	# connect to dbus
	bus = dbus.SessionBus()
	remote = bus.get_object('org.mpris.clementine', '/Player')
	iface = dbus.Interface(remote, 'org.freedesktop.MediaPlayer')
	
	# now playing state
	status = iface.GetStatus()
	# track metadata
	props = iface.GetMetadata()
	
	# generate track info	
	track_info = getTrackInfo(props, status[0])
	
	# now generate now playing string
	success, np = generateNowPlaying(track_info)
	
	if success:
		print(np)
	else:
		if status[0] != 2:
			print("${goto 35}Cannot fetch current track info.\n${goto 35}Is Clementine running?${voffset 12}")
		else:
			print("${goto 35}No active playlist. Just chillin'.${voffset 24}")
	
except Exception as e:
	print("${goto 35}Something broken.\n${goto 35}Error: %s${voffset 12}" % formatField(str(e)))
