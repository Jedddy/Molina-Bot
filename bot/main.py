import os
import logging

from discord import Intents, Game, Message
from discord.ext.commands import Bot
import dotenv

from config.config import get_config
from databases.moderation_database import ModerationDB


dotenv.load_dotenv("bot/token.env")
token = os.getenv("token")

intents = Intents.all()
intents.dm_messages = False

class Molina(Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            command_prefix="?",
            intents=intents,
            **kwargs
        )
        self.synced = False
        self.db = ModerationDB()

    async def get_prefix(self, message: Message) -> str:
        guild = message.guild

        if hasattr(guild, "id"):
            pfx = await get_config(guild.id, "commandPrefix")
            return pfx

        return "?"

    async def on_ready(self) -> None:
        await self.wait_until_ready()
        await self.change_presence(activity=Game(name="Mobile Legends: Bang Bang"))
        print(f"{self.user} is ready.")

    async def setup_hook(self) -> None:
        logging.basicConfig(filename="bot/logs/logs.txt", level=logging.ERROR)

        if not self.synced:
            await self.tree.sync()
            self.synced = True

        for cogs in os.listdir("bot/cogs"):
            if cogs.endswith(".py"):
                await self.load_extension(f"cogs.{cogs[:-3]}")

        await self.db.create_tables()


molina = Molina()
molina.run(token)
