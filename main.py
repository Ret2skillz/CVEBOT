import discord
from discord.ext import commands
from nvd_api import NVDAPI
from dotenv import load_dotenv
import os
from db.setup import init_db


class Client(commands.Bot):
    def __init__(self, command_prefix, intents, nvd_api):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.nvd_api = nvd_api

    async def on_ready(self):
        await self.load_extension("fetch_vulns")

if __name__ == "__main__":
    init_db()

    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    api_key = os.getenv("NVD_API_KEY")

    nvd_api = NVDAPI(api_key)

    intents = discord.Intents.default()
    intents.message_content = True

    client = Client(command_prefix="/", intents=intents, nvd_api=nvd_api)

    
    client.run(token)