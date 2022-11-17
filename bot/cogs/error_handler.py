import asyncio
import logging
from discord.ext import commands
from utils.helper import embed_blueprint


class ErrorHandler(commands.Cog):

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        embed = embed_blueprint(ctx.guild)
        if isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"```Missing argument! -> <{error.param.name}>```"
        elif isinstance(error, commands.MemberNotFound):
            embed.description = f"```Member not found! -> <{error.argument}>```"
        elif isinstance(error, commands.RoleNotFound):
            embed.description = f"```Role not found! -> <{error.argument}>```"
        elif isinstance(error, commands.ChannelNotFound):
            embed.description = f"```Channel not found! -> <{error.argument}>```"
        else:
            embed.description = f"```An error has occured.```"
        error_message = await ctx.send(embed=embed)
        await asyncio.sleep(20)
        await error_message.delete()
        logger = logging.getLogger(__name__)
        logger.error(error)
    

async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))