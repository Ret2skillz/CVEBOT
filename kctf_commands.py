from discord import app_commands, Interaction
from discord.ext import commands
from pagination import create_kctf_embed, paginate_embeds
from kctf_api import KCTFApi


class KCTFCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.kctf_api = KCTFApi()

    async def cog_load(self):
        pass

    @app_commands.command(
        name="kctf_latest",
        description="Fetch the latest entries from the kCTF VRP spreadsheet with commits and flag-capture times",
    )
    @app_commands.describe(
        count="Number of latest entries to display (1–25, default 10)"
    )
    async def kctfLatest(self, interaction: Interaction, count: int = 10):
        if count < 1 or count > 25:
            await interaction.response.send_message(
                "Count must be between 1 and 25.", ephemeral=True
            )
            return

        await interaction.response.defer()

        entries = self.kctf_api.fetch_latest(count)

        if not entries:
            await interaction.followup.send(
                "Could not retrieve kCTF entries. The spreadsheet may be unavailable."
            )
            return

        embeds = [create_kctf_embed(e) for e in entries]
        await paginate_embeds(self.bot, interaction, embeds)


async def setup(bot):
    await bot.add_cog(KCTFCommands(bot))
