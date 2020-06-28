import logging
import typing

import discord
from discord.ext import commands

class RequestManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    # Create and cancel request methods, called from join/leave commands in core.py
    async def user_request_create(self, ctx, role):
        return await ctx.send('user create request') # TODO

    async def user_request_cancel(self, ctx, role):
        return await ctx.send('user cancel request') # TODO


    @commands.group(name='request', invoke_without_command=True, case_insensitive=True)
    @commands.guild_only()
    async def _request(self, ctx):
        '''
        Manages restricted role requests
        
        To make or cancel your own role request, use the 'join' or 'leave' commands.
        '''
        return await ctx.send_help('request')

    @_request.command(name='channel')
    @commands.has_guild_permissions(manage_roles=True)
    async def _request_channel(self, ctx, channel: typing.Optional[discord.TextChannel]):
        '''Sets the channel that requests will be posted in'''
        return await ctx.send('REQUEST CHANNEL') # TODO

    @_request.command(name='approve')
    async def _request_approve(self, ctx, id: str):
        '''Approves a restricted role requests'''
        # check if can read channel
        return await ctx.send('REQUEST APPROVE') # TODO

    @_request.command(name='deny')
    async def _request_deny(self, ctx, id: str):
        '''Denies a restricted role requests'''
        # check if can read channel
        return await ctx.send('REQUEST DENY') # TODO

def setup(bot):
    bot.add_cog(RequestManager(bot))
    logging.info('[Extension] Restricted module loaded')

def teardown(bot):
    bot.remove_cog('RequestManager')
    logging.info('[Extension] Restricted module unloaded')