import asyncio
import discord
from math import ceil
from datetime import timedelta
from discord.ext import commands
from databases.moderation_database import ModerationDB
from utils.helper import parse, send_to_modlog, embed_blueprint
from config.config import update_config, get_config, delete_config


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
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
    
    @commands.command()
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Not specified"):
        """Warns a member"""

        if member.bot:
            return
        embed = embed_blueprint(ctx.guild)
        embed.description = f"**{member} has been warned.** | {reason}"
        embed.set_thumbnail(url=member.avatar.url)
        warn_embed = embed_blueprint(ctx.guild)
        warn_embed.description = f"**You have been warned on {ctx.guild.name}**\n\nReason for warn: {reason}"
        await member.send(embed=warn_embed)
        await ctx.send(embed=embed)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", moderation=True)
        await self.executor.update_db("warn_count", member.id)
        await self.executor.insert_detailed_modlogs(member.id, "Warn", reason=reason, moderator=str(ctx.author))
        
    @commands.command()
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: str = None, *, reason: str = "Not specified"):
        """Mutes a member."""

        time = await parse(duration.rstrip()) if duration else None
        embed = embed_blueprint(ctx.guild)
        embed.description = f"**{member} has been muted for {time[1] if duration else '[time not specified]'}.**"
        role = discord.utils.get(ctx.guild.roles, name='Muted')
        await ctx.send(embed=embed)
        await member.add_roles(role)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", reason=reason, moderation=True)
        await self.executor.insert_detailed_modlogs(member.id, "Mute", reason=reason, moderator=str(ctx.author))
        await self.executor.update_db("mute_count", member.id)
        if duration:
            await asyncio.sleep(time[0])
            await member.remove_roles(role)

    @commands.command()
    async def unmute(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Not specified"):
        """Unmutes a member"""

        role = discord.utils.get(member.roles, name="Muted")
        embed = embed_blueprint(ctx.guild)
        if role:
            await member.remove_roles(role)
            embed.description = f"**Unmuted {member}**"  
        else:
            embed.description = f"**{member} is not currently muted**"
            await ctx.send(embed=embed)
            return
        await ctx.send(embed=embed)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", reason=reason, moderation=True)
        await self.executor.insert_detailed_modlogs(member.id, "Unmute", reason=reason, moderator=str(ctx.author))

    @commands.command()
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Not specified"):
        """Bans a member."""
        
        embed = embed_blueprint(ctx.guild)
        embed.title = f"You have been banned from {ctx.guild.name}"
        embed.description = "You can submit an appeal at:\nhttps://bit.ly/3v4PpKs"
        embed.set_footer(text=f"Reason for ban: {reason}")
        embed.set_thumbnail(url=ctx.guild.icon.url)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass
        await member.ban()
        embed_ban = embed_blueprint(ctx.guild)
        embed_ban.description = f"**{member} has been banned.** | {reason}"
        await ctx.send(embed=embed_ban)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", reason=reason, moderation=True)
        await self.executor.update_db("ban_count", member.id)
        await self.executor.insert_detailed_modlogs(member.id, "Ban", reason=reason, moderator=str(ctx.author))

    @commands.command()
    async def unban(self, ctx: commands.Context, member_id: int, *, reason: str = "Not specified"):
        """Unbans a member"""

        user = await self.bot.fetch_user(member_id)
        embed = embed_blueprint(ctx.guild)
        embed.description = f"**{user} unbanned.** | {reason}"
        await ctx.guild.unban(user)
        await ctx.send(embed=embed)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", reason=reason, moderation=True)
        await self.executor.insert_detailed_modlogs(member_id, "Unban", reason=reason, moderator=str(ctx.author))

    @commands.command()
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Not specified"):
        """Kicks a member."""

        embed_kick = embed_blueprint(ctx.guild)
        embed_kick.description = f"**{member} has been kicked.** | {reason}"
        embed = embed_blueprint(ctx.guild)
        embed.title = f"You have been kicked from {ctx.guild.name}"
        embed.set_footer(text=f"Reason for kick: {reason}")
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await member.send(embed=embed)
        await member.kick(reason=reason)
        await ctx.send(embed=embed_kick)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", reason=reason, moderation=True)
        await self.executor.update_db("kick_count", member.id)
        await self.executor.insert_detailed_modlogs(member.id, "Kick", reason=reason, moderator=str(ctx.author))

    @commands.command()
    async def lock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Locks a channel."""

        embed = embed_blueprint(ctx.guild)
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

    @commands.command()
    async def unlock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Unlocks a locked channel"""

        embed = embed_blueprint(ctx.guild)
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

    @commands.command()
    async def modlogs(self, ctx: commands.Context, member: int | discord.Member, log_type: str = None, page: int = 1):
        """Views mod logs of a member
        
        Put "-d" as type for detailed logs
        """

        embed = embed_blueprint(ctx.guild)
        if isinstance(member, int):
            member = await self.bot.fetch_user(member)
        embed.title = f"**Viewing Mod Logs for {member}**"
        embed.set_thumbnail(url=member.avatar.url)
        user_logs = await self.executor.view_modlogs(member.id)
        logs, page_max = await self.executor.check_detailed_modlogs(member.id, offset=(page - 1)*5) # returns (logs, lenght)
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

    @commands.command()
    async def setmodlog(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Sets modlog channel"""
        
        channel = channel or ctx.channel
        embed = embed_blueprint(ctx.guild)
        embed.description = f"**Mod logs channel set to {channel.name}**"
        await update_config(ctx.guild.id, "modLogChannel", channel.id)
        await ctx.send(embed=embed)

    @commands.command()
    async def setautomodlog(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Sets modlog channel"""

        channel = channel or ctx.channel
        embed = embed_blueprint(ctx.guild)
        embed.description = f"**Automod logs channel set to {channel.name}**"
        await update_config(ctx.guild.id, "autoModLogChannel", channel.id)
        await ctx.send(embed=embed)

    @commands.command()
    async def setbotlog(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Sets modlog channel"""

        channel = channel or ctx.channel
        embed = embed_blueprint(ctx.guild)
        embed.description = f"**Bot logs channel set to {channel.name}**"
        await update_config(ctx.guild.id, "botLogChannel", channel.id)
        await ctx.send(embed=embed)

    @commands.command()
    async def timeout(self, ctx: commands.Context, member: discord.Member, duration: str, *, reason: str = "Not specified"):
        """Time out a member"""

        time = await parse(duration.rstrip()) # Returns a tuple with 2 items. (seconds, formatted_time)
        embed = embed_blueprint(ctx.guild)
        embed.description = f"**{member} has been timed out for {time[1]}.**"
        await member.timeout(timedelta(seconds=time[0]))
        await ctx.send(embed=embed)
        await self.executor.update_db("mute_count", member.id)
        embed.set_thumbnail(url=member.display_avatar)
        await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", reason=reason, moderation=True)

    @commands.command()
    async def whitelist(self, ctx: commands.Context, role: discord.Role):
        """Whitelists a role"""

        embed = embed_blueprint(ctx.guild)
        if role:
            if not await self.executor.in_whilelist(role.id):
                await self.executor.insert_whitelist(role.id)
                embed.description = f"**{role.name} added to automod whitelist.**"
                await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", moderation=True)
            else:
                embed.description = f"**{role} may already be whitelisted.**"
        await ctx.send(embed=embed)

    @commands.command()
    async def unwhitelist(self, ctx: commands.Context, role: discord.Role):
        """Removes a role from whitelist"""
        
        embed = embed_blueprint(ctx.guild)
        if role:
            if await self.executor.in_whilelist(role.id):
                await self.executor.remove_whitelist(role.id)
                embed.description = f"**Removed {role} from whitelist.**"
                await send_to_modlog(ctx, embed=embed, configtype="modLogChannel", moderation=True)
            else:
                embed.description = f"**{role} may not be in whitelist.**"
            await ctx.send(embed=embed)

    @commands.command()
    async def seewhitelist(self, ctx: commands.Context):
        """View whitelist in this server"""

        checker = discord.utils.get
        embed = embed_blueprint(ctx.guild)
        embed.title = f"Viewing whitelisted roles for {ctx.guild.name}"
        roles = await self.executor.view_whitelist()
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
    
    @commands.command()
    async def purge(self, ctx: commands.Context, limit: int):
        """Purges messages on a channel"""

        await ctx.message.delete()
        embed = embed_blueprint(ctx.guild)
        await ctx.channel.purge(limit=limit)
        embed.description = f"**Purged {limit} messages**"
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))