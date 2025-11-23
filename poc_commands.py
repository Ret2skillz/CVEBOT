from discord import app_commands, Interaction
from discord.ext import commands
from pagination import create_poc_embed, paginate_embeds
from db.crud import *

class PoCCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        pass

    @app_commands.command(
                        name="poc",
                        description="Search on github for a PoC for a CVE\n"
                    )
    @app_commands.describe(
                        cve_id="The ID of the CVE you want to find a PoC"
    )   
    async def searchPOC(self, interaction: Interaction, 
                      cve_id: str ):
        
        repos = await self.bot.github_api.fetch_poc(cve_id)

        if not repos:
            await interaction.send("No PoC found for this CVE")
            return

        embeds = []
        for poc in repos:
            embed = create_poc_embed(poc)
            embeds.append(embed)

        await paginate_embeds(self.bot, interaction, embeds)

async def setup(bot):
    await bot.add_cog(PoCCommands(bot))