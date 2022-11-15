import discord
import asyncpg
import logging
import os
import re
import asyncio
from utils.helper import filtered_words
from databases.database import ModerationDB
from discord.ext import commands
from utils.helper import embed_blueprint, send_to_modlog


class AutoMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    async def cog_check(self, ctx: commands.Context):
        return all((
                ctx.author.guild_permissions.ban_members,
                ctx.author.guild_permissions.kick_members,
                ctx.author.guild_permissions.mute_members,
                ))

    @commands.Cog.listener()
    async def on_ready(self):
        self.executor = ModerationDB()
        await self.executor.create_tables()
        self.err_logger = logging.basicConfig(filename="bot/logs/automod_cog.txt", level=logging.ERROR)
        self.filters = filtered_words()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ctx = await self.bot.get_context(message)
        try:
            if not await self.executor.check_if_exists("userlogs", "user_id", message.author.id):
                await self.executor.insert_member(message.author.id)
            if not message.author.bot:
                # Checks if user is either admin, or whitelisted
                checker = any([await self.executor.in_whilelist(role.id) for role in message.author.roles])
                if await self.cog_check(message) or checker:
                    pass
                else:
                    link_check = re.compile(r"(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com\/invite)\/.+[a-z]")
                    if any((link_check.match(msg)) for msg in message.content.split()):
                        try:
                            await message.delete()
                            return
                        except discord.errors.NotFound:
                            pass
                    profan_count = await self.executor.profanity_counter(message.author.id)
                    for word in self.filters:
                        if word in message.content.lower():
                            try:
                                await message.delete()
                                automod = embed_blueprint(ctx.guild)
                                automod.add_field(
                                    name="Info",
                                    value=f"**Message**: {message.content}\n```yaml\nauthor: {message.author}\nauthor id: {message.author.id}\nmessage id: {message.id}```"
                                )
                                automod.set_thumbnail(url=message.author.display_avatar)
                                await send_to_modlog(ctx, embed=automod, configtype="autoModLogs", reason="Automod")
                            except discord.errors.NotFound:
                                pass
                            await self.executor.update_db("profanity_count", message.author.id)
                            if profan_count % 10 == 0 and profan_count > 0:
                                await message.channel.send(f"Please avoid using profane words {message.author.mention}. You have been warned.")
                                await self.executor.update_db("warn_count", message.author.id)
                            if profan_count % 20 == 0 and profan_count > 0:
                                role = discord.utils.get(message.guild.roles, name='Muted')
                                embed = embed_blueprint(message.guild)
                                embed.description = f"**{message.author} was muted**"
                                await message.author.add_roles(role)
                                await send_to_modlog(ctx, embed=embed, configtype="autoModLogs", reason="Automod")
                                await asyncio.sleep(1800)
                                await message.author.remove_roles(role)
        except AttributeError:
            pass
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user: discord.User):
        ctx = await self.bot.get_context(guild)
        embed = embed_blueprint(guild)
        embed.description = "**Member banned**"
        embed.add_field(
            name="Info",
            value=f"```yaml\nuser: {user}```"
        )
        embed.set_thumbnail(url=user.display_avatar)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        ctx = await self.bot.get_context(guild)
        embed = embed_blueprint(guild)
        embed.description = "**Member unbanned**"
        embed.add_field(
            name="Info",
            value=f"```yaml\nuser: {user}```",
        )
        embed.set_thumbnail(url=user.display_avatar)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        ctx = await self.bot.get_context(before)
        if before.author.bot:
            return
        embed = embed_blueprint(before.guild)
        embed.description = f"**Message edited in {before.channel}**"
        embed.add_field(
            name="Info",
            value=f"**Before**: {before.content}\n**After**: {after.content}\n```yaml\nauthor: {before.author}\nauthor id: {before.author.id}```",
        )
        embed.add_field(
            name="Actual message:",
            value=f"[Jump to message]({after.jump_url})",
            inline=False
        )
        embed.set_thumbnail(url=before.author.display_avatar)
        await send_to_modlog(ctx, embed=embed, configtype="botLogChannel")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        ctx = await self.bot.get_context(message)
        if message.author.bot:
            return
        embed = embed_blueprint(guild=message.guild)
        embed.description = f"**Message deleted in {message.channel}**"
        embed.add_field(
            name="Info",
            value=f"**Message**: {message.content}\n```yaml\nauthor: {message.author}\nauthor id: {message.author.id}\nmessage id: {message.id}```"
        )
        embed.set_thumbnail(url=message.author.display_avatar)
        await send_to_modlog(ctx, embed=embed, configtype="botLogChannel")

    @commands.Cog.listener()
    async def on_raw_member_join(self, member: discord.Member):
        ctx = await self.bot.get_context(member)
        embed = embed_blueprint(ctx.guild)
        embed.set_thumbnail(url=member.display_avatar)
        await send_to_modlog(ctx, embed=embed, configtype="botLogChannel")

    @commands.Cog.listener()
    async def on_raw_member_remove(self, member: discord.Member):
        ctx = await self.bot.get_context(member)
        embed = embed_blueprint(ctx.guild)
        embed.set_thumbnail(url=member.display_avatar)
        await send_to_modlog(ctx, embed=embed, configtype="botLogChannel")


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot))