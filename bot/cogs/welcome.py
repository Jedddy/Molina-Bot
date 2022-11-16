import discord
import asyncio
from discord.ext import commands
from config.config import update_config, get_config
from utils.helper import embed_blueprint

"""TODO: Welcome messages"""

class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.server_id = 1031148051760427008 
        self.emoji = discord.PartialEmoji(name='✅')
           
    async def on_ready(self):
        pass

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
    async def on_member_join(self, member):
        pass

    @commands.command()
    async def setverification(self, ctx: commands.Context, role_id):
        """Sets verification channel"""

        embed = embed_blueprint(ctx.guild)
        embed.description = "**React here to verify**"
        role = discord.utils.get(ctx.guild.roles, id=int(role_id)) # Check if role exists
        if role:
            message = await ctx.send(embed=embed)
            await update_config(ctx.guild.id, "verificationChannelID", ctx.channel.id)
            await update_config(ctx.guild.id, "verifiedRoleID", int(role_id))
            await update_config(ctx.guild.id, "verifyMessageID", message.id)
            await message.add_reaction("✅")
            return
        message = await ctx.send("Please input a valid role id.")
        await asyncio.sleep(10)
        await message.delete()
        
    @commands.command()
    async def setwelcome(self, ctx: commands.Context):
        pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))