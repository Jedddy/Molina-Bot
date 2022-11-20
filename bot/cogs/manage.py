import discord
import asyncio
from discord.ext import commands
from databases.moderation_database import ModerationDB
from utils.helper import embed_blueprint

class Management(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    async def cog_check(self, ctx: commands.Context):
        return ctx.author.guild_permissions.administrator

    @commands.Cog.listener()
    async def on_ready(self):
        self.executor = ModerationDB()
        await self.executor.create_tables()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            embed = embed_blueprint()
            container = await self.executor.rank_roles_and_party_channels() # returns a tuple with two lists
            channels = container[1] # returns [(id,), (id,)] same for container[0]
            for role in container[0]:
                if f"<@&{role[0]}>" in message.content and message.channel.id not in (c[0] for c in channels)\
                    and message.channel.id not in (f.id for f in message.guild.forums):

                    chnls = '\n'.join((f'<#{c[0]}>' for c in channels))
                    embed.description = f"{message.author.mention}, If you want to find players to play with, Please go ahead on one of these channels:\n\
                        {chnls}"

                    await message.channel.send(embed=embed)
                    break
        except AttributeError:
            pass

    @commands.command()
    async def setpartychannels(self, ctx: commands.Context, *, channel_ids: str):
        """Sets party channels. 
        Rank mentions in channels that are not inside the container of text channels would be warned
        """
        
        temp = [] # Temporary container for succesful channel checks so we only add everything if we dont get an error from the for loop
        embed = embed_blueprint()
        for channel in channel_ids.split():
            chan = discord.utils.get(ctx.guild.text_channels, id=int(channel))
            if not chan:
                raise commands.ChannelNotFound(channel)
            temp.append(chan.id)

        for chnls in temp:
            await self.executor.add_party_channel(chnls)
        embed.description = f"**✅ Rank mentions inside these channels will not be warned**"
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()

    @commands.command()
    async def insertrankroles(self, ctx: commands.Context, *, roles: str):
        """Insert rank roles.
        Rank roles mentions that aren't inside party channels will be warned
        """

        parsed = ""
        for item in roles.split():
            if item.startswith("<"):
                parsed += item[3:-1] + " "
            else:
                parsed += item + " "

        temp = [] # Temporary container for succesful channel checks so we only add everything if we dont get an error from the for loop
        embed = embed_blueprint()
        for role_id in parsed.split():
            role = ctx.guild.get_role(int(role_id))
            if not role:
                raise commands.RoleNotFound(role_id)
            temp.append(role.id)
        for role in temp:
            await self.executor.add_rank_role(role)
        embed.description = f"**✅ Added rank roles to database. Rank roles mentioned outsite party channels will be warned**"
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(Management(bot))