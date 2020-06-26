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
        return await self._list_helper(ctx, False)

    @_list.command(name='all')
    @commands.has_guild_permissions(manage_roles=True)
    async def _list_all(self, ctx):
        '''Lists all roles in the server'''
        return await self._list_helper(ctx, True)

    async def _list_helper(self, ctx, listAll):
        doc = self.db.get( Servers.id == ctx.guild.id )

        if not listAll: 
            if not ((doc and len(doc['roles']))):
                raise commands.errors.BadArgument(f'This server does not have any requestable roles. (Use list all to list all roles.)')

            roles = list(filter(lambda r: str(r.id) in doc['roles'], ctx.guild.roles)) # Roles in requestable roles
        else: 
            roles = ctx.guild.roles

        roles = list(filter(lambda r: not r.is_default(), reversed(roles))) # Reversed without @everyone role

        # Make list from roles: formatted list of items and raw string of items
        def format_list(*, raw=False):
            def predicate(role):
                if doc and str(role.id) in doc['roles']: 
                    typeName = doc['roles'][str(role.id)]['type'].capitalize()
                    typeStr = f' - {typeName}' if raw else f' *{typeName}*'
                else:
                    typeStr = ''

                if raw:
                    colorStr = '' if role.color == discord.Colour.default() else f' [{role.color}]'
                    return f'{role.name}{ colorStr} ({role.id}){ typeStr}'
                else:
                    return f'<@&{role.id}> (`{role.id}`){ typeStr}'
            return predicate
        
        title = 'All Roles' if listAll else 'Requestable Roles'

        if commands.has_permissions(manage_roles=True)(ctx) and not listAll:
            footer = 'Use the \'list all\' command to list all server roles.' 
        else:
            footer = ''

        lst = list(map(format_list(), roles))
        raw = '\r\n'.join(list(map(format_list(raw=True), roles)))
        
        await utils.sendListEmbed(ctx, title, lst, raw_override=raw, footer=footer)


    @commands.command(name='join')
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def _join(self, ctx, role: discord.Role):
        '''
        Joins or requests a requestable role
        
        If the role is a public role, it will be joined. If the role is a restricted role, a request is submitted.
        '''
        doc = self.db.get( Servers.id == ctx.guild.id )

        if not (doc and str(role.id) in doc['roles']):
            raise commands.errors.BadArgument(f'{role.name} is not a requestable role.') 

        if role in ctx.author.roles:
            raise commands.errors.BadArgument(f'You already have the role {role.name}.') 

        if doc['roles'][str(role.id)]['type'] == 'restricted':
            raise NotImplementedError("role restricted")

        else:
            await ctx.author.add_roles(role)
            return await ctx.send(f':white_check_mark: You have joined the role {role.name}.')

    @commands.command(name='leave')
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def _leave(self, ctx, role: discord.Role):
        '''Leaves or cancels a request for a requestable role'''
        if not self.db.contains(( Servers.id == ctx.guild.id ) & ( Servers.roles[str(role.id)].exists() )):
           raise commands.errors.BadArgument(f'{role.name} is not a requestable role.') 

        if not role in ctx.author.roles:
            raise commands.errors.BadArgument(f'You do not have the role {role.name}.') 

        await ctx.author.remove_roles(role)
        return await ctx.send(f':white_check_mark: You left the role {role.name}.')


    @commands.group(name='roles', invoke_without_command=True, case_insensitive=True, aliases=['role'])
    @commands.guild_only()
    async def _role(self, ctx):
        '''Manages the server's requestable roles'''
        return await ctx.send_help('roles')

    @_role.command(name='add', usage='<role> [public|restricted]')
    @commands.has_guild_permissions(manage_roles=True)
    @utils.guild_in_db()
    async def _role_add(self, ctx, role: discord.Role, roletype: typing.Optional[str] = 'public'):
        '''Adds a role to the requestable roles'''
        types = {
            'public': 'public',
            'restricted': 'restricted',
            'restrict': 'restricted',
            'p': 'public',
            'r': 'restricted'
        }

        if self.db.contains(( Servers.id == ctx.guild.id ) & ( Servers.roles[str(role.id)].exists() )):
           raise commands.errors.BadArgument(f'{role.name} is already a requestable role.') 

        if role.is_default():
            raise commands.errors.BadArgument(f'{role.name} is not a valid role.') 

        if not roletype.lower() in types:
            raise commands.errors.BadArgument(f'{roletype} is not a valid type.') 
        else:
            resolved_type = types[roletype.lower()]

        self.db.update(utils.doc_dd_set(f'roles.{role.id}', { 'type': resolved_type }), Servers.id == ctx.guild.id)
        return await ctx.send(f':white_check_mark: {role.name} added as a requestable {resolved_type} role.')
         

    @_role.command(name='remove')
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_remove(self, ctx, role: discord.Role):
        '''Removes role from the requestable roles'''
        if not self.db.contains(( Servers.id == ctx.guild.id ) & ( Servers.roles[str(role.id)].exists() )):
           raise commands.errors.BadArgument(f'{role.name} is not a requestable role.') 

        self.db.update(utils.doc_dd_del(f'roles.{role.id}'), Servers.id == ctx.guild.id)
        return await ctx.send(f':white_check_mark: {role.name} removed as a requestable role.')

    @_role.command(name='restrict')
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_restict(self, ctx, role: discord.Role):
        '''Makes a public role restricted'''
        return await self._role_update_role(ctx, role, 'restricted')

    @_role.command(name='public', aliases=['unrestrict'])
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_public(self, ctx, role: discord.Role):
        '''Makes a restricted role public'''
        return await self._role_update_role(ctx, role, 'public')

    async def _role_update_role(self, ctx, role: discord.Role, roletype):
        doc = self.db.get( Servers.id == ctx.guild.id )

        if not (doc and str(role.id) in doc['roles']):
           raise commands.errors.BadArgument(f'{role.name} is not a requestable role.') 

        if doc['roles'][str(role.id)]['type'] == roletype:
           raise commands.errors.BadArgument(f'{role.name} is already a {roletype} requestable role.') 

        self.db.update(utils.doc_dd_set(f'roles.{role.id}.type', roletype), Servers.id == ctx.guild.id)
        return await ctx.send(f':white_check_mark: {role.name} is now a {roletype} requestable role.')


def setup(bot):
    bot.add_cog(RoleRequest(bot))
    logging.info('[Extension] Core module loaded')

def teardown(bot):
    bot.remove_cog('RoleRequest')
    logging.info('[Extension] Core module unloaded')