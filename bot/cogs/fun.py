import random
from utils.helper import embed_blueprint
from discord.ext.commands import Bot, Cog, Context, command


class Fun(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        super().__init__()

    @command(aliases=["8ball"])
    async def ball(self, ctx: Context, question: str):
        """Makes the bot answer your question"""

        answers = (
            "No", "Yes", "Maybe", "Ask again next time", "You decide"
        )
        embed = embed_blueprint()
        embed.description = f"**{random.choice(answers)}**"
        await ctx.send(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(Fun(bot))
