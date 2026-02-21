import asyncio
import logging
import discord
import io
from typing import Dict, List, Any

log = logging.getLogger(__name__)

# Discord limits
EMBED_TITLE_LIMIT = 256
EMBED_DESCRIPTION_LIMIT = 4096
EMBED_FIELD_NAME_LIMIT = 256
EMBED_FIELD_VALUE_LIMIT = 1024

def _truncate(text: str, limit: int) -> str:
    if text is None:
        return ""
    text = str(text)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."

def create_vuln_embed(vuln: Dict[str, Any]) -> discord.Embed:
    """
    Create a safe embed for a vulnerability.
    Layout:
      - title: CVE ID
      - description: long description (truncated to EMBED_DESCRIPTION_LIMIT)
      - fields: Published, Url, CWE, CVSS (each value truncated to EMBED_FIELD_VALUE_LIMIT)
    """
    title = _truncate(vuln.get("id", "Unknown"), EMBED_TITLE_LIMIT)
    description = _truncate(vuln.get("description", "") or "", EMBED_DESCRIPTION_LIMIT)

    embed = discord.Embed(title=title, description=description, color=discord.Color.red())

    def add_safe_field(name: str, value: str, inline: bool = False):
        if not value:
            return
        name = _truncate(name, EMBED_FIELD_NAME_LIMIT)
        value = _truncate(value, EMBED_FIELD_VALUE_LIMIT)
        embed.add_field(name=name, value=value, inline=inline)

    published = vuln.get("published")
    if published:
        add_safe_field("Published", published, inline=True)

    url = vuln.get("url")
    if url:
        add_safe_field("Url", url, inline=False)

    cwe = vuln.get("cwe")
    if cwe:
        add_safe_field("CWE", cwe, inline=True)

    cvss = vuln.get("cvss")
    if cvss:
        add_safe_field("CVSS", str(cvss), inline=True)

    return embed

def create_poc_embed(poc: Dict[str, Any]) -> discord.Embed:
    """
    Create a safe embed for a PoC entry.
    Expected keys in `poc` (best-effort): title, id (CVE), description, author, url, references (list), date
    """
    # Prefer a human title, fall back to id or 'PoC'
    title = poc.get("title") or poc.get("id") or "PoC"
    title = _truncate(title, EMBED_TITLE_LIMIT)

    description = poc.get("description", "") or ""
    description = _truncate(description, EMBED_DESCRIPTION_LIMIT)

    embed = discord.Embed(title=title, description=description, color=discord.Color.dark_gold())

    def add_safe_field(name: str, value: str, inline: bool = False):
        if not value:
            return
        name = _truncate(name, EMBED_FIELD_NAME_LIMIT)
        value = _truncate(value, EMBED_FIELD_VALUE_LIMIT)
        embed.add_field(name=name, value=value, inline=inline)

    if poc.get("id"):
        add_safe_field("CVE", poc.get("id"), inline=True)

    if poc.get("author"):
        add_safe_field("Author", poc.get("author"), inline=True)

    if poc.get("date"):
        add_safe_field("Date", poc.get("date"), inline=True)

    if poc.get("url"):
        add_safe_field("Url", poc.get("url"), inline=False)

    refs = poc.get("references") or poc.get("refs") or []
    if isinstance(refs, (list, tuple)) and refs:
        # join references into a single field (truncated)
        refs_text = "\n".join(str(r) for r in refs)
        add_safe_field("References", refs_text, inline=False)
    elif isinstance(refs, str) and refs:
        add_safe_field("References", refs, inline=False)

    return embed

<<<<<<< Updated upstream
def create_audit_embed(repo):
    embed = discord.Embed(
        title=repo['name'],
        url=repo['url'],
        description=repo['description'],
        color=discord.Color.orange()
    )
    embed.add_field(name="Owner", value=repo['owner'])
    embed.add_field(name="Language", value=repo['language'])
    embed.add_field(name="Stars", value=str(repo['stars']))
    embed.add_field(name="Size (KB)", value=str(repo['size_kb']))
    embed.add_field(name="Last Push", value=repo['last_push'])
    return embed

