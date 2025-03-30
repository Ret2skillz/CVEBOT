from discord.ext import commands
from pagination import create_vuln_embed, paginate_embeds
from db.crud import *

class DbCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
                        name="saveCVE",
                        help="Save any Cve you want based on its id, you can add a tag to retrieve them more easily (singe word, no spaces)\n"
                        "Usage: \n"
                        "/saveCve <cve_id> <tag> <type_vuln>\n"
                    )
    async def saveCVE(self, ctx, 
                      cve_id: str= commands.parameter(description="The ID of the CVE you want to save"),
                      tag: str= commands.parameter(default="", description="<optional> a tag you can assign to each cve you save"),
                      type_vuln: str=commands.parameter(default="", description="you can add a type to group some vulns, can be anything from type of vuln to vendor to date, just single word and no spaces")):
        
        vuln = await self.bot.nvd_api.fetch_by_id(cve_id)

        description = vuln[0]['description']
        url = vuln[0]['url']

        discord_username = ctx.author.display_name

        save_cve(discord_username, cve_id, description, url, tag, type_vuln)

        await ctx.send('CVE saved')

    @commands.command(
                        name="myCVE",
                        help="Search the CVEs you have saved\n"
                        "Usage; \n"
                        "/myCVE \n"
    )
    async def searchCVE(self, ctx):
        discord_username = ctx.author.display_name

        vulns = search_cve(discord_username)

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
        await paginate_embeds(self.bot, ctx, embeds)

    @commands.command(
                        name="searchTAG",
                        help="Search the CVEs you have saved, from its tag\n"
                        "Usage; \n"
                        "/searchTAG <tag> \n"
    )
    async def searchTAG(self, ctx,
                        tag: str= commands.parameter(description="Tag of a CVE you have saved")):
        discord_username = ctx.author.display_name

        vulns = search_by_tag(discord_username, tag)

        embeds = []

        for cve_id, description, url, type_vuln in vulns:
            embed = create_vuln_embed({
            "id": cve_id,
            "description": description,
            "url": url,
            "type_vuln": type_vuln
            })
            embeds.append(embed)
        await paginate_embeds(self.bot, ctx, embeds)

    @commands.command(
                        name="searchTYPE",
                        help="Search the CVEs you have saved, by their type\n"
                        "Usage; \n"
                        "/searchTYPE <type_vuln>\n"
    )
    async def searchTYPE(self, ctx,
                        type_vuln: str= commands.parameter(description="Search vulns by their type, useful to 'group' your CVEs")):
        discord_username = ctx.author.display_name

        vulns = search_by_type(discord_username, type_vuln)

        embeds = []

        for cve_id, description, url, tag in vulns:
            embed = create_vuln_embed({
            "id": cve_id,
            "description": description,
            "url": url,
            "tag": tag
            })
            embeds.append(embed)
        await paginate_embeds(self.bot, ctx, embeds)

    @commands.command(
                        name="deleteCVE",
                        help="Delete one of your saved CVE\n"
                        "USage: \n"
                        "/deleteCVE \n"
    )
    async def deleteCVE(self, ctx):
        discord_username = ctx.author.display_name

        delete_cve(discord_username)

        await ctx.send("CVE successfully deleted")

async def setup(bot):
    await bot.add_cog(DbCommands(bot))