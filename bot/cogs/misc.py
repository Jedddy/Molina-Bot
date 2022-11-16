import discord
import asyncio
import os
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
        await update_config(ctx.guild.id, "stickiedMessages", [bot_msg.channel.id, bot_msg.id], inner=True, inner_key=str(ctx.channel.id))

    # @commands.has_guild_permissions(administrator=True)
    # @commands.command()
    # async def rmstick(self, ctx: commands.Context):
    #     sticky_channel = await get_config(ctx.guild.id, "stickiedMessages")
    #     if not sticky_channel:
    #         await ctx.send("There are currently no stickied messages.")
    #         await asyncio.sleep(5)
    #         await msg.delete()
    #         return

    #     sticky_channel_id = sticky_channel.get(str(ctx.channel.id))
    #     if sticky_channel_id[0] != ctx.channel.id:
    #         msg = await ctx.send("Please go to the same channel with the sticky message.")
    #         await asyncio.sleep(5)
    #         await msg.delete()
    #         return

    #     await delete_config(ctx.guild.id, "stickiedMessages", inner_key=str(ctx.channel.id))
    #     await ctx.message.delete()
    #     msg = await ctx.send("Removed! ✅ You can now safely remove the stickied message.")
    #     await asyncio.sleep(5)
    #     await msg.delete()

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

async def setup(bot: commands.Bot):
    await bot.add_cog(Misc(bot))