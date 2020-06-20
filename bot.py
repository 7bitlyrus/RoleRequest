import logging

import discord
from discord.ext import commands

import config

LOG_FORMAT = '[%(asctime)s] [%(levelname)s]: %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

bot = commands.Bot(command_prefix=commands.when_mentioned, case_insensitive=True)

bot.load_extension('jishaku')
bot.run(config.token)