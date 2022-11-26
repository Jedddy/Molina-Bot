import discord
from discord.ext import commands
from config.config import update_config, get_config
from utils.helper import embed_blueprint

"""TODO: Welcome messages"""

class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    async def cog_check(self, ctx: commands.Context):
        return all((
                ctx.author.guild_permissions.ban_members,
                ctx.author.guild_permissions.kick_members,
                ctx.author.guild_permissions.mute_members,
                ))

    @commands.command()
    async def setverification(self, ctx: commands.Context, role: discord.Role):
        """Sets verification channel"""

        embed = embed_blueprint()
        embed.description = "**React here to verify**"
        message = await ctx.send(embed=embed)
        await update_config(ctx.guild.id, "verificationChannelID", ctx.channel.id)
        await update_config(ctx.guild.id, "verifiedRoleID", int(role.id))
        await update_config(ctx.guild.id, "verifyMessageID", message.id)
        await message.add_reaction("✅")
        
    @commands.command()
    async def setwelcome(self, ctx: commands.Context):
        pass


class WelcomeListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.server_id = 1031148051760427008 
        self.emoji = discord.PartialEmoji(name='✅')
        super().__init__()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Gives a role based on a reaction emoji."""
        
        self.verification_message_id = await get_config(self.server_id, "verifyMessageID")
        self.role_id = await get_config(self.server_id, "verifiedRoleID")
        if payload.emoji.id != self.emoji.id:
            return

        if not hasattr(self, "verification_message_id") or payload.message_id != self.verification_message_id:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
       
        role = guild.get_role(self.role_id)
        if role is None:
            return
        
        try:
            await payload.member.add_roles(role)
        except discord.HTTPException:
            pass    
    
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        before_role = before.get_role(712536529469440042)
        after_role = after.get_role(712536529469440042)
        if not before_role and after_role:
            channel = await after.guild.fetch_channel(645626756295950349)
            await channel.send(f"Everyone please welcome {after} to our server!")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
    await bot.add_cog(WelcomeListener(bot))
