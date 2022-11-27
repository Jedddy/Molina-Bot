from discord import (
    HTTPException,
    Member,
    PartialEmoji,
    RawReactionActionEvent,
    Role
)
from discord.ext.commands import Bot, Cog, Context, command
from config.config import update_config, get_config
from utils.helper import embed_blueprint

"""TODO: Welcome messages"""

class Welcome(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__()

    async def cog_check(self, ctx: Context):
        return all((
                ctx.author.guild_permissions.ban_members,
                ctx.author.guild_permissions.kick_members,
                ctx.author.guild_permissions.mute_members,
                ))

    @command()
    async def setverification(self, ctx: Context, role: Role, *, text: str):
        """Sets verification channel"""

        embed = embed_blueprint()
        embed.description = "**React here to verify**"
        message = await ctx.send(text, embed=embed)
        await update_config(ctx.guild.id, "verificationChannelID", ctx.channel.id)
        await update_config(ctx.guild.id, "verifiedRoleID", int(role.id))
        await update_config(ctx.guild.id, "verifyMessageID", message.id)
        await message.add_reaction("🇵🇭")
        
    @command()
    async def setwelcome(self, ctx: Context):
        pass


class WelcomeListener(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.server_id = 1031148051760427008 
        self.emoji = PartialEmoji(name='✅')
        super().__init__()

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        """Gives a role based on a reaction emoji."""
        
        self.verification_message_id = await get_config(self.server_id, "verifyMessageID")
        self.role_id = await get_config(self.server_id, "verifiedRoleID")
        if payload.emoji.id != self.emoji.id:
            return

        if not hasattr(self, "verification_message_id") or payload.message_id != self.verification_message_id:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(self.role_id)
        if guild is None or role is None:
            return

        try:
            await payload.member.add_roles(role)
        except HTTPException:
            pass    
    
    @Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        before_role = before.get_role(712536529469440042)
        after_role = after.get_role(712536529469440042)
        if not before_role and after_role:
            channel = await after.guild.fetch_channel(645626756295950349)
            await channel.send(f"Everyone please welcome {after.mention} to our server!")

    @Cog.listener()
    async def on_member_join(self, member):
        pass

async def setup(bot: Bot):
    await bot.add_cog(Welcome(bot))
    await bot.add_cog(WelcomeListener(bot))

