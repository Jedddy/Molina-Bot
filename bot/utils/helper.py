import discord
from datetime import datetime
from humanfriendly import format_timespan


async def parse(time: str) -> tuple[int, str]:
    """Parses time from string"""
    time_dict = {
        "d": 86400,
        "h": 3600,
        "m": 60,
        "s": 1
    }
    s = 0 # Time in seconds
    temp = ""
    for i in time:
        if i.isdigit():
            temp += i
        elif i.lower() in ["d", "h", "m", "s"]:
            s += time_dict[i] * int(temp)
            temp = ""
    
    message = format_timespan(s)
    return s, message


def filtered_words() -> list[str]:
    """Returns bad words"""
    
    with open("bot/utils/filters/bdwords.txt", "r") as file:
        file = file.read().split("\n")
    return file

def embed_blueprint(guild: discord.Guild) -> discord.Embed:
    """Returns an discord.Embed blueprint that has time, server name and color"""

    time = datetime.now()
    time = time.strftime("%B %d, %Y")
    embed = discord.Embed(color=0xE60283)
    embed.set_footer(text=f"{guild.name} | {time}")
    return embed