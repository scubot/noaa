import re

import discord
from modules.botModule import *
import shlex
from tinydb import TinyDB, Query
import datetime
import asyncio
import requests
import modules.reactionscroll as rs

from geopy import geocoders

STATION_LIST_URL = "https://tidesandcurrents.noaa.gov/stations.html?type=All%20Stations&sort=0"
STATION_LISTING_PATTERN = '\\<a\\ style\\=\\"color\\:\\ \\#015FA9\\;\\"\\ href\\=\\"inventory\\.html\\?id\\=([\\d]+)\\"\\>[\\d]+\\ ([^\\<]+)\\<\\/a\\>'

class Station(object):
    def __init__(self, latitude, longitude, name, id_):
        self.latitude = latitude  # Latitude in decimal form
        self.longitude = longitude  # Longitude in decimal form
        self.name = name  # Human-readable name of the location (e.g., city, state)
        self.id_ = id_  # NOAA identification number of the station

        
class StationGlobe(object):
    def __init__(self, stations, geolocator):
        self.stations = stations  # iterable collection of `Station` objects
        self.geolocator = geolocator  # geopy geolocator
        
    @staticmethod
    def scrape_noaa(geolocator):
        noaa = requests.get(STATION_LIST_URL)
        stations = []
        for match in re.finditer(STATION_LISTING_PATTERN, noaa.text):
            geo = geolocator.geocode(match[1])
            stations.append(Station(geo.latitude, geo.longitude, match[1], match[0]))
        return StationGlobe(stations, geolocator)
    
    def closest_station_coords(self, latitude, longitude):
        """Accepts a latitude and longitude and returns the closest station in the globe."""
        min_distance = float('inf')
        closest_station = None
        for station in self.stations:
            distance = (latitude - station.latitude)**2 + (longitude - station.longitude)**2
            if distance < min_distance:
                min_distance = distance
                closest_station = station
        return station
    
    def closest_station_name(self, location):
        """Accepts a text location and returns the closest station in the globe."""
        geo = geolocator.geocode(location)
        return self.closest_station_coords(geo.latitude, geo.longitude)
            

class NOAAScrollable(rs.Scrollable):
    def preprocess(self, data):  # Ok this actually does nothing
        return data

    def refresh(self, data):
        self.processed_data.clear()
        self.embeds.clear()
        self.processed_data = data
        self.create_embeds()

    def create_embeds(self):
        page_counter = 1
        for y in range(0, len(self.processed_data)):  # Not using an iterable because of the code logic used below
            if y == 0:
                embed = discord.Embed(title=self.title, color=self.color, description='Date: ' +
                                      self.processed_data[y]['t'].strftime("%Y-%m-%d"))
                embed.set_footer(text="Page " + str(page_counter) + " of " + str(NOAA.days_advance) + " | Data "
                                      "provided by the NOAA")
                embed.add_field(name=self.tide_name(self.processed_data[y]),
                                value=self.tide_value(self.processed_data[y]))
            elif self.tide_newday(y):
                page_counter += 1
                embed.add_field(name=self.tide_name(self.processed_data[y]),
                                value=self.tide_value(self.processed_data[y]))
                self.embeds.append(embed)
                del embed
                embed = discord.Embed(title=self.title, color=self.color, description='Date: ' +
                                      self.processed_data[y]['t'].strftime("%Y-%m-%d"))
                embed.set_footer(text="Page " + str(page_counter) + " of " + str(NOAA.days_advance) + " | Data "
                                      "provided by the NOAA")
            else:
                embed.add_field(name=self.tide_name(self.processed_data[y]),
                                value=self.tide_value(self.processed_data[y]))

    def tide_name(self, entry):
        if entry['type'] == 'L':
            return "Low tide at " + entry['t'].strftime("%H:%M")
        elif entry['type'] == 'H':
            return "High tide at " + entry['t'].strftime("%H:%M")

    def tide_value(self, entry):
        return "Depth: " + str(entry['v']) + "ft"

    def tide_newday(self, index):  # This is a safer way to check in case the index overflows
        if self.processed_data[index-1]['t'].day != self.processed_data[index]['t'].day:
            return True
        else:
            return False


