import re
import asyncio
import datetime

from discord import (
    Member,
    Message,
    NotFound,
    RawMemberRemoveEvent,
    utils
)
from discord.ext.commands import Bot, Cog, Context

from utils.helper import filtered_words
from databases.moderation_database import ModerationDB
from utils.helper import embed_blueprint, send_to_modlog, parse
from config.config import get_config


class AutoMod(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = ModerationDB()
        self.filters = filtered_words()
        super().__init__()

    async def cog_check(self, ctx: Context):
        return all((
                ctx.author.guild_permissions.ban_members,
                ctx.author.guild_permissions.kick_members,
                ctx.author.guild_permissions.mute_members,
                ))

    @Cog.listener()
    async def on_ready(self):
        await self.db.create_tables()

    @Cog.listener()
    async def on_message(self, message: Message):
        ctx = await self.bot.get_context(message)

        if message.author.bot:
            return

        if not await self.db.moderation_db_check(message.author.id):
            await self.db.insert_member(message.author.id)

        check = any([await self.db.in_whilelist(role.id) for role in message.author.roles])
        # ^ Checks if user is either admin, or whitelisted
        if await self.cog_check(message) or check:
            return
        else:
            link_check = re.compile(r"(https?:\/\/)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com\/invite)\/.+[a-z]")

            try:
                if any((link_check.match(msg)) for msg in message.content.split()):
                    await message.delete()
                    return
            except NotFound:
                pass

            profan_count = await self.db.profanity_counter(message.author.id)

            for word in self.filters:
                if word in message.content.lower():
                    automod = embed_blueprint()
                    automod.add_field(
                        name="Info",
                        value=f"**Message**: {message.content}\n```yaml\nauthor: {message.author}\nauthor id: {message.author.id}\nmessage id: {message.id}\nword: {word}```"
                    )
                    automod.set_thumbnail(url=message.author.display_avatar)
                    await send_to_modlog(ctx, embed=automod, configtype="autoModLogChannel", reason="Automod")
                    
                    try:
                        await message.delete()
                    except NotFound:
                        pass

                    await self.db.update_db("profanity_count", message.author.id)
                    break

            if profan_count % 10 == 0 and profan_count > 0:
                await message.channel.send(f"Please avoid using profane words {message.author.mention}. You have been warned.")
                await self.db.update_db("warn_count", message.author.id)
                await self.db.insert_detailed_modlogs(message.author.id, "Warn", reason="AutoMod", moderator="None")

            if profan_count % 20 == 0 and profan_count > 0:
                role = utils.get(message.guild.roles, name='Muted')
                embed = embed_blueprint()
                embed.description = f"**{message.author} was muted**"
                await message.author.add_roles(role)
                await send_to_modlog(ctx, embed=embed, configtype="autoModLogChannel", reason="Automod")
                await self.db.insert_detailed_modlogs(message.author.id, "Mute", reason="AutoMod", moderator="None")
                await self.db.update_db("mute_count", message.author.id)
                await asyncio.sleep(1800)
                await message.author.remove_roles(role)

    @Cog.listener()
    async def on_message_edit(self, before: Message, after: Message):
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

    @Cog.listener()
    async def on_message_delete(self, message: Message):
        ctx = await self.bot.get_context(message)

        if message.author.bot:
            return

        embed = embed_blueprint()
        embed.description = f"**Message deleted in {message.channel}**"
        embed.add_field(
            name="Info",
            value=f"**Message**: {message.content}\n```yaml\nauthor: {message.author}\nauthor id: {message.author.id}\nmessage id: {message.id}```"
        )

        if message.attachments:
            image = message.attachments[0].url
            embed.set_image(url=image)

        embed.set_thumbnail(url=message.author.display_avatar)
        await send_to_modlog(ctx, embed=embed, configtype="botLogChannel")

    @Cog.listener()
    async def on_member_join(self, member: Member):
        chnl = await get_config(member.guild.id, "botLogChannel")
        channel = self.bot.get_channel(chnl)

        if not channel:
            return

        embed = embed_blueprint()
        embed.set_thumbnail(url=member.display_avatar)
        embed.description = f"**{member} joined. | {member.id}**"
        account_age = member.created_at.timestamp()
        date_now = datetime.datetime.now()
        t = abs(account_age - date_now.timestamp())
        _, formatted_time = await parse(t)
        embed.add_field(
            name="Account age",
            value=formatted_time
        )
        await channel.send(embed=embed)

    @Cog.listener()
    async def on_raw_member_remove(self, payload: RawMemberRemoveEvent):
        guild = self.bot.get_guild(payload.guild_id)
        chnl = await get_config(guild.id, "botLogChannel")
        channel = self.bot.get_channel(chnl)

        if not channel:
            return

        embed = embed_blueprint()
        embed.set_thumbnail(url=payload.user.display_avatar)
        embed.description = f"**{payload.user} left.** | {payload.user.id}"
        await channel.send(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(AutoMod(bot))
