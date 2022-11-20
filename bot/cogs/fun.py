import discord
import random
from discord.ext import commands
from utils.helper import embed_blueprint


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @commands.command(aliases=["8ball"])
    async def ball(self, ctx: commands.Context, question: str):
        """Makes the bot answer your question"""

        answers = (
            "No", "Yes", "Maybe", "Ask again next time", "You decide"
        )
        embed = embed_blueprint()
        embed.description = f"**{random.choice(answers)}**"
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))