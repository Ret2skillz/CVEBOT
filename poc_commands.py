from discord.ext import commands
from pagination import create_poc_embed, paginate_embeds
from db.crud import *

class PoCCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
                        name="searchPOC",
                        help="Search on github for a PoC for a specific CVE (note that it will only find repos with the cve id as their name\n"
                        "Usage: \n"
                        "/searchPOC <cve_id>\n"
                    )
    async def searchPOC(self, ctx, 
                      cve_id: str= commands.parameter(description="The ID of the CVE you want to find a PoC")):
        
        repos = await self.bot.github_api.fetch_poc(cve_id)

        if not repos:
            await ctx.send("No PoC found for this CVE")
            return

        embeds = []
        for poc in repos:
            embed = create_poc_embed(poc)
            embeds.append(embed)

        await paginate_embeds(self.bot, ctx, embeds)

async def setup(bot):
    await bot.add_cog(PoCCommands(bot))