async def paginate_embeds(bot, ctx, embeds, timeout=60):
=======
def _embed_to_text(embed: discord.Embed) -> str:
    """
    Render embed into plain text for fallback when embed cannot be sent.
    """
    lines = []
    if embed.title:
        lines.append(f"TITLE: {embed.title}")
    if embed.description:
        lines.append("")
        lines.append(embed.description)
        lines.append("")
    for f in embed.fields:
        lines.append(f"{f.name}:")
        lines.append(f.value)
        lines.append("")
    return "\n".join(lines)

async def paginate_embeds(bot, ctx, embeds: List[discord.Embed], timeout: int = 60):
>>>>>>> Stashed changes
    """
    Paginate embeds and support both:
    - discord.Interaction: use response / followup
    - legacy ctx (commands.Context): use ctx.send
    If an embed fails due to size, fall back to sending a text file with contents.
    """
    if not embeds:
        return

    current_page = 0
    is_interaction = isinstance(ctx, discord.Interaction)

    # send initial embed (or fallback to file)
    try:
        if is_interaction:
            if not ctx.response.is_done():
                await ctx.response.send_message(embed=embeds[current_page])
                message = await ctx.original_response()
            else:
                message = await ctx.followup.send(embed=embeds[current_page], wait=True)
            author = ctx.user
        else:
            message = await ctx.send(embed=embeds[current_page])
            author = ctx.author
    except discord.HTTPException as e:
        log.debug("Initial embed send failed, falling back to file: %s", e)
        text = _embed_to_text(embeds[current_page])
        buf = io.StringIO(text)
        file = discord.File(io.BytesIO(buf.getvalue().encode("utf-8")), filename=f"page_{current_page+1}.txt")
        if is_interaction:
            if not ctx.response.is_done():
                await ctx.response.send_message("Embed too large; sending as file.", file=file)
            else:
                await ctx.followup.send("Embed too large; sending as file.", file=file)
        else:
            await ctx.send("Embed too large; sending as file.", file=file)
        return

    # try adding reactions for pagination
    try:
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")
    except Exception as e:
        log.debug("Could not add pagination reactions: %s", e)

    def check(reaction, user):
        return user == author and str(reaction.emoji) in ["⬅️", "➡️"]

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=timeout, check=check)

            if str(reaction.emoji) == "➡️" and current_page < len(embeds) - 1:
                current_page += 1
                try:
                    await message.edit(embed=embeds[current_page])
                except discord.HTTPException as e:
                    log.debug("Embed edit failed, falling back to file: %s", e)
                    text = _embed_to_text(embeds[current_page])
                    buf = io.StringIO(text)
                    file = discord.File(io.BytesIO(buf.getvalue().encode("utf-8")), filename=f"page_{current_page+1}.txt")
                    try:
                        await message.channel.send(file=file)
                    except Exception as e2:
                        log.debug("Fallback file send failed: %s", e2)

            elif str(reaction.emoji) == "⬅️" and current_page > 0:
                current_page -= 1
                try:
                    await message.edit(embed=embeds[current_page])
                except discord.HTTPException as e:
                    log.debug("Embed edit failed, falling back to file: %s", e)
                    text = _embed_to_text(embeds[current_page])
                    buf = io.StringIO(text)
                    file = discord.File(io.BytesIO(buf.getvalue().encode("utf-8")), filename=f"page_{current_page+1}.txt")
                    try:
                        await message.channel.send(file=file)
                    except Exception as e2:
                        log.debug("Fallback file send failed: %s", e2)

            # try to remove user's reaction
            try:
                await message.remove_reaction(str(reaction.emoji), user)
            except discord.Forbidden:
                log.debug("Missing MANAGE_MESSAGES; cannot remove user's reaction")
                try:
                    await message.remove_reaction(str(reaction.emoji), bot.user)
                except Exception as e:
                    log.debug("Could not remove bot reaction either: %s", e)
            except Exception as e:
                log.debug("Unexpected error removing reaction: %s", e)

        except asyncio.TimeoutError:
            break