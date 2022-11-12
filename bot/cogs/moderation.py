import asyncio
import logging
import os
import asyncpg
import discord
import re
from datetime import timedelta
from discord.ext import commands
from utils.database import ModerationDB
from utils.helper import parse, filtered_words, embed_blueprint
from config.config import get_config, update_config

user, passw, db = os.getenv("user"), os.getenv("password"), os.getenv("db") 

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = None
        super().__init__()

    async def cog_check(self, ctx: commands.Context):
        return all((
                ctx.author.guild_permissions.ban_members,
                ctx.author.guild_permissions.kick_members,
                ctx.author.guild_permissions.mute_members,
                ))

    async def send_to_modlog(self, guild: discord.Guild, embed: discord.Embed):
        channel = await get_config(str(guild.id), "modLogChannel")
        if not channel:
            return

        sender = discord.utils.get(guild.text_channels, id=channel)
        if not sender:
            return

        await sender.send(embed=embed)
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.db = await asyncpg.create_pool(database=db, user=user, password=passw)
        self.executor = ModerationDB(self.db)
        await self.executor.create_tables()
        self.err_logger = logging.basicConfig(filename="bot/logs/mod_cog.txt", level=logging.ERROR)
        self.filters = filtered_words()
        self.locked_channels = {}
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.bot:
            try:
                checker = any([await self.executor.in_whilelist(role.id) for role in message.author.roles])
                if await self.cog_check(message) or checker:
                    pass
                else:
                    link_check = re.compile(r"(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com\/invite)\/.+[a-z]")
                    if any((link_check.match(msg)) for msg in message.content.split()):
                        await message.delete()
                    if message.author == self.bot.user:
                        return
                    if not await self.executor.check_if_exists("userlogs", "user_id", message.author.id):
                        await self.executor.insert_member(message.author.id)
                    profan_count = await self.executor.profanity_counter(message.author.id)
                    for word in self.filters:
                        if word in message.content.lower():
                            await message.delete()
                            await self.executor.update_db("profanity_count", message.author.id)
                            if profan_count % 10 == 0 and profan_count > 0:
                                await message.channel.send(f"Please avoid using profane words {message.author.mention}. You have been warned.")
                                await self.executor.update_db("warn_count", message.author.id)
                            if profan_count % 20 == 0 and profan_count > 0:
                                role = discord.utils.get(message.guild.roles, name='Muted')
                                await message.author.add_roles(role)
                                await asyncio.sleep(1800)
                                await message.author.remove_roles(role)
            except AttributeError:
                pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user: discord.User):
        embed = embed_blueprint(guild)
        embed.description = "**Member banned**"
        embed.add_field(
            name="Info",
            value=f"```yaml\nuser: {user}```"
        )
        embed.set_thumbnail(url=user.avatar.url)
        await self.send_to_modlog(guild, embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        embed = embed_blueprint(guild)
        embed.description = "**Member unbanned**"
        embed.add_field(
            name="Info",
            value=f"```yaml\nuser: {user}```",
        )
        embed.set_thumbnail(url=user.avatar.url)
        await self.send_to_modlog(guild, embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        embed = embed_blueprint(before.guild)
        embed.description = f"**Message edited in {before.channel.name}**"
        embed.add_field(
            name="Info",
            value=f"```yaml\nbefore: {before.content}\nafter: {after.content}\nauthor: {before.author}```",
        )
        embed.set_thumbnail(url=before.author.avatar.url)
        await self.send_to_modlog(before.guild, embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        embed = embed_blueprint(guild=message.guild)
        embed.description = f"**Message deleted in {message.channel.name}**"
        embed.add_field(
            name="Info",
            value=f"```yaml\nmessage: {message.content}\nauthor: {message.author}```"
        )
        embed.set_thumbnail(url=message.author.avatar.url)
        await self.send_to_modlog(message.guild, embed=embed)

    @commands.command()
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Not specified"):
        """Warns a member"""

        embed = embed_blueprint(guild=ctx.guild)
        embed.description = f"**A member has been warned.**"
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Member", value=member)
        embed.add_field(name="Moderator", value=ctx.author, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        await self.executor.update_db("warn_count", member.id)
        await ctx.send(embed=embed)

    @commands.command()
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: str = None):
        """Mutes a member."""

        time = await parse(duration.rstrip()) if duration else None
        embed = embed_blueprint(guild=ctx.guild)
        embed.description = f"**{member} has been muted for {time[1] if duration else '[time not specified]'}.**"
        role = discord.utils.get(member.guild.roles, name='Muted')
        await ctx.send(embed=embed)
        await self.executor.update_db("mute_count", member.id)
        await member.add_roles(role)
        if duration:
            await asyncio.sleep(time[0])
            await member.remove_roles(role)

    @commands.command()
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        """Unmutes a member"""

        role = discord.utils.get(member.roles, name="Muted")
        embed = embed_blueprint(guild=ctx.guild)
        if role:
            await member.remove_roles(role)
            embed.description = f"**Unmuted {member}**"
        else:
            embed.description = f"**{member} is not currently muted**"
        await ctx.send(embed=embed)

    @commands.command()
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Not specified"):
        """Bans a member."""
        
        embed = embed_blueprint(guild=ctx.guild)
        embed.title = f"You have been banned from {ctx.guild.name}"
        embed.description = "You can submit an appeal at:\nhttps://bit.ly/3v4PpKs"
        embed.set_footer(text=f"Reason for ban: {reason}")
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await member.send(embed=embed)
        await member.ban()
        embed_ban = embed_blueprint(guild=ctx.guild)
        embed_ban.description = f"**{member} has been banned.**"
        await ctx.send(embed=embed_ban)
        await self.executor.update_db("ban_count", member.id)

    @commands.command()
    async def unban(self, ctx: commands.Context, member_id: int):
        """Unbans a member"""

        user = await self.bot.fetch_user(member_id)
        embed = embed_blueprint(guild=ctx.guild)
        embed.description = f"**{user} unbanned.**"
        await ctx.guild.unban(user)
        await ctx.send(embed=embed)

    @commands.command()
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Not specified"):
        """Kicks a member."""

        embed = embed_blueprint(guild=ctx.guild)
        embed.title = f"You have been kicked from {ctx.guild.name}"
        embed.set_footer(text=f"Reason for kick: {reason}")
        await member.send(embed=embed)
        await member.kick(reason=reason)
        embed_kick = embed_blueprint(guild=ctx.guild)
        embed_kick.description = f"**{member} has been kicked.**"
        await ctx.send(embed=embed_kick)
        await self.executor.update_db("kick_count", member.id)

    @commands.command()
    async def lock(self, ctx: commands.Context):
        """Locks a channel."""

        if ctx.channel.id not in self.locked_channels.keys():
            embed = embed_blueprint(guild=ctx.guild)
            embed.description = "**Channel locked.**"
            channel = ctx.channel
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False
            self.locked_channels[ctx.channel.id] = "Locked"
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await ctx.send(embed=embed)

    @commands.command()
    async def unlock(self, ctx: commands.Context):
        """Unlocks a locked channel"""

        if ctx.channel.id in self.locked_channels.keys():
            embed = embed_blueprint(guild=ctx.guild)
            embed.description = "**Channel unlocked.**"
            channel = ctx.channel
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = True
            self.locked_channels.pop(ctx.channel.id)
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await ctx.send(embed=embed)
    
    @commands.command()
    async def modlogs(self, ctx: commands.Context, member: discord.Member):
        """Views mod logs of a member"""

        embed = embed_blueprint(guild=ctx.guild)
        embed.title = f"**Viewing Mod Logs for {member}**"
        embed.set_thumbnail(url=member.avatar.url)
        user_logs = await self.executor.view_modlogs(member.id)
        user_logs.pop("profanity_count")
        embed.add_field(
            name="User ID",
            value=user_logs.pop("user_id"),
            inline=False
            )
        desc = (f"{name[:-6].title()} count: {value}\n" for name, value in user_logs.items())
        embed.description = f"```yaml\n{''.join(desc)}\n```"
        await ctx.send(embed=embed)

    @commands.command
    async def timeout(self, ctx: commands.Context, member: discord.Member, duration: str):
        """Time out a member"""

        time = await parse(duration.rstrip()) # Returns a tuple with 2 items. (seconds, formatted_time)
        embed = embed_blueprint(guild=ctx.guild)
        embed.description = f"**{member} has been timed out for {time[1]}.**"
        await member.timeout(timedelta(seconds=time[0]))
        await ctx.send(embed=embed)
        await self.executor.update_db("mute_count", member.id)

    @commands.command()
    async def whitelist(self, ctx: commands.Context, role: discord.Role):
        """Whitelists a role"""

        embed = embed_blueprint(guild=ctx.guild)
        embed.description = f"{role.name} added to automod whitelist."
        if not await self.executor.in_whilelist(role.id):
            await self.executor.insert_whitelist(role.id)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{role} may already be whitelisted.")

    @commands.command()
    async def setmodlog(self, ctx: commands.Context):
        """Sets modlog channel"""

        embed = embed_blueprint(ctx.guild)
        embed.description = f"**Mod logs channel set to {ctx.channel.name}**"
        await update_config(ctx.guild.id, "modLogChannel", ctx.channel.id)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))