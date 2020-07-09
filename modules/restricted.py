import logging
import typing

import discord
from discord.ext import commands

import utils

class RequestManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    # TODO: Listen for reactions


    # Create and cancel request methods, called from join/leave commands in core.py
    async def request_create(self, ctx, role):
        return await ctx.send('user create request') # TODO

    async def request_cancel(self, ctx, role):
        return await ctx.send('user cancel request') # TODO


    # Approve and deny methods, called from reactions listener
    async def request_approve(self, ctx):
        return await ctx.send('mod approve request') # TODO

    async def request_cancel(self, ctx):
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