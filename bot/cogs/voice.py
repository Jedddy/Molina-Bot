from discord import Member, VoiceState
from config.config import get_config
from discord.ext.commands import Bot, Cog
from discord import NotFound


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
        try:
            if not before.channel and after.channel:
                if vc_role not in member.roles:
                    await member.add_roles(vc_role)
            elif before.channel and not after.channel:
                if vc_role in member.roles:
                    await member.remove_roles(vc_role)
        except NotFound:
            pass


async def setup(bot: Bot):
    await bot.add_cog(VoiceListener(bot))
