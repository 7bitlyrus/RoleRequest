import typing
import logging

import discord
from discord.ext import commands
from tinydb import Query

import utils

Servers = Query()

class RoleRequest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.group(name='list', invoke_without_command=True, case_insensitive=True)
    @commands.guild_only()
    async def _list(self, ctx):
        '''Lists all requestable roles'''
        return await ctx.send('LIST') # TODO

    @_list.command(name='all')
    @commands.has_guild_permissions(manage_roles=True)
    async def _list_all(self, ctx):
        '''Lists all roles in the server'''
        return await ctx.send('LIST ALL') # TODO


    @commands.command(name='join')
    @commands.guild_only()
    async def _join(self, ctx, role: discord.Role):
        '''
        Joins or requests a requestable roles
        
        If the role is a public role, it will be joined. If the role is a restricted role, a request is submitted.
        '''
        return await ctx.send('JOIN') # TODO

    @commands.command(name='leave')
    @commands.guild_only()
    async def _leave(self, ctx, role: discord.Role):
        '''Leaves or cancels a request for a requestable role'''
        return await ctx.send('LEAVE') # TODO


    @commands.group(name='roles', invoke_without_command=True, case_insensitive=True, aliases=['role'])
    @commands.guild_only()
    async def _role(self, ctx):
        '''
        Manages the server's requestable roles
        
        To see a list of roles, use the 'list' command.
        '''
        return await ctx.send_help('roles')

    @_role.command(name='add', usage='<role> [public|restricted]')
    @commands.has_guild_permissions(manage_roles=True)
    @utils.guild_in_db()
    async def _role_add(self, ctx, role: discord.Role, type: typing.Optional[str] = 'public'):
        '''
        Adds a role to the requestable roles
        '''
        Roles = Query()
        types = {
            'public': 'public',
            'restricted': 'restricted',
            'restrict': 'restricted',
            'p': 'public',
            'r': 'restricted'
        }

        if self.db.contains((Servers.id == ctx.guild.id) & (Servers.roles.any(Roles.id == role.id))):
           raise commands.errors.BadArgument(f'{role.name} is already a requestable role.') 

        if not type.lower() in types:
            raise commands.errors.BadArgument(f'{type} is not a valid type.') 
        else:
            resolved_type = types[type.lower()]

        self.db.update(utils.list_append('roles', {'id': role.id, 'type': resolved_type}), Servers.id == ctx.guild.id)
        await ctx.send(f':white_check_mark: {role.name} added as a requestable {resolved_type} role.')
         

    @_role.command(name='remove')
    @commands.has_guild_permissions(manage_roles=True)
    @utils.guild_in_db()
    async def _role_remove(self, ctx, role: discord.Role):
        '''Removes role from the requestable roles'''
        Roles = Query()

        if not self.bot.db.contains((Servers.id == ctx.guild.id) & (Servers.roles.any(Roles.id == role.id))):
           raise commands.errors.BadArgument(f'{role.name} is not a requestable role.') 

        self.db.update(utils.list_remove('roles', lambda x: x['id'] == role.id), Servers.id == ctx.guild.id)
        await ctx.send(f':white_check_mark: {role.name} removed as a requestable role.')

    @_role.command(name='restrict')
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_restict(self, ctx, role: discord.Role):
        '''Makes a public role restricted'''
        await self._role_update_role(ctx, role, 'restricted')

    @_role.command(name='public', aliases=['unrestrict'])
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_public(self, ctx, role: discord.Role):
        '''Makes a restricted role public'''
        await self._role_update_role(ctx, role, 'public')

    async def _role_update_role(self, ctx, role: discord.Role, type):
        Roles = Query()

        if not self.bot.db.contains((Servers.id == ctx.guild.id) & (Servers.roles.any(Roles.id == role.id))):
           raise commands.errors.BadArgument(f'{role.name} is not a requestable role.') 

        if self.bot.db.contains((Servers.id == ctx.guild.id) & Servers.roles.any((Roles.id == role.id) & (Roles.type == type))):
           raise commands.errors.BadArgument(f'{role.name} is already a {type} requestable role.') 

        self.db.update(utils.list_update('roles', lambda x: x['id'] == role.id, {'id': role.id, 'type': type}), Servers.id == ctx.guild.id)
        await ctx.send(f':white_check_mark: {role.name} is now a {type} requestable role.')


def setup(bot):
    bot.add_cog(RoleRequest(bot))
    logging.info('[Extension] Core module loaded')

def teardown(bot):
    bot.remove_cog('RoleRequest')
    logging.info('[Extension] Core module unloaded')