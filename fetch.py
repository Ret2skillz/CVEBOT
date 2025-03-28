import discord
from discord.ext import commands
from nvd_api import NVDAPI

nvdapi = NVDAPI()

#daily_cve = nvdapi.fetch_daily_pwn()

#print(daily_cve)

cve_search = nvdapi.fetch_pwn("2024-11-20T00:00:00.000", "2025-03-19T23:59:59.999")

print(cve_search)