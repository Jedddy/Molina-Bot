import discord
from discord.ext import commands
from config.config import get_config
from typing import Mapping, Optional, List, Any


class Help(commands.HelpCommand):
    hidden_cogs = ("ErrorHandler", "AutoMod", "Levels", "Management")

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]]) -> None:
        embed = discord.Embed(
            title="Molina Help",
            color=0xE60283
        )
        embed.set_thumbnail(url=self.context.guild.icon)
        embed.set_footer(text=self.get_destination().guild.name)
        for cog, cmd in mapping.items():
            if hasattr(cog, "qualified_name") and cog.qualified_name not in self.hidden_cogs:
                embed.add_field(
                    name=cog.qualified_name,
                    value=", ".join([f"`{cm.name}`" for cm in await self.filter_commands(cmd, sort=True)]),
                    inline=False
                    )
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, cmd: commands.Command):
        guild_id = self.get_destination().guild.id
        prefix = await get_config(guild_id, "commandPrefix")
        desc = \
        f"name: {cmd.name}\ncategory: {cmd.cog_name}\ndescription:\n {cmd.help or cmd.short_doc}\n\n" \
        f"usage: {prefix}{cmd.name} {cmd.signature}"

        embed = discord.Embed(
            title=f"Command info: {cmd.qualified_name}",
            description = f"```yaml\n---\n{desc}\n---\n```"
            )
        embed.set_footer(text="[optional], <required>, '=' denotes default value")
        await self.get_destination().send(embed=embed)



async def setup(bot: commands.Bot):
    bot._default_help_command = bot.help_command
    bot.help_command = Help()
