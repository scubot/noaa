# Made by hxtk

import noaa
import re
import requests
from tinydb import TinyDB, Query
from geopy import geocoders
from geopy.extra.rate_limiter import RateLimiter

geolocator = geocoders.Nominatim(user_agent='scubot', timeout=5)
geolocator.geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
station_globe = noaa.StationGlobe.scrape_noaa(geolocator)