import logging

import discord
from discord.ext import commands
from tinydb import TinyDB

import config
import datetime
import utils

LOG_FORMAT = '[%(asctime)s] [%(levelname)s]: %(message)s'
logging.basicConfig(format = LOG_FORMAT, level = logging.INFO)

if config.prefix:
    prefix = commands.when_mentioned_or(config.prefix)
else:
    prefix = commands.when_mentioned

bot = commands.Bot(command_prefix=prefix, case_insensitive=True, 
    allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False)) 

db = TinyDB('db.json')

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.db = db
        bot.git_hash = utils.getGitInfo(initialize=True)
        bot.start_time = datetime.datetime.utcnow()

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info('[Bot] Ready')

        for guild in bot.db:
            if not bot.get_guild(guild['id']):
                utils.removeGuild(bot, guild['id'])

    @commands.Cog.listener()
    async def on_guild_remove(guild):
        utils.removeGuild(bot, guild.id)

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