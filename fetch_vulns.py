from discord.ext import commands
from pagination import create_vuln_embed, paginate_embeds

class FetchVulns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Bot will send coucou to a mighty tomato")
    async def coucou(self, ctx):
        await ctx.send("coucou")

    @commands.command(
                        name="fetchVulns",
                        help="Fetches vulns based on 'pwn' CWEs in a time limit (not exceeding 120 days)\n"
                        "Usage: \n"
                        "/fetchVulns <startDate> <endDate>\n"
                        "exemple : \n"
                        "/fetchVulns 2024-11-20T00:00:00.000 2025-03-19T23:59:59.999"
                    )
    async def fetchVulns(self, ctx,
                         startDate: str = commands.parameter(description="start date"),
                         endDate: str = commands.parameter(description="end date")):
        
        vulns = await self.bot.nvd_api.fetch_pwn(start_date=startDate, end_date=endDate)

        embeds = []
        for vuln in vulns:
            embed = create_vuln_embed(vuln)
            embeds.append(embed)

        await paginate_embeds(self.bot, ctx, embeds) 

async def setup(bot):
    await bot.add_cog(FetchVulns(bot))