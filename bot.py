import logging
import typing

import discord
from discord.ext import commands

import config

LOG_FORMAT = '[%(asctime)s] [%(levelname)s]: %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

bot = commands.Bot(command_prefix=commands.when_mentioned, case_insensitive=True)

class RoleRequest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.READY = False


    @commands.Cog.listener()
    async def on_ready(self):
        logging.info('[Bot] Ready')
        if not self.READY: self.READY = True

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.send(':x: ' + str(error))


    @commands.group(name='list', invoke_without_command=True, case_insensitive=True)
    @commands.guild_only()
    async def _list(self, ctx):
        '''Lists all requestable roles'''
        return await ctx.send("LIST") # TODO

    @_list.command(name='all')
    @commands.has_guild_permissions(manage_roles=True)
    async def _list_all(self, ctx):
        '''Lists all roles in the server'''
        return await ctx.send("LIST ALL") # TODO

    @_list.command(name='colors', aliases=['color', 'colour', 'colours'])
    async def _list_colors(self, ctx):
        '''Shows an image of requestable colored roles'''
        return await ctx.send("LIST COLORS") # TODO


    @commands.command(name='join')
    @commands.guild_only()
    async def _join(self, ctx, role: discord.Role):
        '''Joins a public role or submits a request for a restricted role'''
        return await ctx.send("JOIN") # TODO

    @commands.command(name='leave')
    @commands.guild_only()
    async def _leave(self, ctx, role: discord.Role):
        '''Leaves or cancels a request for a requestable role'''
        return await ctx.send("LEAVE") # TODO


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
        return await ctx.send("REQUEST CHANNEL") # TODO

    @_request.command(name='approve')
    async def _request_approve(self, ctx, id: str):
        '''Approves a restricted role requests'''
        # check if can read channel
        return await ctx.send("REQUEST APPROVE") # TODO

    @_request.command(name='deny')
    async def _request_deny(self, ctx, id: str):
        '''Denies a restricted role requests'''
        # check if can read channel
        return await ctx.send("REQUEST DENY") # TODO


    @commands.group(name='roles', invoke_without_command=True, case_insensitive=True, aliases=['role'])
    @commands.guild_only()
    async def _role(self, ctx):
        '''
        Manages the server's requestable roles
        
        To see a list of roles, use the 'list' command.
        '''
        return await ctx.send_help('roles')

    @_role.command(name='add')
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_add(self, ctx, id: str, type: typing.Optional[str]):
        '''Adds a role to the requestable roles'''
        return await ctx.send("ROLE ADD") # TODO

    @_role.command(name='remove')
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_remove(self, ctx, id: str):
        '''Removes role to the requestable roles'''
        return await ctx.send("ROLE REMOVE") # TODO

    @_role.command(name='restict')
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_restict(self, ctx, id: str):
        '''Makes a public role restricted'''
        return await ctx.send("ROLE RESTRICT") # TODO

    @_role.command(name='public', aliases=['unrestrict'])
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_public(self, ctx, id: str):
        '''Makes a restricted role public'''
        return await ctx.send("ROLE PUBLIC") # TODO


    # TODO REACTION ROLES

bot.add_cog(RoleRequest(bot))
bot.load_extension('jishaku')
bot.run(config.token)