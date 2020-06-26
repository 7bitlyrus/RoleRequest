import logging
import io

import discord
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

# Functions
async def sendListEmbed(ctx, title, lst, *, raw_override=None, footer=None):
    # Overall - 128 - footer - title, description, field values
    footer_len = 0 if not footer else len(footer)
    LEN_LIMITS = (6000 - 128 - len(title) - footer_len, 2048, 1024) 

    lengths = list(map(lambda x: len(x), lst))

    lenOverall = 0
    lastItem = None

    # Start building with description
    description = ''
    for i in range(len(lst)):
        # Description < Overall, so we won't have to worry about hitting it yet; + 1 for newline
        if len(description) + lengths[i] + 1 > LEN_LIMITS[1]: break 

        description += lst[i] + '\n'
        lastItem = i

    lenOverall += len(description)

    # If description is full, start with fields
    fields = []
    for f in range(24): # 24 Fields, reserve last one for maximum length link
        if lastItem + 1 == len(lst): break
        if lenOverall + lengths[lastItem+1] + 1 > LEN_LIMITS[0]: break

        fields.append('')
        for i in range(lastItem+1, len(lst)):
            if lenOverall + len(fields[f]) + lengths[i] + 1 > LEN_LIMITS[0]: break
            if len(fields[f]) + lengths[i] + 1 > LEN_LIMITS[2]: break

            fields[f] += lst[i] + '\n'
            lastItem = i

        lenOverall += len(fields[f])

    # If its still too large, send the 'raw' list as a file.
    if lastItem + 1 < len(lst):
        fields.append(f'Showing {lastItem+1} items.')
        raw = '\r\n'.join(lst) if not raw_override else raw_override
        file = discord.File(fp=io.BytesIO(str.encode(raw)), filename='list.txt')
    else:
        file = None

    # Create the embed object (finally)
    embed = discord.Embed(title=title, description=description)
    if footer: embed.set_footer(text=footer)
    for field in fields:
        embed.add_field(name='\uFEFF', value=field, inline=False) # \uFEFF = ZERO WIDTH NO-BREAK SPACE

    message = await ctx.send(embed=embed, file=file)
    if file: # Update the message embed with the file url
        url = message.attachments[0].url
        newValue = fields[len(fields)-1] + f' [See all {len(lst)}.]({url})'

        embed.remove_field(len(fields)-1)
        embed.add_field(name='\uFEFF', value=newValue, inline=False)

        return await message.edit(embed=embed)
    else:
        return message
