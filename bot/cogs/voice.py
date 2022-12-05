from discord import Member, Role, VoiceState
from utils.helper import embed_blueprint
from config.config import update_config, get_config
from discord.ext.commands import Bot, Cog, Context, command, has_guild_permissions



class Voice(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__()

    @has_guild_permissions(administrator=True)
    @command()
    async def invcrole(self, ctx: Context, role: Role):
        """Adds the in VC role to the CONFIG"""

        embed = embed_blueprint()
        embed.description = f"**Added {role} as `In VC` role**"
        await update_config(ctx.guild.id, "inVCRole", role.id)
        await ctx.send(embed=embed)


class VoiceListener(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__()

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        # For adding `In VC` role to members inside a VC
        vc_role = await get_config(member.guild.id, "inVCRole")
        vc_role = member.guild.get_role(vc_role)
        if not vc_role:
            return
        if not before.channel and after.channel:
            await member.add_roles(vc_role)
        elif before.channel and not after.channel:
            await member.remove_roles(vc_role)
        for channel in member.guild.voice_channels:
            for member in channel.members:
                if vc_role not in member.roles:
                    await member.add_roles(vc_role)

async def setup(bot: Bot):
    await bot.add_cog(Voice(bot))
    await bot.add_cog(VoiceListener(bot))