class NOAA(BotModule):
    name = 'noaa'

    description = 'Provides data from NOAA stations'

    days_advance = 7

    help_text = '`!noaa tide [station_id]` for information about tides (up to' + str(days_advance) + ' days in advance.'

    trigger_string = 'noaa'

    module_version = '0.1.0'

    listen_for_reaction = True

    message_returns = []

    scroll = NOAAScrollable(limit=0, title='', color=0x1C6BA0, inline=False, table='')
    
    station_globe = StationGlobe.scrape_noaa(geocoders.Nominatim(user_agent='scubot'))

    async def contains_returns(self, message):
        for x in self.message_returns:
            if message.id == x[0].id:
                return True
        return False

    async def find_pos(self, message):
        for x in self.message_returns:
            if message.id == x[0].id:
                return x[1]

    async def update_pos(self, message, ty):
        for x in self.message_returns:
            if message.id == x[0].id:
                if ty == 'next':
                    x[1] += 1
                if ty == 'prev':
                    x[1] -= 1

    async def fetching_placeholder(self):
        embed = discord.Embed(title='🔄 Now fetching data...')
        return embed

    async def api_error(self, obj):
        try:
            x = obj.json()['error']
            return True
        except KeyError:
            return False

    async def parse_command(self, message, client):
        msg = shlex.split(message.content)
        target = Query()
        if len(msg) > 1:
            if msg[1] == 'tide':
                station_id = 0
                coords_match = re.match('^(-?[\d]+.[\d]+),? (-?[\d]+.[\d]+)$', msg[2])
                if re.match('^[\d]+$', msg[2]):
                    station_id = msg[2]
                elif coords_match:
                    station_id = station_globe.closest_station_coords(float(coords_match.group(1)),
                                                                      float(coords_match.group(2))).id_
                else:
                    station_id = station_globe.closest_station_name(msg[2]).id_
                
                m_ret = await client.send_message(message.channel, embed=await self.fetching_placeholder())
                self.scroll.title = "Tidal information for station #" + station_id
                days_advance = datetime.timedelta(days=self.days_advance)
                today = datetime.date.today()
                end_date = today + days_advance
                today = today.isoformat().replace('-', '')
                end_date = end_date.isoformat().replace('-', '')
                url = "https://tidesandcurrents.noaa.gov/api/datagetter?product=predictions" \
                      "&application=NOS.COOPS.TAC.WL&begin_date=" + today + "&end_date=" + end_date + "&datum=MLLW" \
                      "&station=" + station_id + "&time_zone=lst_ldt&units=english&interval=hilo&format=json"
                html = requests.get(url)
                if await self.api_error(html):
                    await client.edit_message(m_ret, embed=discord.Embed(title='That station does not exist or'
                                                                               ' does not provide tidal data.'))
                    return 0
                data = html.json()['predictions']
                for entry in data:  # Converting string into datetime objects
                    entry['t'] = datetime.datetime.strptime(entry['t'], "%Y-%m-%d %H:%M")
                self.scroll.refresh(data)
                await client.edit_message(m_ret, embed=self.scroll.initial_embed())
                self.message_returns.append([m_ret, 0])
                await client.add_reaction(m_ret, "⏪")
                await client.add_reaction(m_ret, "⏩")
            else:
                return 0

    async def on_reaction_add(self, reaction, client, user):
        if not await self.contains_returns(reaction.message):
            return 0
        pos = await self.find_pos(reaction.message)
        react_text = reaction.emoji
        if type(reaction.emoji) is not str:
            react_text = reaction.emoji.name
        if react_text == "⏩":
            embed = self.scroll.next(current_pos=pos)
            await client.edit_message(reaction.message, embed=embed)
            await self.update_pos(reaction.message, 'next')
        if react_text == "⏪":
            embed = self.scroll.previous(current_pos=pos)
            await client.edit_message(reaction.message, embed=embed)
            await self.update_pos(reaction.message, 'prev')
                                   
