from discord.ext import commands
from pagination import create_vuln_embed, paginate_embeds

class FetchVulns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Bot will send coucou to a mighty tomato")
    async def coucou(self, ctx):
        await ctx.send("coucou")

    @commands.command(help="Bot will just say bye to you")
    async def bye(self, ctx):
        await ctx.send("bye")

    @commands.command(
                        name="vulnsW",
                        help="Fetches vulns based on 'pwn' CWEs of the last 7 days, you can add severity score if you want\n"
                        "Usage: \n"
                        "/vulnsW <severity>\n"
                        "exemple : \n"
                        "/vulnsW high"
                    )
    async def vulnsW(self, ctx, severity: str= commands.parameter(default=None, description="<optional> Severity if you want one")):
        
        vulns = await self.bot.nvd_api.fetch_weekly_pwn(severity)

        embeds = []
        for vuln in vulns:
            embed = create_vuln_embed(vuln)
            embeds.append(embed)

        await paginate_embeds(self.bot, ctx, embeds) 

    @commands.command(
                        name="vulnsM",
                        help="Fetches vulns based on 'pwn' CWEs of the last 30 days\n"
                        "Usage: \n"
                        "/vulnsM \n"
                    )
    async def vulnsM(self, ctx, severity: str= commands.parameter(default=None, description="<optional> Severity if you want one")):

        vulns = await self.bot.nvd_api.fetch_monthly_pwn(severity)

        embeds = []
        for vuln in vulns:
            embed = create_vuln_embed(vuln)
            embeds.append(embed)

        await paginate_embeds(self.bot, ctx, embeds)

    @commands.command(
                        name="vulnsT",
                        help="Fetches vulns based on 'pwn' CWEs of the last 120 days\n"
                        "Usage: \n"
                        "/vulnsT \n"
                    )
    async def vulnsT(self, ctx, severity: str= commands.parameter(default=None, description="<optional> Severity if you want one")):

        vulns = await self.bot.nvd_api.fetch_trimester_pwn(severity)

        embeds = []
        for vuln in vulns:
            embed = create_vuln_embed(vuln)
            embeds.append(embed)

        await paginate_embeds(self.bot, ctx, embeds)

    @commands.command(
                        name="vulnsD",
                        help="Fetches vulns based on 'pwn' CWEs of the day\n"
                        "Usage: \n"
                        "/vulnsD \n"
                    )
    async def vulnsD(self, ctx, severity: str= commands.parameter(default=None, description="<optional> Severity if you want one")):

        vulns = await self.bot.nvd_api.fetch_daily_pwn(severity)

        embeds = []
        for vuln in vulns:
            embed = create_vuln_embed(vuln)
            embeds.append(embed)

        await paginate_embeds(self.bot, ctx, embeds)

    @commands.command(
                        name="vulnsC",
                        help="Fetches vulns, you amount a number it will fetch between today - number, this number can't be bigger than 119\n"
                        "Or optionally you can give a custom date instead of today but use the format Y-M-D or it will not work\n"
                        "Usage: \n"
                        "/vulnsC <number> <date>\n"
                        "Exemple: \n"
                        "/vulnsC 70 2024-10-30"
                    )
    async def vulnsC(self, ctx, 
                     range: int= commands.parameter(description="Range of days you need"), 
                     date: str= commands.parameter(default="", description="<optional> If you want to use a different date as base than today"),
                     severity: str= commands.parameter(default=None, description="<optional> Severity if you want one")):

        vulns = await self.bot.nvd_api.fetch_custom_pwn(range, date, severity)

        embeds = []
        for vuln in vulns:
            embed = create_vuln_embed(vuln)
            embeds.append(embed)

        await paginate_embeds(self.bot, ctx, embeds)

    @commands.command(
                        name="vulnID",
                        help="Fetches vuln by its ID\n"
                        "Usage: \n"
                        "vulnID <ID>"
    )
    async def vulnID(self, ctx, id: str=commands.parameter(description="Id of the CVE you want to search")):

        vuln = await self.bot.nvd_api.fetch_by_id(id)

        embeds = []
        embed = create_vuln_embed(vuln)
        embeds.append(embed)

        await paginate_embeds(self.bot, ctx, embeds)

async def setup(bot):
    await bot.add_cog(FetchVulns(bot))