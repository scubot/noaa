from typing import List

import datetime

import discord
from discord.ext import commands

import reactionscroll as rs
from noaa import tides


class NOAAScrollable(rs.Scrollable):
    def preprocess(self, data: tides.PredictionsResult):
        return data

    def refresh(self, data):
        self.processed_data.clear()
        self.embeds.clear()
        self.processed_data = data
        self.create_embeds()

    def create_embeds(self):
        data = self.split_data(self.processed_data)
        for day, items in enumerate(data):
            embed = discord.Embed(
                title=self.title,
                color=self.color,
                description='Date: {}'.format(
                    items[0].time.strftime('%Y-%m-%d')))
            embed.set_footer(
                text='Page {} of {} | Data provided by NOAA'.format(
                    day + 1, len(data)))

            for item in items:
                embed.add_field(name=self.tide_name(item),
                                value=self.tide_value(item))

            self.embeds.append(embed)

    def tide_name(self, entry: tides.PredictionsRow):
        if entry.type == 'L':
            return "Low tide at " + entry.time.strftime("%H:%M")
        elif entry.type == 'H':
            return "High tide at " + entry.time.strftime("%H:%M")

    def tide_value(self, entry: tides.PredictionsRow):
        return "Depth: " + str(entry.value) + "ft"

    @staticmethod
    def split_data(data: List[tides.PredictionsRow]) -> List[List[tides.PredictionsRow]]:
        res = [[]]

        for this, that in zip(data, data[1:]):
            res[-1].append(this)
            if this.time.day != that.time.day:
                res.append([])
        res[-1].append(data[-1])
        return res



class Noaa(commands.Cog):
    name = 'noaa'
    description = 'Provides data from NOAA stations'
    days_advance = 7
    help_text = '`!noaa tide [station_id]` for information about tides up to' + str(days_advance) + ' days in advance.'
    trigger_string = 'noaa'
    module_version = '1.0.0.dev'
    listen_for_reaction = True
    message_returns = []
    scroll = NOAAScrollable(limit=0, title='', color=0x1C6BA0, inline=False, table='')

    def __init__(self, bot):
        self.version = '1.0.0.dev0'
        self.bot = bot

    @commands.command()
    async def tides(self, ctx: commands.context, station: int):
        m_ret = await ctx.send(embed=await self.fetching_placeholder())
        self.scroll.title = "Tidal information for station #" + str(station)
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
            return 0

        self.scroll.refresh(data)
        await m_ret.edit(embed=self.scroll.initial_embed())
        self.message_returns.append([m_ret, 0])
        await m_ret.add_reaction("⏪")
        await m_ret.add_reaction("⏩")

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

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not await self.contains_returns(reaction.message):
            return 0
        pos = await self.find_pos(reaction.message)
        react_text = reaction.emoji
        if type(reaction.emoji) is not str:
            react_text = reaction.emoji.name
        if react_text == "⏩":
            embed = self.scroll.next(current_pos=pos)
            await reaction.message.edit(embed=embed)
            await self.update_pos(reaction.message, 'next')
        if react_text == "⏪":
            embed = self.scroll.previous(current_pos=pos)
            await reaction.message.edit(embed=embed)
            await self.update_pos(reaction.message, 'prev')

def setup(bot):
    bot.add_cog(Noaa(bot))
