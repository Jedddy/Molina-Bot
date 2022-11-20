import discord
from discord.ext import commands
from config.config import get_config
from datetime import datetime
from humanfriendly import format_timespan


async def parse(time: str | int | float) -> tuple[int, str]:
    """Parses time from string"""
    time_dict = {
        "d": 86400,
        "h": 3600,
        "m": 60,
        "s": 1
    }
    if isinstance(time, str):
        s = 0 # Time in seconds
        temp = ""
        for i in time:
            if i.isdigit():
                temp += i
            elif i.lower() in ["d", "h", "m", "s"]:
                s += time_dict[i] * int(temp)
                temp = ""
    else:
        s = time
    text = format_timespan(s)
    return s, text


def filtered_words() -> list[str]:
    """Returns bad words"""
    
    with open("bot/utils/filters/bdwords.txt", "r") as file:
        file = file.read().split("\n")
    return file


def embed_blueprint() -> discord.Embed:
    """Returns an discord.Embed blueprint that has time, server name and color"""

    _time = datetime.now()
    embed = discord.Embed(color=0xE60283)
    embed.timestamp = _time
    return embed


async def send_to_modlog(ctx: commands.Context, *, embed: discord.Embed, configtype: str, reason: str = None, moderation: bool = False):
    """Sends to corresponding modlog channel"""
    guild = ctx.guild
    channel_id = await get_config(str(guild.id), configtype)
    if not channel_id:
        return

    sender = discord.utils.get(guild.text_channels, id=channel_id)
    if not sender:
        return
    
    if reason:
        embed.add_field(
            name="Reason:",
            value=reason,
            inline=False
        )
    if moderation:
        embed.add_field(
            name="Moderator",
            value=ctx.author
        )
    await sender.send(embed=embed)