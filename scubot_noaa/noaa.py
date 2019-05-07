import discord
import shlex
from tinydb import TinyDB, Query
import datetime
import reactionscroll as rs

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


class NOAA:
    name = 'noaa'

    description = 'Provides data from NOAA stations'

    days_advance = 7

    help_text = '`!noaa tide [station_id]` for information about tides (up to' + str(days_advance) + ' days in advance.'

    trigger_string = 'noaa'

    module_version = '0.1.0'

    listen_for_reaction = True

    message_returns = []

    scroll = NOAAScrollable(limit=0, title='', color=0x1C6BA0, inline=False, table='')

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
                m_ret = await client.send_message(message.channel, embed=await self.fetching_placeholder())
                self.scroll.title = "Tidal information for station #" + msg[2]
                days_advance = datetime.timedelta(days=self.days_advance)
                today = datetime.date.today()
                end_date = today + days_advance
                today = today.isoformat().replace('-', '')
                end_date = end_date.isoformat().replace('-', '')
                url = "https://tidesandcurrents.noaa.gov/api/datagetter?product=predictions" \
                      "&application=NOS.COOPS.TAC.WL&begin_date=" + today + "&end_date=" + end_date + "&datum=MLLW" \
                      "&station=" + msg[2] + "&time_zone=lst_ldt&units=english&interval=hilo&format=json"
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
