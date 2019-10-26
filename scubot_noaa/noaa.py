"""Scubot module for fetching tide charts from NOAA."""
from typing import List, Mapping

import datetime

import discord
from discord.ext import commands

import reactionscroll as rs
from noaa import tides


def tide_name(entry: tides.PredictionsRow) -> str:
    """Returns the string form of a given tide prediction"""
    if entry.type == 'L':
        return "Low tide at " + entry.time.strftime("%H:%M")
    if entry.type == 'H':
        return "High tide at " + entry.time.strftime("%H:%M")
    return ""

def tide_value(entry: tides.PredictionsRow):
    """Returns the string form of a tide depth."""
    return "Depth: " + str(entry.value) + "ft"

def split_data(data: List[tides.PredictionsRow]) -> List[List[tides.PredictionsRow]]:
    """Groups a list of tide predictions into rows of tide predictions.

    Args:
        data: A list of tides.PredictionsRow tuples sorted in ascending order by date.

    Returns:
        A list of lists of tides.PredictionsRow tuples such that there is one inner list
        for each day found in the input data and the tides.PredictionRow elements within
        are exactly those occuring on the corresponding day.
    """
    res = [[]]
    for this, that in zip(data, data[1:]):
        res[-1].append(this)
        if this.time.day != that.time.day:
            res.append([])
    res[-1].append(data[-1])
    return res


def make_map(tides: List[tides.PredictionsRow]) -> Mapping[Any, Any]:
    """Converts a list of tide predictions into a map of tide names to tide values.

    Args:
        tides: List of tide predictions data

    Returns:
        dict of tide_name to tide_value for each tide in the list.
    """
    res = dict(zip(map(tide_name, tides), map(tide_value, tides)))


class Noaa(commands.Cog):
    """Noaa defines the bot cog for the tide chart.

    Args:
        bot: a discord.py bot instance
    """
    name = 'noaa'
    description = 'Provides data from NOAA stations'
    days_advance = 7
    help_text = '`!noaa tide [station_id]` for information about tides up to' + \
        str(days_advance) + ' days in advance.'
    trigger_string = 'noaa'
    module_version = '1.0.0.dev'
    listen_for_reaction = True
    message_returns = []

    def __init__(self, bot: commands.Bot, scroll_builder: rs.ScrollViewBuilder):
        self.version = '1.0.0.dev0'
        self.bot = bot
        self.scroll_builder = scroll_builder

    @commands.command()
    async def tides(self, ctx: commands.context, station: int):
        """Command endpoint for tidechart module.

        This signature implements a commands.command.

        When called, a NoaaScrollable is sent in the channel given by
        the context parameter.

        Args:
            ctx: context of the message that invoked the command.
            station: the ID of the station to be queried.
        """
        m_ret = await ctx.send(embed=discord.Embed(title='🔄 Now fetching data...'))
        try:
            data = tides.NoaaRequest() \
                .station(station) \
                .product(tides.Product.PREDICTIONS) \
                .datum(tides.Datum.MEAN_LOWER_LOW_WATER) \
                .timezone(tides.TimeZone.LOCAL_DST) \
                .begin_date(datetime.datetime.today()) \
                .range(24 * self.days_advance) \
                .interval(tides.Interval.HILO) \
                .units(tides.Unit.ENGLISH) \
                .execute()
        except tides.ApiError as error:
            await m_ret.edit(embed=discord.Embed(title=str(error)))
            return

        title = "Tidal information for station #" + str(station)
        await self.scroll_builder.create_on_message(
            m_ret,
            map(make_map, split_data(data)),
            title=title,
            key_str=tide_name,
            value_str=tide_value)


def setup(bot: commands.Bot):
    """Creates an instance of the cog and adds it to the given bot."""
    scroll_builder = rs.ScrollViewBuilder(title='', color=0x1C6BA0, inline=False, bot=bot)
    bot.add_cog(Noaa(bot, scroll_builder))
