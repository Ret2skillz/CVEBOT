from discord import app_commands, Interaction
from discord.ext import commands
from pagination import create_vuln_embed, paginate_embeds

class FetchVulns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        pass

    @app_commands.command(
                        name="weekly",
                        description="Fetches vulns of the last 7 days, you can add severity score if you want\n"
                    )
    @app_commands.describe(
        severity="<optional> Severity if you want one"
    )
    async def vulnsW(self, interaction: Interaction, severity: str= ""):
        
        vulns = await self.bot.nvd_api.fetch_weekly_pwn(severity)

        if not vulns:
            await interaction.send("No vulns with your criterias were found for this week!")
            return

        embeds = []
        for vuln in vulns:
            embed = create_vuln_embed(vuln)
            embeds.append(embed)

        await paginate_embeds(self.bot, interaction, embeds) 

    @app_commands.command(
                        name="monthly",
                        description="Fetches vulns of the last 30 days\n"
                    )
    @app_commands.describe(
        severity="<optional> Severity if you want one"
    )
    async def vulnsM(self, interaction: Interaction, severity: str= ""):

        vulns = await self.bot.nvd_api.fetch_monthly_pwn(severity)

        if not vulns:
            await interaction.send("No vulns with criteria were found for this month!")
            return

        embeds = []
        for vuln in vulns:
            embed = create_vuln_embed(vuln)
            embeds.append(embed)

        await paginate_embeds(self.bot, interaction, embeds)

    @app_commands.command(
                        name="trimester",
                        description="Fetches vulns of the last 120 days\n"
                    )
    @app_commands.describe(
        severity="<optional> Severity if you want one"
    )
    async def vulnsT(self, interaction: Interaction, severity: str= ""):

        vulns = await self.bot.nvd_api.fetch_trimester_pwn(severity)

        if not vulns:
            await interaction.send("No vulns with your criterias were found for the last 120 days!")
            return

        embeds = []
        for vuln in vulns:
            embed = create_vuln_embed(vuln)
            embeds.append(embed)

        await paginate_embeds(self.bot, interaction, embeds)

    @app_commands.command(
                        name="daily",
                        description="Fetches vulns of the last day\n"
                    )
    @app_commands.describe(
        severity="<optional> Severity if you want one"
    )
    async def vulnsD(self, interaction: Interaction, severity: str= ""):

        vulns = await self.bot.nvd_api.fetch_daily_pwn(severity)

        if not vulns:
            await interaction.send("No vulns with your criterias were found for last day")
            return

        embeds = []
        for vuln in vulns:
            embed = create_vuln_embed(vuln)
            embeds.append(embed)

        await paginate_embeds(self.bot, interaction, embeds)

    @app_commands.command(
                        name="custom",
                        description="Fetches vulns, between today - number, this number can't be bigger than 119\n"
                    )
    @app_commands.describe(
        range="Range of days you need",
        date="<optional> If you want to use a different date as base than today",
        severity="<optional> Severity if you want one"
    )
    async def vulnsC(self, interaction: Interaction, 
                     range: int, 
                     date: str= "",
                     severity: str= ""):

        vulns = await self.bot.nvd_api.fetch_custom_pwn(range, date, severity)

        if not vulns:
            await interaction.send("No vulns found for your days range!")
            return

        embeds = []
        for vuln in vulns:
            embed = create_vuln_embed(vuln)
            embeds.append(embed)

        await paginate_embeds(self.bot, interaction, embeds)

    @app_commands.command(
                        name="id",
                        description="Fetches vuln by its ID\n"
    )
    @app_commands.describe(
        id="Id of the CVE you want to search"
    )
    async def vulnID(self, interaction: Interaction, id: str):

        vulns = await self.bot.nvd_api.fetch_by_id(id)

        if not vulns:
            await interaction.send("No vuln of this ID found")
            return

        vuln = vulns[0]

        embeds = []
        embed = create_vuln_embed(vuln)
        embeds.append(embed)

        await paginate_embeds(self.bot, interaction, embeds)

async def setup(bot):
    await bot.add_cog(FetchVulns(bot))