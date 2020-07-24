import logging
import typing

import discord
from discord.ext import commands

import utils

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
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)

        if commands.has_permissions(manage_roles=True)(ctx) and not listAll:
            footer = f'Use the "{ctx.prefix}list all" command to list all server roles.' 
            errMsgExtra = f'(Use the `{ctx.prefix}list all` command to list all server roles.)'
        else:
            footer = ''
            errMsgExtra = ''

        if not listAll: 
            if not ((doc and len(doc['roles']))):
                return await utils.cmdFail(ctx, f'This server does not have any requestable roles. {errMsgExtra}')

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
        lst = list(map(format_list(), roles))
        raw = '\r\n'.join(list(map(format_list(raw=True), roles)))

        await utils.sendListEmbed(ctx, title, lst, raw_override=raw, footer=footer)

    @commands.command(name='join')
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def _join(self, ctx, role: discord.Role):
        '''
        Joins or requests a requestable role
        
        If the role is a open role, it will be joined. If the role is a limited role, a request is submitted.
        '''
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)

        if not (doc and str(role.id) in doc['roles']):
            return await utils.cmdFail(ctx, f'"{role.name}" is not a requestable role.') 

        if role in ctx.author.roles:
            return await utils.cmdFail(ctx, f'You already have the role "{role.name}".') 

        if doc['roles'][str(role.id)]['type'] == 'limited':
            return await self.bot.get_cog('RequestManager').request_create(ctx, role)

        await ctx.author.add_roles(role, reason='User joined role via command')
        return await utils.cmdSuccess(ctx, f'You have joined the role "{role.name}".')

    @commands.command(name='leave')
    @commands.guild_only()
    @commands.bot_has_guild_permissions(manage_roles=True)
    async def _leave(self, ctx, role: discord.Role):
        '''Leaves or cancels a request for a requestable role'''
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)

        if not (doc and str(role.id) in doc['roles']):
           return await utils.cmdFail(ctx, f'"{role.name}" is not a requestable role.') 

        if not role in ctx.author.roles:
            if doc['roles'][str(role.id)]['type'] == 'limited':
                return await self.bot.get_cog('RequestManager').request_cancel(ctx, role)
            
            return await utils.cmdFail(ctx, f'You do not have the role "{role.name}".') 

        await ctx.author.remove_roles(role, reason='User left role via command')
        return await utils.cmdSuccess(ctx, f'You left the role "{role.name}".')

    @commands.group(name='roles', invoke_without_command=True, case_insensitive=True, aliases=['role'])
    @commands.guild_only()
    async def _role(self, ctx):
        '''Manages the server's requestable roles'''
        return await ctx.send_help('roles')

    @_role.command(name='add', usage='<role> [open|limited]')
    @commands.has_guild_permissions(manage_roles=True)
    @utils.guild_in_db()
    async def _role_add(self, ctx, role: discord.Role, roletype: typing.Optional[str] = 'open'):
        '''Adds a role to the requestable roles'''
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)
        
        types = {
            'open': 'open',
            'limited': 'limited',
            'o': 'openn',
            'l': 'limited'
        }

        if doc and str(role.id) in doc['roles']:
            return await utils.cmdFail(ctx, f'"{role.name}" is already a requestable role.') 

        if role.is_default():
            return await utils.cmdFail(ctx, f'"{role.name}" is not a valid role.') 

        if not roletype.lower() in types:
            return await utils.cmdFail(ctx, f'"{roletype}" is not a valid type.') 
        
        resolved_type = types[roletype.lower()]
        utils.guildKeySet(ctx.bot, ctx.guild, f'roles.{role.id}', { 'type': resolved_type })
        return await utils.cmdSuccess(ctx, f'"{role.name}" added as a requestable {resolved_type} role.')
         
    @_role.command(name='remove')
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_remove(self, ctx, role: discord.Role):
        '''Removes role from the requestable roles'''
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)

        if not (doc and str(role.id) in doc['roles']):
           return await utils.cmdFail(ctx, f'"{role.name}" is not a requestable role.') 

        utils.guildKeyDel(ctx.bot, ctx.guild, f'roles.{role.id}')
        return await utils.cmdSuccess(ctx, f'"{role.name}" removed as a requestable role.')

    @_role.command(name='limit')
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_limit(self, ctx, role: discord.Role):
        '''Makes a open role limited'''
        return await self._role_update_role(ctx, role, 'limited')

    @_role.command(name='open', aliases=['unlimit'])
    @commands.has_guild_permissions(manage_roles=True)
    async def _role_open(self, ctx, role: discord.Role):
        '''Makes a limited role open'''
        return await self._role_update_role(ctx, role, 'open')

    async def _role_update_role(self, ctx, role: discord.Role, roletype):
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)

        if not (doc and str(role.id) in doc['roles']):
           return await utils.cmdFail(ctx, f'"{role.name}" is not a requestable role.') 

        if doc['roles'][str(role.id)]['type'] == roletype:
           return await utils.cmdFail(ctx, f'"{role.name}" is already a {roletype} requestable role.') 

        utils.guildKeySet(ctx.bot, ctx.guild, f'roles.{role.id}.type', roletype)
        return await utils.cmdSuccess(ctx, f'"{role.name}" is now a {roletype} requestable role.')

def setup(bot):
    bot.add_cog(RoleRequest(bot))
    logging.info('[Extension] Core module loaded')

def teardown(bot):
    bot.remove_cog('RoleRequest')
    logging.info('[Extension] Core module unloaded')