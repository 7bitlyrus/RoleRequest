import logging

from discord.ext import commands
from tinydb import Query

Servers = Query()

# Database Operations
def list_append(key, element):
    def transform(doc):
        doc[key].append(element)
    return transform

def list_remove(key, filterFunc):
    def transform(doc):
        doc[key] = list(filter(lambda x: not filterFunc(x), doc[key]))
    return transform

def list_update(key, filterFunc, new): # TODO: Update this to key, filter, subkey, value
    def transform(doc):
        doc[key] = list(map(lambda x: new if filterFunc(x) else x, doc[key]))
    return transform

# Checks
def guild_in_db():
    async def predicate(ctx):
        try:
            db = ctx.bot.db

            if not db.contains(Servers.id == ctx.guild.id):
                default_document = {'id': ctx.guild.id, 'roles': []}

                db.insert(default_document)
                logging.info(f'[Bot] Guild initalized to database: {ctx.guild} ({ctx.guild.id})')
            return True
        except Exception as e:
            logging.warn(e)
            return False
    return commands.check(predicate)
