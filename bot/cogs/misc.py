import discord
import asyncio
import os
from discord.ext import commands
from utils.helper import embed_blueprint, parse

user, passw, db = os.getenv("user"), os.getenv("password"), os.getenv("db") 

class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    # @commands.command()
    # async def stick(self, ctx: commands.Context, *, message):
    #     embed = embed_blueprint(ctx.guild)
    #     embed.description = " ".join([msg for msg in message])
    #     await ctx.send(embed=embed)

    @commands.command()
    async def remindme(self, ctx: commands.Context, time: str, *, reminder: str):
        rmdr = ''.join([rm for rm in reminder])
        embed = embed_blueprint(ctx.guild)
        embed.description = f"**Hello!, You told me to remind you about {rmdr}!**\n**See message here:** {ctx.message.jump_url}"
        time = await parse(time)
        await ctx.send(f"Got it! Molina will remind you of \"{rmdr}\" in {time[1]}")
        await asyncio.sleep(time[0])
        await ctx.author.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Misc(bot))