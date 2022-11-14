import asyncio
import logging
from discord.ext import commands
from utils.helper import embed_blueprint


class ErrorHandler(commands.Cog):

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = embed_blueprint(ctx.guild)
            embed.description = f"```Missing argument! -> <{error.param.name}>```"
            error_message = await ctx.send(embed=embed)
            await asyncio.sleep(20)
            await error_message.delete()
        if isinstance(error, commands.MemberNotFound):
            embed = embed_blueprint(ctx.guild)
            embed.description = f"```Member not found! -> <{error.argument}>```"
            error_message = await ctx.send(embed=embed)
            await asyncio.sleep(20)
            await error_message.delete()
        else:
            logger = logging.getLogger()
            logger.error(error)
    

async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))