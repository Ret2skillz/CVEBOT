import discord
from discord import app_commands, Interaction
from discord.ext import commands
from pagination import create_kctf_embed
from kctf_api import KCTFApi
from db.crud import save_kctf_entry, get_saved_kctf_entries, delete_kctf_entry


class KCTFBrowserView(discord.ui.View):
    def __init__(self, entries, embeds, author_id):
        super().__init__(timeout=120)
        self.entries = entries
        self.embeds = embeds
        self.author_id = author_id
        self.current_page = 0
        self._update_state()

    def _update_state(self):
        self.children[0].disabled = (self.current_page == 0)
        self.children[2].disabled = (self.current_page == len(self.embeds) - 1)
        if self.embeds:
            embed = self.embeds[self.current_page]
            embed.set_footer(text=f"Entry {self.current_page + 1}/{len(self.embeds)}")

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

    @discord.ui.button(label="Save Entry", style=discord.ButtonStyle.success, emoji="💾")
    async def save_button(self, interaction: Interaction, button: discord.ui.Button):
        entry = self.entries[self.current_page]
        issue = entry.get("issue", "")
        if not issue:
            await interaction.response.send_message(
                "Cannot save: entry has no issue identifier.", ephemeral=True
            )
            return
        saved = save_kctf_entry(
            discord_username=str(interaction.user.id),
            issue=issue,
            commit=entry.get("commit", ""),
            captured=entry.get("captured", ""),
            submitter=entry.get("submitter", ""),
            reward=entry.get("reward", ""),
        )
        if saved:
            await interaction.response.send_message(
                f"Saved kCTF entry **{issue}**!", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"**{issue}** is already in your saved entries.", ephemeral=True
            )

    @discord.ui.button(label="Next", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: Interaction, button: discord.ui.Button):
        self.current_page += 1
        self._update_state()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)


class KCTFSavedView(discord.ui.View):
    def __init__(self, entries, embeds, author_id):
        super().__init__(timeout=120)
        self.entries = entries
        self.embeds = embeds
        self.author_id = author_id
        self.current_page = 0
        self._update_state()

    def _update_state(self):
        self.children[0].disabled = (self.current_page == 0)
        self.children[2].disabled = (self.current_page == len(self.embeds) - 1)
        if self.embeds:
            embed = self.embeds[self.current_page]
            embed.set_footer(text=f"Saved Entry {self.current_page + 1}/{len(self.embeds)}")

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

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_button(self, interaction: Interaction, button: discord.ui.Button):
        entry = self.entries[self.current_page]
        delete_kctf_entry(str(interaction.user.id), entry['issue'])

        self.entries.pop(self.current_page)
        self.embeds.pop(self.current_page)

        if not self.entries:
            await interaction.response.edit_message(content="No more saved entries.", embed=None, view=None)
            self.stop()
            return

        if self.current_page >= len(self.entries):
            self.current_page = len(self.entries) - 1

        self._update_state()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        await interaction.followup.send(f"Removed entry **{entry['issue']}**.", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: Interaction, button: discord.ui.Button):
        self.current_page += 1
        self._update_state()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)


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
        view = KCTFBrowserView(entries, embeds, interaction.user.id)
        await interaction.followup.send(embed=embeds[0], view=view)

    @app_commands.command(
        name="kctf_saved",
        description="View your saved kCTF VRP entries",
    )
    async def kctfSaved(self, interaction: Interaction):
        entries = get_saved_kctf_entries(str(interaction.user.id))
        if not entries:
            await interaction.response.send_message(
                "You haven't saved any kCTF entries yet!", ephemeral=True
            )
            return

        embeds = [create_kctf_embed(e) for e in entries]
        view = KCTFSavedView(entries, embeds, interaction.user.id)
        await interaction.response.send_message(embed=embeds[0], view=view)


async def setup(bot):
    await bot.add_cog(KCTFCommands(bot))
