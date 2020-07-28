import logging

import discord
from discord.ext import commands
from tinydb import TinyDB

import config
import datetime
import utils

LOG_FORMAT = '[%(asctime)s] [%(levelname)s]: %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

bot = commands.Bot(command_prefix=commands.when_mentioned_or("::"), case_insensitive=True)
    # allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False)) TODO add in discord.py 1.4 

db = TinyDB('db.json')

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.db = db
        (bot.git_hash, _, _) = utils.getGitInfo()
        bot.start_time = datetime.datetime.utcnow()

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info('[Bot] Ready')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            await utils.cmdFail(ctx, f'Command raised an unexpected exception.')
            raise error
        else:
            await utils.cmdFail(ctx, str(error))

bot.add_cog(Core(bot))
bot.load_extension('jishaku')
bot.load_extension('modules.core')
bot.load_extension('modules.limited')
bot.run(config.token)
# TODO: Add reaction roles module