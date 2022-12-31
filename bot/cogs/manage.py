import asyncio
from discord import Message, MessageType, utils
from discord.ext.commands import (
    Bot,
    Cog,
    Context,
    ChannelNotFound,
    RoleNotFound,
    command
    )
from databases.moderation_database import ModerationDB
from utils.helper import embed_blueprint
from config.config import get_config

class Management(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.db = ModerationDB()
        super().__init__()

    async def cog_check(self, ctx: Context):
        return ctx.author.guild_permissions.administrator

    @Cog.listener()
    async def on_message(self, message: Message):

        if message.author.guild_permissions.manage_channels:
            return

        if message.type == MessageType.premium_guild_subscription:
            channl = await get_config(message.guild.id, "boostChannel")
            if not channl:
                return
            else:
                channel = message.guild.get_channel(channl)
                await channel.send(f"Thank you for boosting the server! {message.author.mention}\nPlease check your perks below:")
        try:
            embed = embed_blueprint()
            container = await self.db.rank_roles_and_party_channels() # returns a tuple with two lists
            channels = container[1] # returns [(id,), (id,)] same for container[0]
            for role in container[0]:
                if f"<@&{role[0]}>" in message.content and message.channel.id not in (c[0] for c in channels)\
                    and message.channel.id not in (f.id for f in message.guild.forums):

                    chnls = '\n'.join((f'<#{c[0]}>' for c in channels))
                    embed.description = f"If you want to find players to play with, Please go ahead on one of these channels:\n{chnls}"

                    await message.channel.send(message.author.mention, embed=embed)
                    break
        except AttributeError:
            pass

    @command()
    async def setpartychannels(self, ctx: Context, *, channel_ids: str):
        """Sets party channels. 
        Rank mentions in channels that are not inside the container of text channels would be warned
        """
        
        temp = [] # Temporary container for succesful channel checks so we only add everything if we dont get an error from the for loop
        embed = embed_blueprint()
        for channel in channel_ids.split():
            chan = utils.get(ctx.guild.text_channels, id=int(channel))
            if not chan:
                raise ChannelNotFound(channel)
            temp.append(chan.id)

        for chnls in temp:
            await self.db.add_party_channel(chnls)
        embed.description = f"**✅ Rank mentions inside these channels will not be warned**"
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()

    @command()
    async def insertrankroles(self, ctx: Context, *, roles: str):
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
                raise RoleNotFound(role_id)
            temp.append(role.id)
        for role in temp:
            await self.db.add_rank_role(role)
        embed.description = f"**✅ Added rank roles to database. Rank roles mentioned outsite party channels will be warned**"
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()


async def setup(bot: Bot):
    await bot.add_cog(Management(bot))
