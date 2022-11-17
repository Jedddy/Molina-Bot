import discord
from discord.ext import commands

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))