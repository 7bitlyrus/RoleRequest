import datetime
import logging
import typing

import discord
from discord.ext import commands

import config
import utils

class RequestManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    # TODO: Listen for reactions
    # TODO: Expiry check

    # Create and cancel request methods, called from join/leave commands in core.py
    async def request_create(self, ctx, role):
        doc = utils.getGuildDoc(ctx)

        channel = doc['requests_opts']['channel']
        users_requests = list(filter(lambda e: e['user'] == ctx.author.id, doc['requests'].values()))

        if doc['requests_opts']['hidejoins']:
            try:
                await ctx.message.delete(delay = 5)
            except:
                pass
            delete = 15
        else: 
            delete = None

        if not channel:
            return await utils.cmdFail(ctx, f'Restricted role requests are currently disabled for this guild.', 
                delete_after = delete)

        existing_requests = list(filter(lambda e: e['role'] == role.id, users_requests))

        if existing_requests and existing_requests[-1]['status'] == 'pending':
            return await utils.cmdFail(ctx, f'You already have a request pending for the role "{role.name}".', 
                delete_after = delete)

        # Ratelimit if ratelimit score > 21; score calculated from status of requests in last 24h
        rl_score = 0
        for e in users_requests:
            if(e['status'] == 'denied'): rl_score += 7
            if(e['status'] == 'cancelled'): rl_score += 5
            if(e['status'] == 'pending'): rl_score += 3
        if rl_score > 21:
            return await utils.cmdFail(ctx, 'You have too many recent requests. Please try again later.', 
                delete_after = delete)

        embed = discord.Embed(
            title="Restricted Role Request",
            description=f'<@{ctx.message.author.id}> requested the <@&{role.id}> role.',
            color = discord.Colour.blurple(),
            timestamp = datetime.datetime.utcnow() + datetime.timedelta(hours=24))
        embed.set_author(name=f'{ctx.message.author} ({ctx.message.author.id})', icon_url=ctx.message.author.avatar_url)
        embed.add_field(name='Status', value='Pending. React to approve or deny the request.')
        embed.set_footer(text='Request expires')

        embed_message = await ctx.guild.get_channel(channel).send(embed=embed)
        await embed_message.add_reaction(config.greenTick)
        await embed_message.add_reaction(config.redTick)

        utils.guildKeySet(ctx, f'requests.{ctx.message.id}', { 
            'user': ctx.author.id, 
            'role': role.id, 
            'status': 'pending',
            'embed': (embed_message.channel.id, embed_message.id)
        })
        return await utils.cmdSuccess(ctx, f'Your request for "{role.name}" has been submitted.', delete_after = delete)

    async def request_cancel(self, ctx, role):
        doc = utils.getGuildDoc(ctx)

        requests = list(filter(
            lambda e: e[1]['user'] == ctx.author.id and e[1]['role'] == role.id, doc['requests'].items()))
        key, val = requests[-1] if requests else (None, None)

        if not val or val['status'] != 'pending':
            return await utils.cmdFail(ctx, f'You do not have a request pending for the role "{role.name}".')

        try:
            embed_message = await ctx.guild.get_channel(val['embed'][0]).fetch_message(val['embed'][1])

            embed = embed_message.embeds[0]
            embed.colour = discord.Colour.darker_grey()
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_footer(text='Request cancelled')
            embed.remove_field(0)
            embed.add_field(name='Status', value='Cancelled by user.')
            
            await embed_message.edit(embed=embed)
            await embed_message.clear_reactions()
        except:
            pass
        
        utils.guildKeySet(ctx, f'requests.{key}.status', 'cancelled') 

        return await utils.cmdSuccess(ctx, f'Your request for "{role.name}" has been cancelled.')


    # Approve and deny methods, called from reactions listener
    async def request_approve(self, ctx):
        return await ctx.send('mod approve request') # TODO

    async def request_deny(self, ctx):
        return await ctx.send('mod deny request') # TODO


    @commands.group(name='requests', invoke_without_command=True, case_insensitive=True, aliases=['request'])
    @commands.guild_only()
    async def _requests(self, ctx):
        '''
        Manages settings for restricted role requests
        
        To make or cancel your own role request, use the 'join' or 'leave' commands.
        '''
        return await ctx.send_help('request')

    @_requests.command(name='disable')
    @commands.has_guild_permissions(manage_roles=True)
    @utils.guild_in_db()
    async def _requests_disable(self, ctx):
        '''Disables requests for the guild'''
        doc = utils.getGuildDoc(ctx)

        if doc['requests_opts']['channel'] == None:
            return await utils.cmdFail(ctx, f'Requests are already disabled for this guild.')

        utils.guildKeySet(ctx, f'requests_opts.channel', None)
        return await utils.cmdSuccess(ctx, f'Requests are now disabled for this guild.')

    @_requests.command(name='channel')
    @commands.has_guild_permissions(manage_roles=True)
    @utils.guild_in_db()
    async def _requests_channel(self, ctx, channel: typing.Optional[discord.TextChannel]):
        '''Gets/sets the channel that requests will be posted in'''
        doc = utils.getGuildDoc(ctx)
        current = doc['requests_opts']['channel']
        msg_prefix = 'The requests channel is'
        
        if not channel:
            if not current:
                return await ctx.send(f'Requests are currently disabled for this guild.')
            return await ctx.send(f'{msg_prefix} currently <#{doc["requests_opts"]["channel"]}>')
            
        if channel.id == current:
            return await utils.cmdFail(ctx, f'{msg_prefix} already {channel}.')
            
        utils.guildKeySet(ctx, f'requests_opts.channel', channel.id)
        return await utils.cmdSuccess(ctx, f'{msg_prefix} now {channel}.')

    @_requests.command(name='hidejoins', aliases=['hidejoin'])
    @commands.has_guild_permissions(manage_roles=True)
    @utils.guild_in_db()
    async def _requests_quiet(self, ctx, setting: typing.Optional[bool]):
        '''Shows/sets automatic deletion of join commands for restricted roles'''
        doc = utils.getGuildDoc(ctx)
        current = doc['requests_opts']['hidejoins']
        msg_prefix = 'Automatic deletion of join commands for restricted roles is'

        if setting is None:
            return await ctx.send(f'{msg_prefix} currently **{"enabled" if current else "disabled"}**.')

        if setting == current:
            return await utils.cmdFail(ctx, f'{msg_prefix} already **{"enabled" if current else "disabled"}**.')

        utils.guildKeySet(ctx, f'requests_opts.hidejoins', setting)
        return await utils.cmdSuccess(ctx, f'{msg_prefix} now **{"enabled" if setting else "disabled"}**.')

            
def setup(bot):
    bot.add_cog(RequestManager(bot))
    logging.info('[Extension] Restricted module loaded')

def teardown(bot):
    bot.remove_cog('RequestManager')
    logging.info('[Extension] Restricted module unloaded')