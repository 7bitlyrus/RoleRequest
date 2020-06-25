import logging

from discord.ext import commands
from tinydb import Query
import dict_deep

Servers = Query()

# Database Operations
def doc_dd_set(key, val):
    def transform(doc):
        dict_deep.deep_set(doc, key, val)
    return transform

def doc_dd_del(key):
    def transform(doc):
        dict_deep.deep_del(doc, key)
    return transform

# Checks
def guild_in_db():
    async def predicate(ctx):
        try:
            db = ctx.bot.db

            if not db.contains(Servers.id == ctx.guild.id):
                default_document = {'id': ctx.guild.id, 'roles': {}}

                db.insert(default_document)
                logging.info(f'[Bot] Guild initalized to database: {ctx.guild} ({ctx.guild.id})')
            return True
        except Exception as e:
            logging.warn(e)
            return False
    return commands.check(predicate)
