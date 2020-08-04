import logging
import typing

import discord
from discord import version_info
from discord.ext import commands

from consts import *
import utils

class RoleRequest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.group(name='list', invoke_without_command=True, case_insensitive=True)
    @commands.guild_only()
    async def _list(self, ctx):
        '''Lists all requestable roles'''
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)
        has_manage_roles = commands.has_permissions(manage_roles=True)(ctx)

        if not (doc and len(doc['roles'])):
            return await utils.cmdFail(ctx, f'This server does not have any requestable roles.' +
            f' (Use the `{ctx.prefix}list all` command to list all server roles.)' if has_manage_roles else '')

        roles = list(filter(lambda r: str(r.id) in doc['roles'], ctx.guild.roles)) # Roles in requestable roles

        await self._list_send_embed(ctx, 'Requestable Roles', roles,
        footer=f'Use the "{ctx.prefix}list all" command to list all server roles.' if has_manage_roles else None)

    @_list.command(name='all')
    @commands.has_guild_permissions(manage_roles=True)
    async def _list_all(self, ctx):
        '''Lists all roles in the server'''
        await self._list_send_embed(ctx, 'All Roles', ctx.guild.roles)

    async def _list_send_embed(self, ctx, title, roles, *, footer=None):
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)
        roles = list(filter(lambda r: not r.is_default(), reversed(roles))) # Reversed without @everyone role

        role_list = []
        raw_list = []

        for role in roles:
            typeStr = doc['roles'][str(role.id)]['type'].title() if (doc and str(role.id) in doc['roles']) else None
            colorStr = '' if role.color == discord.Colour.default() else f' [{role.color}]'

            role_list.append(f'<@&{role.id}> (`{role.id}`)' + (f' **{typeStr}**' if typeStr else ''))
            raw_list.append(f'{role.name}{colorStr} ({role.id})' + f' {typeStr}' if typeStr else '')

        await utils.sendListEmbed(ctx, title, role_list, raw_override='\r\n'.join(raw_list), footer=footer)

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

    @commands.command(name='role', usage='<role> (add|open|limit(ed)|remove)')
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    @utils.guild_in_db()
    async def _role(self, ctx, role: discord.Role, option: typing.Optional[str]):
        '''Adds, modifies, or removes a requestable role
        
        Adds or removes a role from the server's requestable roles or modifies an existing requestable roles type.'''
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)

        options = {
            'open': ['open', 'o'],
            'limited': ['limited', 'limit', 'l'],

            'remove': ['delete', 'del', 'd', 'remove', 'rem', 'r'],
            'add': ['add', 'a'] # Option resolves to 'open' but only for new roles.
        }

        resolved_option = None
        for key, val in options.items():
            if option in val:
                resolved_option = key

        if option and not resolved_option:
            return await utils.cmdFail(ctx, f'"{option}" is not a valid option.') 

        if role.is_default() or role.managed: # @everyone role or managed
            return await utils.cmdFail(ctx, f'"{role.name}" is not a valid role.')

        role_request_type = None if not (doc and str(role.id) in doc['roles']) else doc['roles'][str(role.id)]['type']

        # Role info
        if resolved_option is None:
            embed = discord.Embed(
                title="Role Info",
                description=f'<@&{role.id}> (`{role.id}`)\n' + 
                f'**Color:** {"None" if role.color == discord.Colour.default() else role.color}\n' + 
                f'**Hoisted:** {"Yes" if role.hoist else "No"}\n' +
                f'**Mentionable:** {"Yes" if role.mentionable else "No"}\n' +
                '**Requestable:** ' + ('No' if not role_request_type else f'Yes, {role_request_type.title()}'),
                color = discord.Embed.Empty if role.color == discord.Colour.default() else role.colour
            )

            if commands.has_permissions(manage_roles=True)(ctx):
                    embed.set_footer(text=f'See "{ctx.prefix}help role" for valid subcommands.')

            return await ctx.send(embed=embed)

        # Remove role
        if resolved_option == "remove":
            if not role_request_type:
                return await utils.cmdFail(ctx, f'"{role.name}" is not a requestable role.') 

            utils.guildKeyDel(ctx.bot, ctx.guild, f'roles.{role.id}')
            return await utils.cmdSuccess(ctx, f'"{role.name}" has been removed as a requestable role.')

        # Modify role type
        if role_request_type:
            if resolved_option == 'add':
                return await utils.cmdFail(ctx, f'"{role.name}" is already a requestable role.') 

            if role_request_type == resolved_option:
                return await utils.cmdFail(ctx, f'"{role.name}" is already a {resolved_option} requestable role.') 

            utils.guildKeySet(ctx.bot, ctx.guild, f'roles.{role.id}.type', resolved_option)
            return await utils.cmdSuccess(ctx, f'"{role.name}" is now a {resolved_option} requestable role.')

        # Add role
        else:
            if resolved_option == 'add': resolved_option = 'open'

            utils.guildKeySet(ctx.bot, ctx.guild, f'roles.{role.id}', { 'type': resolved_option })
            return await utils.cmdSuccess(ctx, f'{role.name}" has been added as a requestable {resolved_option} role.')

    @commands.command(name='about')
    async def _about(self, ctx):
        """Print information about this bot instance"""
        desc = ABOUT_DESCRIPTION

        application = await self.bot.application_info()
        (version_info, fork) = utils.getGitInfo(ref_commit=self.bot.git_hash)

        if not fork:
            desc = f'[Issue Tracker]({ABOUT_ISSUE_TRACKER})\n\n' + desc

        embed = discord.Embed(title=ABOUT_TITLE, url=ABOUT_URL, description=desc, timestamp = self.bot.start_time)
        embed.set_author(name=f'About {self.bot.user}', icon_url=self.bot.user.avatar_url)
        embed.set_footer(text='Up since')
        embed.add_field(name='Instance Owner', value=application.owner if application.owner else '*Unavailable*')
        embed.add_field(name='Version Info', value=version_info if version_info else '*Unavailable*')

        return await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(RoleRequest(bot))
    logging.info('[Extension] Core module loaded')

def teardown(bot):
    bot.remove_cog('RoleRequest')
    logging.info('[Extension] Core module unloaded')