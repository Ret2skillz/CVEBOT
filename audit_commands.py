import discord
from discord import app_commands, Interaction
from discord.ext import commands
from pagination import create_audit_embed
from github_api import AUDIT_CATEGORIES
from db.crud import save_audit_repo, get_saved_audit_repos, delete_audit_repo

CATEGORY_CHOICES = [
    app_commands.Choice(name="All categories", value="all"),
    app_commands.Choice(name="Emulators", value="emulator"),
    app_commands.Choice(name="Virtual Machines / Hypervisors", value="vm"),
    app_commands.Choice(name="Custom Servers (FTP/HTTP/SMTP…)", value="server"),
    app_commands.Choice(name="File-parsing / custom libs", value="lib"),
    app_commands.Choice(name="Custom crypto libs", value="crypto"),
]


class AuditBrowserView(discord.ui.View):
    def __init__(self, repos, embeds, author_id):
        super().__init__(timeout=120)
        self.repos = repos
        self.embeds = embeds
        self.author_id = author_id
        self.current_page = 0
        self._update_state()

    def _update_state(self):
        self.children[0].disabled = (self.current_page == 0)
        self.children[2].disabled = (self.current_page == len(self.embeds) - 1)
        # Update footer to show page number
        if self.embeds:
            embed = self.embeds[self.current_page]
            embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.embeds)} | Repo: {self.repos[self.current_page]['name']}")

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This view is not for you.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.grey)
    async def prev_button(self, interaction: Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self._update_state()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label="Save Repo", style=discord.ButtonStyle.success, emoji="💾")
    async def save_button(self, interaction: Interaction, button: discord.ui.Button):
        repo = self.repos[self.current_page]
        save_audit_repo(
            discord_username=str(interaction.user.id),
            repo_name=repo['name'],
            repo_url=repo['url'],
            repo_desc=repo['description'][:500] if repo.get('description') else "No description",
            stars=repo.get('stars', 0),
            language=repo.get('language', "N/A")
        )
        await interaction.response.send_message(f"Saved **{repo['name']}** to your list!", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: Interaction, button: discord.ui.Button):
        self.current_page += 1
        self._update_state()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)


class SavedAuditView(discord.ui.View):
    def __init__(self, repos, embeds, author_id):
        super().__init__(timeout=120)
        self.repos = repos
        self.embeds = embeds
        self.author_id = author_id
        self.current_page = 0
        self._update_state()

    def _update_state(self):
        self.children[0].disabled = (self.current_page == 0)
        self.children[2].disabled = (self.current_page == len(self.embeds) - 1)
        if self.embeds:
            embed = self.embeds[self.current_page]
            embed.set_footer(text=f"Saved Repo {self.current_page + 1}/{len(self.embeds)}")

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.grey)
    async def prev_button(self, interaction: Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self._update_state()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_button(self, interaction: Interaction, button: discord.ui.Button):
        repo = self.repos[self.current_page]
        delete_audit_repo(str(interaction.user.id), repo['url'])
        
        # Remove from local list
        self.repos.pop(self.current_page)
        self.embeds.pop(self.current_page)
        
        if not self.repos:
            await interaction.response.edit_message(content="No more saved repos.", embed=None, view=None)
            self.stop()
            return
            
        # Adjust page index if needed
        if self.current_page >= len(self.repos):
            self.current_page = len(self.repos) - 1
            
        self._update_state()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        await interaction.followup.send(f"Removed **{repo['name']}**.", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: Interaction, button: discord.ui.Button):
        self.current_page += 1
        self._update_state()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)


class AuditCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        pass

    @app_commands.command(
        name="saved_audits",
        description="View your saved audit target repositories"
    )
    async def savedAudits(self, interaction: Interaction):
        repos = get_saved_audit_repos(str(interaction.user.id))
        if not repos:
            await interaction.response.send_message("You haven't saved any repositories yet!", ephemeral=True)
            return

        embeds = []
        for r in repos:
            # Reconstruct repo dict for the embed helper
            r_adapted = {
                "name": r["name"],
                "url": r["url"],
                "description": r["description"],
                "stars": r["stars"],
                "language": r["language"],
                "size_kb": "N/A",  
                "last_push": "N/A", 
                "owner": "Unknown" 
            }
            embeds.append(create_audit_embed(r_adapted))
        
        view = SavedAuditView(repos, embeds, interaction.user.id)
        # Send ephemeral=True for personal lists usually, but regular message also works. 
        # Using regular message so pagination buttons work easily without thinking about ephemeral complexity.
        await interaction.response.send_message(embed=embeds[0], view=view)

    @app_commands.command(
        name="audit_targets",
        description="Search GitHub for C/C++ repos that are good candidates for vulnerability auditing"
    )
    @app_commands.describe(
        category="Type of project to look for",
        stale="True = forgotten repos (not updated since 2021); False = moderately active repos",
        min_stars="Minimum stars (default: 10)",
        max_stars="Maximum stars (default: 500)",
        min_size="Minimum repo size in KB (default: 10)",
        max_size="Maximum repo size in KB (default: 10000)",
        page="Page of results (10 repos per page)"
    )
    @app_commands.choices(category=CATEGORY_CHOICES)
    async def auditTargets(
        self,
        interaction: Interaction,
        category: app_commands.Choice[str] = None,
        stale: bool = True,
        min_stars: int = 10,
        max_stars: int = 500,
        min_size: int = 10,
        max_size: int = 10000,
        page: int = 1,
    ):
        await interaction.response.defer()

        cat_value = category.value if category else "all"
        repos = await self.bot.github_api.fetch_audit_targets(
            category=cat_value,
            stale=stale,
            min_stars=min_stars,
            max_stars=max_stars,
            min_size=min_size,
            max_size=max_size,
            page=max(1, page),
        )

        if not repos:
            await interaction.followup.send(
                "No repositories found for those criteria. Try changing the category or toggling stale."
            )
            return

        embeds = [create_audit_embed(r) for r in repos]
        view = AuditBrowserView(repos, embeds, interaction.user.id)
        await interaction.followup.send(embed=embeds[0], view=view)


async def setup(bot):
    await bot.add_cog(AuditCommands(bot))
