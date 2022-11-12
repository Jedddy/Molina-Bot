import discord
from discord.ext import commands
from typing import Mapping, Optional, List, Any

class Help(commands.HelpCommand):
    hidden_cogs = ("ErrorHandler")

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
        desc = \
        f"name: {cmd.name}\ncategory: {cmd.cog_name}\ndescription:\n {cmd.help or cmd.short_doc}\n\n" \
        f"usage: {cmd.name} {cmd.signature}"

        embed = discord.Embed(
            title=f"Command info: {cmd.qualified_name}",
            description = f"```yaml\n---\n{desc}\n---\n```"
            )
        embed.set_footer(text="[optional], <required>, '=' denotes default value")
        await self.get_destination().send(embed=embed)



async def setup(client):
    client._default_help_command = client.help_command
    client.help_command = Help()
