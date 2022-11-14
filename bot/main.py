import os
import discord
import dotenv
from config.config import get_config
from discord.ext import commands

dotenv.load_dotenv("bot/token.env")
token = os.getenv("token")

class Molina(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            command_prefix="?", 
            intents=discord.Intents.all(),
            **kwargs
            )
        self.synced = False

    async def get_prefix(self, message: discord.Message) -> str:
        pfx = await get_config(message.guild.id, "commandPrefix")
        return pfx or "?"

    async def on_ready(self) -> None:
        await self.wait_until_ready()
        await self.change_presence(activity=discord.Game(name="Mobile Legends: Bang Bang"))
        print(f"{self.user} is ready.")
        
    async def setup_hook(self) -> None:
        # Load cogs
        if not self.synced:
            await self.tree.sync()
            self.synced = True
            
        for cogs in os.listdir("bot/cogs"):
            if cogs.endswith(".py"):
                await self.load_extension(f"cogs.{cogs[:-3]}")

molina = Molina(application_id='1040074864763088978')
molina.run(token)