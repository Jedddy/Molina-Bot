import asyncio
import logging

from discord.ext.commands import (
    Bot,
    Cog,
    ChannelNotFound,
    CheckFailure,
    CommandNotFound,
    CommandInvokeError,
    Context,
    MissingRequiredArgument,
    MemberNotFound,
    RoleNotFound
)

from utils.helper import embed_blueprint


class ErrorHandler(Cog):
    ignored = (CheckFailure, CommandNotFound, CommandInvokeError)

    @Cog.listener()
    async def on_command_error(self, ctx: Context, error):
        embed = embed_blueprint()
        
        if isinstance(error, MissingRequiredArgument):
            embed.description = f"```Missing argument! -> <{error.param.name}>```"
        elif isinstance(error, MemberNotFound):
            embed.description = f"```Member not found! -> <{error.argument}>```"
        elif isinstance(error, RoleNotFound):
            embed.description = f"```Role not found! -> <{error.argument}>```"
        elif isinstance(error, ChannelNotFound):
            embed.description = f"```Channel not found! -> <{error.argument}>```"
        elif isinstance(error, self.ignored):
            return
        else:
            embed.description = f"```An error has occured.```"

        error_message = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await error_message.delete()
        logger = logging.getLogger(__name__)
        logger.exception(error)


async def setup(bot: Bot):
    await bot.add_cog(ErrorHandler(bot))
