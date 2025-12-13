# Updated fetch_vulns.py — ensure we pass product=None for "all" so original pwn searches still run.
from discord import app_commands, Interaction
from discord.ext import commands
from pagination import create_vuln_embed, paginate_embeds
from csv_utils import vulns_to_csv_bytes
import discord
import io
from product_map import PRODUCTS

PRODUCT_CHOICES = [app_commands.Choice(name=v["label"], value=k) for k, v in PRODUCTS.items()]


class FetchVulns(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        pass

    async def _prepare_product(self, product_choice: app_commands.Choice | None, exact: bool):
        """
        Return:
          - None when 'all' (no product filter)
          - product dict otherwise (with 'strict' set if exact=True)
        """
        key = product_choice.value if product_choice else "all"
        if key == "all":
            return None
        info = PRODUCTS.get(key, {}).copy() if PRODUCTS.get(key) else {"label": key, "keyword": None, "cpe": None}
        if exact:
            info["strict"] = True
        return info

    @app_commands.command(
        name="weekly",
        description="Fetches vulns of the last 7 days; can filter by product and export CSV"
    )
    @app_commands.describe(
        severity="<optional> Severity if you want one",
        product="Optional product/vendor to filter results",
        as_csv="<optional> Send results as a CSV file instead of paginated embeds",
        exact="If true, use exact CPE filtering only (do not fallback to keyword)"
    )
    @app_commands.choices(product=PRODUCT_CHOICES)
    async def vulnsW(self, interaction: Interaction, severity: str = "", product: app_commands.Choice[str] = None, as_csv: bool = False, exact: bool = False):
        await interaction.response.defer()
        product_info = await self._prepare_product(product, exact)
        vulns = await self.bot.nvd_api.fetch_weekly_pwn(severity=severity, product=product_info)

        if not vulns:
            await interaction.followup.send("No vulns with your criterias were found for this week!")
            return

        if as_csv:
            csv_bytes = vulns_to_csv_bytes(vulns)
            filename = f"vulns_weekly_{product_info.get('label','all') if product_info else 'all'}.csv"
            file_obj = discord.File(io.BytesIO(csv_bytes), filename=filename)
            await interaction.followup.send("CSV export:", file=file_obj)
            return

        embeds = [create_vuln_embed(v) for v in vulns]
        await paginate_embeds(self.bot, interaction, embeds)

    @app_commands.command(name="monthly", description="Fetches vulns of the last 30 days; can filter by product and export CSV")
    @app_commands.describe(severity="<optional> Severity if you want one", product="Optional product/vendor to filter results", as_csv="<optional> Send results as a CSV file instead of paginated embeds", exact="If true, use exact CPE filtering only (do not fallback to keyword)")
    @app_commands.choices(product=PRODUCT_CHOICES)
    async def vulnsM(self, interaction: Interaction, severity: str = "", product: app_commands.Choice[str] = None, as_csv: bool = False, exact: bool = False):
        await interaction.response.defer()
        product_info = await self._prepare_product(product, exact)
        vulns = await self.bot.nvd_api.fetch_monthly_pwn(severity=severity, product=product_info)

        if not vulns:
            await interaction.followup.send("No vulns with criteria were found for this month!")
            return

        if as_csv:
            csv_bytes = vulns_to_csv_bytes(vulns)
            filename = f"vulns_monthly_{product_info.get('label','all') if product_info else 'all'}.csv"
            file_obj = discord.File(io.BytesIO(csv_bytes), filename=filename)
            await interaction.followup.send("CSV export:", file=file_obj)
            return

        embeds = [create_vuln_embed(v) for v in vulns]
        await paginate_embeds(self.bot, interaction, embeds)

    @app_commands.command(name="trimester", description="Fetches vulns of the last 120 days; can filter by product and export CSV")
    @app_commands.describe(severity="<optional> Severity if you want one", product="Optional product/vendor to filter results", as_csv="<optional> Send results as a CSV file instead of paginated embeds", exact="If true, use exact CPE filtering only (do not fallback to keyword)")
    @app_commands.choices(product=PRODUCT_CHOICES)
    async def vulnsT(self, interaction: Interaction, severity: str = "", product: app_commands.Choice[str] = None, as_csv: bool = False, exact: bool = False):
        await interaction.response.defer()
        product_info = await self._prepare_product(product, exact)
        vulns = await self.bot.nvd_api.fetch_trimester_pwn(severity=severity, product=product_info)

        if not vulns:
            await interaction.followup.send("No vulns with your criterias were found for the last 120 days!")
            return

        if as_csv:
            csv_bytes = vulns_to_csv_bytes(vulns)
            filename = f"vulns_trimester_{product_info.get('label','all') if product_info else 'all'}.csv"
            file_obj = discord.File(io.BytesIO(csv_bytes), filename=filename)
            await interaction.followup.send("CSV export:", file=file_obj)
            return

        embeds = [create_vuln_embed(v) for v in vulns]
        await paginate_embeds(self.bot, interaction, embeds)

    @app_commands.command(name="daily", description="Fetches vulns of the last day; can filter by product and export CSV")
    @app_commands.describe(severity="<optional> Severity if you want one", product="Optional product/vendor to filter results", as_csv="<optional> Send results as a CSV file instead of paginated embeds", exact="If true, use exact CPE filtering only (do not fallback to keyword)")
    @app_commands.choices(product=PRODUCT_CHOICES)
    async def vulnsD(self, interaction: Interaction, severity: str = "", product: app_commands.Choice[str] = None, as_csv: bool = False, exact: bool = False):
        await interaction.response.defer()
        product_info = await self._prepare_product(product, exact)
        vulns = await self.bot.nvd_api.fetch_daily_pwn(severity=severity, product=product_info)

        if not vulns:
            await interaction.followup.send("No vulns with your criterias were found for last day")
            return

        if as_csv:
            csv_bytes = vulns_to_csv_bytes(vulns)
            filename = f"vulns_daily_{product_info.get('label','all') if product_info else 'all'}.csv"
            file_obj = discord.File(io.BytesIO(csv_bytes), filename=filename)
            await interaction.followup.send("CSV export:", file=file_obj)
            return

        embeds = [create_vuln_embed(v) for v in vulns]
        await paginate_embeds(self.bot, interaction, embeds)

    @app_commands.command(name="custom", description="Fetches vulns between today - number of days (max 119); can filter by product")
    @app_commands.describe(range="Range of days you need (max 119)", date="<optional> base date YYYY-MM-DD", severity="<optional> Severity", product="Optional product/vendor", as_csv="<optional> CSV export", exact="If true, use exact CPE filtering only (do not fallback to keyword)")
    @app_commands.choices(product=PRODUCT_CHOICES)
    async def vulnsC(self, interaction: Interaction, range: int, date: str = "", severity: str = "", product: app_commands.Choice[str] = None, as_csv: bool = False, exact: bool = False):
        if range < 0 or range > 119:
            await interaction.response.defer()
            await interaction.followup.send("Range must be between 0 and 119 days.")
            return

        await interaction.response.defer()
        product_info = await self._prepare_product(product, exact)
        vulns = await self.bot.nvd_api.fetch_custom_pwn(range, date, severity, product=product_info)

        if not vulns:
            await interaction.followup.send("No vulns found for your days range!")
            return

        if as_csv:
            csv_bytes = vulns_to_csv_bytes(vulns)
            filename = f"vulns_custom_{range}d_{product_info.get('label','all') if product_info else 'all'}.csv"
            file_obj = discord.File(io.BytesIO(csv_bytes), filename=filename)
            await interaction.followup.send("CSV export:", file=file_obj)
            return

        embeds = [create_vuln_embed(v) for v in vulns]
        await paginate_embeds(self.bot, interaction, embeds)

    @app_commands.command(name="id", description="Fetches vuln by its ID")
    @app_commands.describe(id="Id of the CVE you want to search", product="Optional product/vendor to filter results (not usually needed for ID lookups)", as_csv="<optional> CSV export", exact="If true, use exact CPE filtering only (do not fallback to keyword)")
    @app_commands.choices(product=PRODUCT_CHOICES)
    async def vulnID(self, interaction: Interaction, id: str, product: app_commands.Choice[str] = None, as_csv: bool = False, exact: bool = False):
        await interaction.response.defer()
        product_info = await self._prepare_product(product, exact)
        vulns = await self.bot.nvd_api.fetch_by_id(id, product=product_info)

        if not vulns:
            await interaction.followup.send("No vuln of this ID found")
            return

        if as_csv:
            csv_bytes = vulns_to_csv_bytes(vulns)
            filename = f"vuln_{id}_{product_info.get('label','all') if product_info else 'all'}.csv"
            file_obj = discord.File(io.BytesIO(csv_bytes), filename=filename)
            await interaction.followup.send("CSV export:", file=file_obj)
            return

        vuln = vulns[0]
        embed = create_vuln_embed(vuln)
        await paginate_embeds(self.bot, interaction, [embed])


async def setup(bot):
    await bot.add_cog(FetchVulns(bot))