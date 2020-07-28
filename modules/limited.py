import datetime
import logging
import typing

import discord
from discord.ext import commands, tasks

import config
import utils

class LimitedRequests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.expiry_check.start()
        self.expiry_check.clear_exception_types()

    def cog_unload(self):
        self.expiry_check.stop()

    @tasks.loop(minutes=10, reconnect=False)
    async def expiry_check(self):
        logging.info('[Limited] Checking for expired requests...')

        expire_before = (datetime.datetime.utcnow() - datetime.timedelta(hours=24)).timestamp() # 24 hours ago

        for server in self.db:
            for message_id, request in server['requests'].items():
                if request['created'] > expire_before: continue
                
                guild = await self.bot.fetch_guild(server['id'])
                await self.request_update(guild, message_id, request, 'expired')
                logging.info(f'[Limited] Expired request {message_id}')


    @expiry_check.before_loop
    async def before_expiry_check(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.member: return
        if payload.member.bot: return

        doc = utils.getGuildDoc(self.bot, payload.member.guild)
        if not doc: return

        request = doc['requests'][str(payload.message_id)]
        if not request: return

        if str(payload.emoji) == config.greenTick:
            await self.request_update(payload.member.guild, payload.message_id, request, 'approved', payload.member)
        elif str(payload.emoji) == config.redTick:
            await self.request_update(payload.member.guild, payload.message_id, request, 'denied', payload.member)
        
        return

    # Create and cancel request methods, called from join/leave commands in core.py
    async def request_create(self, ctx, role):
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)

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
            return await utils.cmdFail(ctx, f'Limited role requests are currently disabled for this guild.', 
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
            title="Limited Role Request",
            description=f'<@{ctx.message.author.id}> requested the <@&{role.id}> role.',
            color = discord.Colour.blurple(),
            timestamp = datetime.datetime.utcnow() + datetime.timedelta(hours=24))
        embed.set_author(name=f'{ctx.message.author} ({ctx.message.author.id})', icon_url=ctx.message.author.avatar_url)
        embed.add_field(name='Status', value='Pending. React to approve or deny the request.')
        embed.set_footer(text='Request expires')

        embed_message = await ctx.guild.get_channel(channel).send(embed=embed)
        await embed_message.add_reaction(config.greenTick)
        await embed_message.add_reaction(config.redTick)

        utils.guildKeySet(ctx.bot, ctx.guild, f'requests.{embed_message.id}', { 
            'channel': embed_message.channel.id,
            'created': datetime.datetime.utcnow().timestamp(),
            'role': role.id, 
            'status': 'pending',
            'user': ctx.author.id, 
        })

        return await utils.cmdSuccess(ctx, f'Your request for "{role.name}" has been submitted.', delete_after = delete)

    async def request_cancel(self, ctx, role):
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)

        requests = list(filter(
            lambda e: e[1]['user'] == ctx.author.id and e[1]['role'] == role.id, doc['requests'].items()))
        request = requests[-1] if requests else (None, None)

        if not request[1] or request[1]['status'] != 'pending':
            return await utils.cmdFail(ctx, f'You do not have a request pending for the role "{role.name}".')

        await self.request_update(ctx.guild, request[0], request[1], 'cancelled')
        return await utils.cmdSuccess(ctx, f'Your request for "{role.name}" has been cancelled.')

    async def request_update(self, guild, message_id, request, status, mod = None):
        statuses = {
            'cancelled': {
                'colour': discord.Colour.darker_grey(),
                'footer': 'Request cancelled',
                'status': 'Cancelled by user.'
            },
            'approved': {
                'colour': discord.Colour.dark_green(),
                'dm': 'been approved.',
                'footer': 'Request approved',
                'status': f'Approved by {mod}.'
            },
            'denied': {
                'colour': discord.Colour.dark_red(),
                'dm': 'been denied.',
                'footer': 'Request denied',
                'status': f'Denied by {mod}.'
            },
            'expired': {
                'colour': discord.Colour.greyple(),
                'dm': 'expired due to lack of moderator response.',
                'footer': 'Request expired',
                'status': f'Request expired due to lack of moderator response.'
            }
        }

        member = guild.get_member(request['user'])
        role = guild.get_role(request['role'])
        layout = statuses[status]

        if status == 'approved': await member.add_roles(role, reason='User role request approved')

        if status == 'expired':
            utils.guildKeyDel(self.bot, guild, f'requests.{message_id}') 
        else:
            utils.guildKeySet(self.bot, guild, f'requests.{message_id}.status', status) 

        if request['status'] == 'pending':
            channel = await self.bot.fetch_channel(request['channel'])

            try:
                embed_message = await channel.fetch_message(message_id)

                embed = embed_message.embeds[0]
                embed.colour = layout['colour']
                embed.timestamp = datetime.datetime.utcnow()
                embed.set_footer(text=layout['footer'])
                embed.remove_field(0)
                embed.add_field(name='Status', value=layout['status'])
                
                await embed_message.edit(embed=embed)
                await embed_message.clear_reactions()
            except:
                pass

            if status != 'cancelled':
                try:
                    await member.send(f'Your request for "{role}" in "{guild}" has {layout["dm"]}')
                except:
                    pass
        return
            
    @commands.group(name='requests', invoke_without_command=True, case_insensitive=True, aliases=['request'])
    @commands.guild_only()
    async def _requests(self, ctx):
        '''
        Manages settings for limited role requests
        
        To make or cancel your own role request, use the 'join' or 'leave' commands.
        '''
        return await ctx.send_help('request')

    @_requests.command(name='disable')
    @commands.has_guild_permissions(manage_guild=True)
    @utils.guild_in_db()
    async def _requests_disable(self, ctx):
        '''Disables requests for the guild'''
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)

        if doc['requests_opts']['channel'] == None:
            return await utils.cmdFail(ctx, f'Requests are already disabled for this guild.')

        utils.guildKeySet(ctx.bot, ctx.guild, f'requests_opts.channel', None)
        return await utils.cmdSuccess(ctx, f'Requests are now disabled for this guild.')

    @_requests.command(name='channel')
    @commands.has_guild_permissions(manage_guild=True)
    @utils.guild_in_db()
    async def _requests_channel(self, ctx, channel: typing.Optional[discord.TextChannel]):
        '''Gets/sets the channel that requests will be posted in'''
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)
        current = doc['requests_opts']['channel']
        msg_prefix = 'The requests channel is'
        
        if not channel:
            if not current:
                return await ctx.send(f'Requests are currently disabled for this guild.')
            return await ctx.send(f'{msg_prefix} currently <#{doc["requests_opts"]["channel"]}>')
            
        if channel.id == current:
            return await utils.cmdFail(ctx, f'{msg_prefix} already {channel}.')
            
        utils.guildKeySet(ctx.bot, ctx.guild, f'requests_opts.channel', channel.id)
        return await utils.cmdSuccess(ctx, f'{msg_prefix} now {channel}.')

    @_requests.command(name='hidejoins', aliases=['hidejoin'])
    @commands.has_guild_permissions(manage_guild=True)
    @utils.guild_in_db()
    async def _requests_hidejoins(self, ctx, setting: typing.Optional[bool]):
        '''Shows/sets automatic deletion of join commands for limited roles'''
        doc = utils.getGuildDoc(ctx.bot, ctx.guild)
        current = doc['requests_opts']['hidejoins']
        msg_prefix = 'Automatic deletion of join commands for limited roles is'

        setting_str = lambda setting: "enabled" if setting else "disabled"

        if setting is None:
            return await ctx.send(f'{msg_prefix} currently **{setting_str(current)}**.')

        if setting == current:
            return await utils.cmdFail(ctx, f'{msg_prefix} already **{setting_str(current)}**.')

        utils.guildKeySet(ctx.bot, ctx.guild, f'requests_opts.hidejoins', setting)
        return await utils.cmdSuccess(ctx, f'{msg_prefix} now **{setting_str(setting)}**.')
            
def setup(bot):
    bot.add_cog(LimitedRequests(bot))
    logging.info('[Extension] Limited module loaded')

def teardown(bot):
    bot.remove_cog('LimitedRequests')
    logging.info('[Extension] Limited module unloaded')