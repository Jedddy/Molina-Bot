import asyncio
from math import ceil
from datetime import timedelta
from discord import Forbidden, Member, Role, TextChannel, User, utils
from databases.moderation_database import ModerationDB
from utils.helper import parse, send_to_modlog, embed_blueprint
from config.config import update_config, get_config, delete_config
from discord.ext.commands import Bot, Cog, Context, command


class Moderation(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        super().__init__()

    async def cog_check(self, ctx: Context):
        return all((
                ctx.author.guild_permissions.ban_members,
                ctx.author.guild_permissions.kick_members,
                ctx.author.guild_permissions.mute_members,
                ))
        
    @Cog.listener()
    async def on_ready(self):
        self.db = ModerationDB()
        await self.db.create_tables()
    
    @command()
    async def warn(self, ctx: Context, member: Member, *, reason: str = "Not specified"):
        """Warns a member"""

        if member.bot:
            return
        embed = embed_blueprint()
        embed.description = f"**{member} has been warned.** | {reason}"
        embed.set_thumbnail(url=member.avatar.url)
        warn_embed = embed_blueprint()
        warn_embed.description = f"**You have been warned on {ctx.guild.name}**\n\nReason for warn: {reason}"
        await member.send(embed=warn_embed)
        await ctx.send(embed=embed)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", moderation=True)
        await self.db.update_db("warn_count", member.id)
        await self.db.insert_detailed_modlogs(member.id, "Warn", reason=reason, moderator=str(ctx.author))
        
    @command()
    async def mute(self, ctx: Context, member: Member, duration: str = None, *, reason: str = "Not specified"):
        """Mutes a member."""

        time = await parse(duration.rstrip()) if duration else None
        embed = embed_blueprint()
        embed.description = f"**{member} has been muted for {time[1] if duration else '[time not specified]'}.**"
        role = utils.get(ctx.guild.roles, name='Muted')
        await ctx.send(embed=embed)
        await member.add_roles(role)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", reason=reason, moderation=True)
        await self.db.insert_detailed_modlogs(member.id, "Mute", reason=reason, moderator=str(ctx.author))
        await self.db.update_db("mute_count", member.id)
        if duration:
            await asyncio.sleep(time[0])
            await member.remove_roles(role)

    @command()
    async def unmute(self, ctx: Context, member: Member, *, reason: str = "Not specified"):
        """Unmutes a member"""

        role = utils.get(member.roles, name="Muted")
        embed = embed_blueprint()
        if role:
            await member.remove_roles(role)
            embed.description = f"**Unmuted {member}**"  
        else:
            embed.description = f"**{member} is not currently muted**"
            await ctx.send(embed=embed)
            return
        await ctx.send(embed=embed)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", reason=reason, moderation=True)
        await self.db.insert_detailed_modlogs(member.id, "Unmute", reason=reason, moderator=str(ctx.author))

    @command()
    async def ban(self, ctx: Context, member: Member, *, reason: str = "Not specified"):
        """Bans a member."""
        
        embed = embed_blueprint()
        embed.title = f"You have been banned from {ctx.guild.name}"
        embed.description = "You can submit an appeal at:\nhttps://bit.ly/3v4PpKs"
        embed.set_footer(text=f"Reason for ban: {reason}")
        embed.set_thumbnail(url=ctx.guild.icon.url)
        try:
            await member.send(embed=embed)
        except Forbidden:
            pass
        await member.ban()
        embed_ban = embed_blueprint()
        embed_ban.description = f"**{member} has been banned.** | {reason}"
        await ctx.send(embed=embed_ban)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", reason=reason, moderation=True)
        await self.db.update_db("ban_count", member.id)
        await self.db.insert_detailed_modlogs(member.id, "Ban", reason=reason, moderator=str(ctx.author))

    @command()
    async def unban(self, ctx: Context, member_id: int, *, reason: str = "Not specified"):
        """Unbans a member"""

        user = await self.bot.fetch_user(member_id)
        embed = embed_blueprint()
        embed.description = f"**{user} unbanned.** | {reason}"
        await ctx.guild.unban(user)
        await ctx.send(embed=embed)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", reason=reason, moderation=True)
        await self.db.insert_detailed_modlogs(member_id, "Unban", reason=reason, moderator=str(ctx.author))

    @command()
    async def kick(self, ctx: Context, member: Member, *, reason: str = "Not specified"):
        """Kicks a member."""

        embed_kick = embed_blueprint()
        embed_kick.description = f"**{member} has been kicked.** | {reason}"
        embed = embed_blueprint()
        embed.title = f"You have been kicked from {ctx.guild.name}"
        embed.set_footer(text=f"Reason for kick: {reason}")
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await member.send(embed=embed)
        await member.kick(reason=reason)
        await ctx.send(embed=embed_kick)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", reason=reason, moderation=True)
        await self.db.update_db("kick_count", member.id)
        await self.db.insert_detailed_modlogs(member.id, "Kick", reason=reason, moderator=str(ctx.author))

    @command()
    async def lock(self, ctx: Context, channel: TextChannel = None):
        """Locks a channel."""

        embed = embed_blueprint()
        channel = channel or ctx.channel
        locked_channels = await get_config(ctx.guild.id, "lockedChannels")
        if not locked_channels or str(channel.id) not in locked_channels.keys():
            embed.description = "**Channel locked.**"
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await update_config(ctx.guild.id, "lockedChannels", channel.id, inner=True, inner_key=str(channel.id))
            await ctx.send(embed=embed)
            return
        embed.description = f"**Channel {channel.name} already locked.**"
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()

    @command()
    async def unlock(self, ctx: Context, channel: TextChannel = None):
        """Unlocks a locked channel"""

        embed = embed_blueprint()
        channel = channel or ctx.channel
        locked_channels = await get_config(ctx.guild.id, "lockedChannels")
        if str(channel.id) in locked_channels.keys():
            embed.description = "**Channel unlocked.**"
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = True
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await delete_config(ctx.guild.id, "lockedChannels", str(channel.id))
        else:
            embed.description = f"Channel {channel.name} isn't locked!"
        await ctx.send(embed=embed)

    @command()
    async def modlogs(self, ctx: Context, member: User, log_type: str = None, page: int = 1):
        """Views mod logs of a member
        
        Put "-d" as type for detailed logs
        """

        embed = embed_blueprint()
        await self.bot.fetch_user(member.id)
        embed.title = f"**Viewing Mod Logs for {member}**"
        embed.set_thumbnail(url=member.display_avatar.url)
        user_logs = await self.db.view_modlogs(member.id)
        logs, page_max = await self.db.check_detailed_modlogs(member.id, offset=(page - 1)*5) # returns (logs, lenght)
        if log_type == "-d":
            if logs:
                embed.description = f"Page {page}/{ceil(page_max/5)}"
                for log in logs:
                    case_no, user_id, ltype, reason, moderator, date = log # log is a tuple containing the rows on the db
                    embed.add_field(
                        name=f"Case {case_no}",
                        value=f"Type: {ltype}\nModerator: {moderator}\nReason: {reason}\nDate: {date}",
                        inline=False
                    )
                embed.set_footer(text="<prefix>modlogs <member> -d <page>")
            else:
                embed.description = "**No logs yet.**"
        else:
            if user_logs:
                user_logs.pop("profanity_count")
                embed.add_field(
                    name="User ID",
                    value=user_logs.pop("user_id"),
                    inline=False
                    )
                desc = (f"{name[:-6].title()} count: {value}\n" for name, value in user_logs.items())
                embed.description = f"```yaml\n{''.join(desc)}\n```"
            else:
                embed.description = "**No logs yet.**"
        await ctx.send(embed=embed)

    @command()
    async def setmodlog(self, ctx: Context, channel: TextChannel = None):
        """Sets modlog channel"""
        
        channel = channel or ctx.channel
        embed = embed_blueprint()
        embed.description = f"**Mod logs channel set to {channel.name}**"
        await update_config(ctx.guild.id, "modLogChannel", channel.id)
        await ctx.send(embed=embed)

    @command()
    async def setautomodlog(self, ctx: Context, channel: TextChannel = None):
        """Sets modlog channel"""

        channel = channel or ctx.channel
        embed = embed_blueprint()
        embed.description = f"**Automod logs channel set to {channel.name}**"
        await update_config(ctx.guild.id, "autoModLogChannel", channel.id)
        await ctx.send(embed=embed)

    @command()
    async def setbotlog(self, ctx: Context, channel: TextChannel = None):
        """Sets modlog channel"""

        channel = channel or ctx.channel
        embed = embed_blueprint()
        embed.description = f"**Bot logs channel set to {channel.name}**"
        await update_config(ctx.guild.id, "botLogChannel", channel.id)
        await ctx.send(embed=embed)

    @command()
    async def timeout(self, ctx: Context, member: Member, duration: str, *, reason: str = "Not specified"):
        """Time out a member"""

        time = await parse(duration.rstrip()) # Returns a tuple with 2 items. (seconds, formatted_time)
        embed = embed_blueprint()
        embed.description = f"**{member} has been timed out for {time[1]}.** | {reason}"
        await member.timeout(timedelta(seconds=time[0]))
        await ctx.send(embed=embed)
        await self.db.update_db("mute_count", member.id)
        embed.set_thumbnail(url=member.display_avatar)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", reason=reason, moderation=True)
        await self.db.insert_detailed_modlogs(member.id, "Timeout", reason=reason, moderator=str(ctx.author))

    @command()
    async def whitelist(self, ctx: Context, role: Role):
        """Whitelists a role"""

        embed = embed_blueprint()
        if role:
            if not await self.db.in_whilelist(role.id):
                await self.db.insert_whitelist(role.id)
                embed.description = f"**{role.name} added to automod whitelist.**"
                await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", moderation=True)
            else:
                embed.description = f"**{role} may already be whitelisted.**"
        await ctx.send(embed=embed)

    @command()
    async def unwhitelist(self, ctx: Context, role: Role):
        """Removes a role from whitelist"""
        
        embed = embed_blueprint()
        if role:
            if await self.db.in_whilelist(role.id):
                await self.db.remove_whitelist(role.id)
                embed.description = f"**Removed {role} from whitelist.**"
                await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", moderation=True)
            else:
                embed.description = f"**{role} may not be in whitelist.**"
            await ctx.send(embed=embed)

    @command()
    async def seewhitelist(self, ctx: Context):
        """View whitelist in this server"""

        checker = utils.get
        embed = embed_blueprint()
        embed.title = f"Viewing whitelisted roles for {ctx.guild.name}"
        roles = await self.db.view_whitelist()
        if not roles:
            embed.description = "**Nothing to show.**"
            await ctx.send(embed=embed)
            return
        checks = []
        for role in roles:
            if checker(ctx.guild.roles, id=role[0]):
                checks.append(checker(ctx.guild.roles, id=role[0]))
        embed.description = "\n".join((f"{num}. **{r.name}**" for num, r in enumerate(checks, start=1)))
        await ctx.send(embed=embed)
    
    @command()
    async def purge(self, ctx: Context, limit: int):
        """Purges messages on a channel"""

        await ctx.message.delete()
        embed = embed_blueprint()
        await ctx.channel.purge(limit=limit)
        embed.description = f"**Purged {limit} messages**"
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()


async def setup(bot: Bot):
    await bot.add_cog(Moderation(bot))
