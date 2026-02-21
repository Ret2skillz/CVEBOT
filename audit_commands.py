from discord import app_commands, Interaction
from discord.ext import commands
from pagination import create_audit_embed, paginate_embeds
from github_api import AUDIT_CATEGORIES

CATEGORY_CHOICES = [
    app_commands.Choice(name="All categories", value="all"),
    app_commands.Choice(name="Emulators", value="emulator"),
    app_commands.Choice(name="Virtual Machines / Hypervisors", value="vm"),
    app_commands.Choice(name="Custom Servers (FTP/HTTP/SMTP…)", value="server"),
    app_commands.Choice(name="File-parsing / custom libs", value="lib"),
    app_commands.Choice(name="Custom crypto libs", value="crypto"),
]


class AuditCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        pass

    @app_commands.command(
        name="audit_targets",
        description="Search GitHub for C/C++ repos that are good candidates for vulnerability auditing"
    )
    @app_commands.describe(
        category="Type of project to look for",
        stale="True = forgotten repos (not updated since 2021); False = moderately active repos",
        page="Page of results (10 repos per page)"
    )
    @app_commands.choices(category=CATEGORY_CHOICES)
    async def auditTargets(
        self,
        interaction: Interaction,
        category: app_commands.Choice[str] = None,
        stale: bool = True,
        page: int = 1,
    ):
        await interaction.response.defer()

        cat_value = category.value if category else "all"
        repos = await self.bot.github_api.fetch_audit_targets(
            category=cat_value,
            stale=stale,
            page=max(1, page),
        )

        if not repos:
            await interaction.followup.send(
                "No repositories found for those criteria. Try changing the category or toggling stale."
            )
            return

        embeds = [create_audit_embed(r) for r in repos]
        await paginate_embeds(self.bot, interaction, embeds)


async def setup(bot):
    await bot.add_cog(AuditCommands(bot))
