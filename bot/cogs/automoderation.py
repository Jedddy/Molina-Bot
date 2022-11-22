import discord
import re
import asyncio
import datetime
from utils.helper import filtered_words
from databases.moderation_database import ModerationDB
from discord.ext import commands
from utils.helper import embed_blueprint, send_to_modlog, parse
from config.config import get_config


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
        self.db = ModerationDB()
        await self.db.create_tables()
        self.filters = filtered_words()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ctx = await self.bot.get_context(message)
        try:
            if not await self.db.moderation_db_check(message.author.id):
                await self.db.insert_member(message.author.id)
            if not message.author.bot:
                # Checks if user is either admin, or whitelisted
                checker = any([await self.db.in_whilelist(role.id) for role in message.author.roles])
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
                    profan_count = await self.db.profanity_counter(message.author.id)
                    for word in self.filters:
                        if word in message.content.lower():
                            await message.delete()
                            automod = embed_blueprint()
                            automod.add_field(
                                name="Info",
                                value=f"**Message**: {message.content}\n```yaml\nauthor: {message.author}\nauthor id: {message.author.id}\nmessage id: {message.id}```"
                            )
                            automod.set_thumbnail(url=message.author.display_avatar)
                            await send_to_modlog(ctx, embed=automod, configtype="autoModLogs", reason="Automod")
                            await self.db.update_db("profanity_count", message.author.id)
                            if profan_count % 10 == 0 and profan_count > 0:
                                await message.channel.send(f"Please avoid using profane words {message.author.mention}. You have been warned.")
                                await self.db.update_db("warn_count", message.author.id)
                                await self.db.insert_detailed_modlogs(message.author.id, "Warn", reason="AutoMod", moderator="None")
                            if profan_count % 20 == 0 and profan_count > 0:
                                role = discord.utils.get(message.guild.roles, name='Muted')
                                embed = embed_blueprint()
                                embed.description = f"**{message.author} was muted**"
                                await message.author.add_roles(role)
                                await send_to_modlog(ctx, embed=embed, configtype="autoModLogs", reason="Automod")
                                await self.db.insert_detailed_modlogs(message.author.id, "Mute", reason="AutoMod", moderator="None")
                                await asyncio.sleep(1800)
                                await message.author.remove_roles(role)
        except (AttributeError, discord.errors.NotFound) as e:
            pass
    
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        ctx = await self.bot.get_context(before)
        if before.author.bot:
            return
        embed = embed_blueprint()
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
        embed = embed_blueprint()
        embed.description = f"**Message deleted in {message.channel}**"
        embed.add_field(
            name="Info",
            value=f"**Message**: {message.content}\n```yaml\nauthor: {message.author}\nauthor id: {message.author.id}\nmessage id: {message.id}```"
        )
        embed.set_thumbnail(url=message.author.display_avatar)
        await send_to_modlog(ctx, embed=embed, configtype="botLogChannel")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        chnl = await get_config(member.guild.id, "botLogChannel")
        chnl = self.bot.get_channel(chnl)
        if not chnl:
            return
        embed = embed_blueprint()
        embed.set_thumbnail(url=member.display_avatar)
        embed.description = f"**{member} joined. | {member.id}**"
        account_age = member.created_at.timestamp()
        date_now = datetime.datetime.now()
        t = abs(account_age - date_now.timestamp())
        formatted_time = await parse(t)
        embed.add_field(
            name="Account age",
            value=formatted_time[1]
        )
        await chnl.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent):
        guild = self.bot.get_guild(payload.guild_id)
        chnl = await get_config(guild.id, "botLogChannel")
        if not chnl:
            return
        chnl = self.bot.get_channel(chnl)
        embed = embed_blueprint()
        embed.set_thumbnail(url=payload.user.display_avatar)
        embed.description = f"**{payload.user} left. | {payload.user.id}**"
        await chnl.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot))