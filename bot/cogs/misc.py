import discord
import asyncio
from typing import Union, Optional
from discord.ext import commands
from utils.helper import embed_blueprint, parse
from config.config import get_config, update_config, delete_config


class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Mainly for sticky messages

        if message.author.id == self.bot.user.id:
            return
        channel = await get_config(message.guild.id, "stickiedMessages")
        if not channel:
            return
        stickied_message = channel.get(str(message.channel.id), None)
        if not stickied_message:
            return
        if stickied_message[0] != message.channel.id:
            return
        try:
            old_msg = await message.channel.fetch_message(stickied_message[1])
            await old_msg.delete()
            new_msg = await message.channel.send(old_msg.content)
        # Update the sticky config again
            await update_config(message.guild.id, "stickiedMessages", [new_msg.channel.id, new_msg.id], inner=True, inner_key=str(new_msg.channel.id))

        except discord.errors.NotFound:
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Also mainly for stickied messages"""

        if not message.author.bot:
            return

        channel = await get_config(message.guild.id, "stickiedMessages")
        if not channel:
            return
        
        stickied_message = channel.get(str(message.channel.id), None)
        if not stickied_message:
            return

        if message.id == stickied_message[1]:
            await delete_config(message.guild.id, "stickiedMessages", inner_key=str(message.channel.id))

    @commands.has_guild_permissions(administrator=True)
    @commands.command()
    async def stick(self, ctx: commands.Context, *, message: str):
        """Sticks a piece of message on the channel"""

        bot_msg = await ctx.send(message)
        await ctx.message.delete()
        await update_config(ctx.guild.id, "stickiedMessages", [bot_msg.channel.id, bot_msg.id], inner=True, inner_key=str(ctx.channel.id))

    @commands.command()
    async def remindme(self, ctx: commands.Context, time: str, *, reminder: str):
        """Will remind you on dms after your specified time."""
        
        rmdr = ''.join([rm for rm in reminder])
        embed = embed_blueprint(ctx.guild)
        embed.description = f"**Hello!, You told me to remind you about {rmdr}!**\n**See message here:**\n{ctx.message.jump_url}"
        time = await parse(time)
        await ctx.send(f"Got it! Molina will remind you of \"{rmdr}\" in {time[1]}")
        await asyncio.sleep(time[0])
        await ctx.author.send(embed=embed)

    @commands.has_guild_permissions(administrator=True)
    @commands.command()
    async def prefix(self, ctx: commands.Context, pfx: str):
        """Change default commands prefix"""

        embed = embed_blueprint(ctx.guild)
        await update_config(ctx.guild.id, "commandPrefix", pfx)
        embed.description = f"**✅ Set commands prefix to {pfx}**"
        await ctx.send(embed=embed)

    @commands.has_guild_permissions(administrator=True)
    @commands.command()
    async def announce(self, ctx: commands.Context, keyword: Union[discord.TextChannel, str], 
                        variant: Optional[Union[discord.Role, discord.TextChannel]] = None, 
                        channel: Optional[discord.TextChannel] = None, *, message: str):
        """Send an announcement to a specified channel"""

        mention = None
        embed = embed_blueprint(ctx.guild)
        image = ctx.message.attachments
        if image and image[0].content_type[:5] == "image":
            embed.set_image(url=image[0].url)
        if isinstance(keyword, discord.TextChannel):
            ctx = keyword
        elif isinstance(keyword, str):
            if keyword.lower() == "everyone":
                mention = ctx.guild.default_role
                ctx = variant
            elif keyword.lower() == "role":
                mention = variant.mention
                ctx = channel
        embed.description = message
        await ctx.send(mention, embed=embed)
    
    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Sends the bot's latency"""

        embed = embed_blueprint(ctx.guild)
        embed.description = f"**Pong! ✅ {round(self.bot.latency * 1000)}ms**"
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Misc(bot))