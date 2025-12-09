from discord import app_commands, Interaction
from discord.ext import commands
from pagination import create_vuln_embed, paginate_embeds
from db.crud import *

class DbCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        pass

    @app_commands.command(
                        name="save",
                        description="Save any Cve you want based on its id, tag is single word, no spaces"
                    )
    @app_commands.describe(
                        cve_id="The ID of the CVE you want to save",
                        tag="<optional> a tag you can assign to each cve you save",
                        type_vuln="you can add a type to group some vulns, can be anything from type of vuln to vendor to date, just single word and no spaces"
    )
    async def saveCVE(self, interaction: Interaction, cve_id: str,tag: str= "", type_vuln: str=""):
        
        vuln = await self.bot.nvd_api.fetch_by_id(cve_id)

        if not vuln:
            await interaction.response.send_message("You must have entered a wrong CVE ID")
            return

        description = vuln[0]['description']
        url = vuln[0]['url']

        discord_username = interaction.user.display_name

        save_cve(discord_username, cve_id, description, url, tag, type_vuln)

        await interaction.response.send_message('CVE saved')

    @app_commands.command(
                        name="searchmy",
                        description="Search all the CVEs you have saved\n"
    )
    async def searchCVE(self, interaction: Interaction):
        discord_username = interaction.user.display_name

        vulns = search_cve(discord_username)

        if not vulns:
            await interaction.response.send_message("You have no saved CVEs")
            return

        embeds = []

        for cve_id, description, url, tag, type_vuln in vulns:
            embed = create_vuln_embed({
            "id": cve_id,
            "description": description,
            "url": url,
            "tag": tag,
            "type_vuln": type_vuln
            })
            embeds.append(embed)
        await paginate_embeds(self.bot, interaction, embeds)

    @app_commands.command(
                        name="searchtag",
                        description="Search the CVEs you have saved, from its tag\n"
    )
    @app_commands.describe(
                        tag="Tag of a CVE you have saved",
    )
    async def searchTAG(self, interaction: Interaction,
                        tag: str):
        discord_username = interaction.user.display_name

        vulns = search_by_tag(discord_username, tag)

        if not vulns:
            await interaction.response.send_message("No CVEs of this tag found")
            return

        embeds = []

        for cve_id, description, url, type_vuln in vulns:
            embed = create_vuln_embed({
            "id": cve_id,
            "description": description,
            "url": url,
            "type_vuln": type_vuln
            })
            embeds.append(embed)
        await paginate_embeds(self.bot, interaction, embeds)

    @app_commands.command(
                        name="searchtype",
                        description="Search the CVEs you have saved, by their type\n"
    )
    @app_commands.describe(
                        type_vuln="Search vulns by their type, useful to 'group' your CVEs",
    )
    async def searchTYPE(self, interaction: Interaction,
                        type_vuln: str):
        discord_username = interaction.user.display_name

        vulns = search_by_type(discord_username, type_vuln)

        if not vulns:
            await interaction.response.send_message("No CVEs of this type found")
            return

        embeds = []

        for cve_id, description, url, tag in vulns:
            embed = create_vuln_embed({
            "id": cve_id,
            "description": description,
            "url": url,
            "tag": tag
            })
            embeds.append(embed)
        await paginate_embeds(self.bot, interaction, embeds)

    @app_commands.command(
                        name="delete",
                        description="Delete one of your saved CVE\n"
    )
    async def deleteCVE(self, interaction: Interaction):
        discord_username = interaction.user.display_name

        delete_cve(discord_username)

        await interaction.response.send_message("CVE successfully deleted")

async def setup(bot):
    await bot.add_cog(DbCommands(bot))
