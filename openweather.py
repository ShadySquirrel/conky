#!/usr/bin/python
import os, sys, requests, json, time, datetime

# API key. Get your own!
key = '5cebdf6797cdca00a9bdb706c873c529'
# list of cities, bitch!
cities = ['792680']
# where to store data
storage = "/home/user/.conky/tmp/"
# update period, in minutes
update_period = 20
# debug mode
debug = False

# list of icons
icons = {
# store in format openweather icon: font icon # condition description
"01d": "a", "01n": "A", # 	clear sky
"02d": "b", "02n": "D", #	few clouds
"03d": "d", "03n": "C", #	scattered clouds
"04d": "e", "04n": "f", #	broken clouds
"09d": "j", "09n": "j", #	shower rain
"10d": "g", "10n": "G", #	rain
"11d": "m", "11n": "K", #	thunderstorm
"13d": "r", "13n": "r", #	snow
"50d": "9", "50n": "9", #	mist
}
def printd(txt):
	flag = "OpenWeather"
	if debug and len(txt) > 0:
		print("[%s] %s" % (flag, txt))

# start code.
weather_results = []


def check_age(time_refreshed):
	time_now = time.time()

	time_diff = time_now - time_refreshed

	# guess that data is always old
	state = False

	# convert update period to seconds
	too_old = update_period * 60

	printd("Data from %s, now %s, difference %s, max %s" % (str(time_refreshed), str(time_now), str(time_diff), str(too_old)))

	# now, check if data is actually old
	if too_old <= time_diff :
		state = True

	return state

def weather_get(city):
	# let's say there is no data.
	weather_data = None

	# where current data is stored.
	weather_file = "%s/openweather_%s.json" % (storage, city)

	# check if we already have data, if not, download.
	if not os.path.isfile(weather_file):
		printd("No data found, send request")
		weather_data = request_data(city)
		weather_data['refresh_time'] = time.time()
		writeWeatherData(weather_data)
	else:
		# we found old data, good, let's check how old it is.
		printd("Old data Found, loading and checking")
		with open(weather_file, "r") as f:
			weather_data = json.load(f)
			f.close()

		# time we have refreshed that database is stored in unixtime format.
		time_refreshed = weather_data['refresh_time']

		# check if we need a refresh
		to_refresh = check_age(time_refreshed)

		# data is too old, redownload it, timestamp it, and save it.
		if to_refresh:
			printd("- Data too old, request new.")
			new_data = request_data(city)

			if new_data != False:
				weather_data = new_data
				weather_data['refresh_time'] = time.time()
				writeWeatherData(weather_data)

	return(weather_data)

def writeWeatherData(weather_data):
	printd("* Saving new weather data...")
	weather_file = "%s/openweather_%s.json" % (storage, weather_data["id"])


	with open(weather_file, "w") as f:
		json.dump(weather_data, f)
		f.close()

def request_data(city):
	printd("Sending request for %s" % city)
	r = requests.get('http://api.openweathermap.org/data/2.5/weather?id={}&appid={}'.format(city, key))
	status_code = r.status_code
	printd("- Got response code %s" % str(status_code))

	if status_code == 200:
		weather_data = r.json()
		return weather_data
	else:
		printd("! Data refresh failed")
		return False

# opendata gives temperature in Kelvins, this little piggy converts it to degree celsius
def toCelsius(T):
	t = T - 273.15
	return t

# visibility is in meters, convert to kilometers.
def toKilometers(m):
	return m/1000

# determine wind direction
def windDirection(deg):
	# data matix first... format: direction: [min, max]
	wind_data = {
		"N": [348.75, 11.25], "NNE": [11.25, 33.75],
		"NE": [33.75, 56.25], "ENE": [56.25, 78.75],
		"E":[78.75, 101.25], "ESE": [101.25, 123.75],
		"SE":[123.75, 146.25], "SSE": [146.25, 168.75],
		"S":[168.75, 191.25],"SSW": [191.25, 213.75],
		"SW": [213.75, 236.25], "WSW": [236.25, 258.75],
		"W": [258.75, 281.25], "WNW": [281.25, 303.75],
		"NW": [303.75, 326.25], "NNW": [326.25, 348.75]
	}
	# let's say it's unknown
	direction = "Unknown"
	# now, logic...
	for d in wind_data:
		w = wind_data[d]
		if deg >= w[0] and deg <= w[1]:
			printd(d)
			direction = d

	# return
	return direction

def timestamp2String(timestamp, date=True):
	if date:
		time_format = "%H:%M, %d.%m.%Y"
	else:
		time_format = "%H:%M"

	return datetime.datetime.fromtimestamp(int(timestamp)).strftime(time_format)

# here is the main block
to_print = ""
for city in cities:
	# get data...
	weather_data = weather_get(city)

	# grab values we need
	description = weather_data['weather'][0]
	weather = weather_data['main']
	wind = weather_data['wind']
	clouds = weather_data['clouds']
	system = weather_data['sys']

	# rain and snow aren't always available, so, that's solved this way
	rain = []
	if 'rain' in weather_data:
		rain = weather_data['rain']
	snow = []
	if 'snow' in weather_data:
		snow = weather_data['snow']

	# select icon
	icon = icons[description['icon']]

	to_print += "${voffset -12}${color3}${font ConkyColorsWeather:size=20}%s${font}${voffset -18}${goto 35}${color}Weather in${color1} %s, %s ${color}(%s,%s)${color}\n" % (icon, weather_data['name'], system['country'], weather_data['coord']['lat'], weather_data['coord']['lon'])

	to_print += "${voffset 5}${goto 35}${color}Currently: ${color1}%s, %.1f°C ${color}(${color1}%.1f°C ${color}min, ${color1}%.1f°C${color} max)\n" % (description['main'], toCelsius(weather['temp']), toCelsius(weather['temp_min']), toCelsius(weather['temp_max']))

	to_print += "${goto 35}Pressure: ${color1}%.1f mbar${color} / Humidity: ${color1}%.1f%%\n" % (weather['pressure'], weather['humidity'])
	if len(rain) > 0:
		to_print += "${goto 35}Rain accumulation: ${color1} %.1f mm${color}\n" % rain['3h']

	if len(snow) > 0:
		to_print += "${goto 35}Snow fall: ${color1} %.1f mm${color}\n" % snow['3h']

	wind_direction = "N/A"
	if "deg" in wind:
		wind_direction = windDirection(wind['deg'])

	visibility = "N/A"
	if "visibility" in weather_data:
		visibility = str("%.1f km" % toKilometers(weather_data['visibility']))

	to_print += "${goto 35}${color}Visibility: ${color1}%s${color} / Wind: ${color1}%.2f m/s${color}, ${color1}%s\n" % (visibility, wind['speed'], wind_direction)

	to_print += "${goto 35}${color}Cloudiness: ${color1}%d%%${color} / Sunrise: ${color1}%s${color} / Sunset: ${color1}%s\n${color}" % (clouds['all'], timestamp2String(system['sunrise'], False), timestamp2String(system['sunset'], False))

	to_print += "${voffset 3}${goto 35}${alignr 0}${font Fira Sans:size=6}Data from ${color1}%s${color}${font}\n" % timestamp2String(int(weather_data['dt']))

	to_print += "${voffset -5}${goto 35}${alignr 0}${font Fira Sans:size=6}Refreshed at ${color1}%s${color}${font}\n" % timestamp2String(int(weather_data['refresh_time']))

print(to_print)
