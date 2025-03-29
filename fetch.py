import discord
from discord.ext import commands
from nvd_api import NVDAPI
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
api_key = os.getenv("NVD_API_KEY")

nvd_api = NVDAPI(api_key)

daily_cve = nvd_api.fetch_daily_pwn()

print(daily_cve)

cve_search = nvd_api.fetch_pwn("2024-11-20T00:00:00.000", "2025-03-19T23:59:59.999")

print(cve_search)