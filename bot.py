import datetime
import logging

import discord
from discord.ext import commands
from tinydb import TinyDB

import config

LOG_FORMAT = '[%(asctime)s] [%(levelname)s]: %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

bot = commands.Bot(command_prefix=commands.when_mentioned, case_insensitive=True)
db = TinyDB('db.json')

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.db = db

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info('[Bot] Ready')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            logging.warning(error)
            await ctx.send(f':warning: Command raised an exception. Time occurred: `{datetime.datetime.now()}`')
        else: await ctx.send(f':x: {str(error)}')

bot.add_cog(Core(bot))
bot.load_extension('jishaku')
bot.load_extension('modules.core')
bot.run(config.token)
