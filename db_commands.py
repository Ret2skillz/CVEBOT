from discord.ext import commands
from pagination import create_vuln_embed, paginate_embeds
from db.crud import *

class DbCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
                        name="saveCVE",
                        help="Save any Cve you want based on its id\n"
                        "Usage: \n"
                        "/saveCve <cve_id> \n"
                    )
    async def saveCVE(self, ctx, 
                      cve_id: str= commands.parameter(description="The ID of the CVE you want to save")):
        
        vuln = await self.bot.nvd_api.fetch_by_id(cve_id)

        description = vuln[0]['description']
        url = vuln[0]['url']

        discord_username = ctx.author.display_name

        save_cve(discord_username, cve_id, description, url)

        await ctx.send('CVE saved')

    @commands.command(
                        name="searchCVE",
                        help="Search the CVEs you have saved\n"
                        "Usage; \n"
                        "/searchCVE \n"
    )
    async def searchCVE(self, ctx):
        discord_username = ctx.author.display_name

        vulns = search_cve(discord_username)

        embeds = []

        for cve_id, description, url in vulns:
            embed = create_vuln_embed({
            "id": cve_id,
            "description": description,
            "url": url
            })
        embeds.append(embed)
        await paginate_embeds(self.bot, ctx, embeds)

async def setup(bot):
    await bot.add_cog(DbCommands(bot))