import discord
from discord.ext import commands
from nvd_api import NVDAPI
from github_api import GITHUBAPI
from dotenv import load_dotenv
import os
from db.setup import init_db


class Client(commands.Bot):
    def __init__(self, command_prefix, intents, nvd_api, github_api):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.nvd_api = nvd_api
        self.github_api = github_api

    async def setup_hook(self):
        await self.load_extension("fetch_vulns")
        await self.load_extension("db_commands")
        await self.load_extension("poc_commands")
        await self.load_extension("audit_commands")
        await self.load_extension("kctf_commands")
        await self.tree.sync()

if __name__ == "__main__":
    init_db()

    load_dotenv(override=True)
    token = os.getenv("DISCORD_TOKEN")
    api_key = os.getenv("NVD_API_KEY")
    github_key = os.getenv("GITHUB_TOKEN")

    nvd_api = NVDAPI(api_key)
    github_api = GITHUBAPI(github_key)

    intents = discord.Intents.default()
    intents.message_content = True

    client = Client(command_prefix="/", intents=intents, nvd_api=nvd_api, github_api=github_api)

    
    client.run(token)