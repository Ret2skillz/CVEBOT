import asyncio
import discord

def create_vuln_embed(vuln):
    embed = discord.Embed(
        title = vuln['id'],
        color=discord.Color.red()
    )

    embed.add_field(name="description", value=vuln['description'])
    if 'published' in vuln:
        embed.add_field(name="Published", value=vuln['published'])
    embed.add_field(name="Url", value=vuln['url'])
    if 'tag' in vuln:
        embed.add_field(name="Tag", value=vuln['tag'])
    if 'type_vuln' in vuln:
        embed.add_field(name="Type", value=vuln['type_vuln'])

    return embed

def create_poc_embed(poc):
    embed = discord.Embed(
        title = poc['name'],
        color=discord.Color.blue()
    )

    embed.add_field(name="owner", value=poc['owner'])
    embed.add_field(name="url", value=poc['url'])

    return embed

async def paginate_embeds(bot, ctx, embeds, timeout=60):
    """
    Paginate embeds and support both:
    - commands.Context (prefix commands): ctx.send, ctx.author
    - discord.Interaction (slash commands / component callbacks): interaction.response.send_message, interaction.user

    Usage:
      await paginate_embeds(bot, interaction, embeds)
      or
      await paginate_embeds(bot, ctx, embeds)
    """
    current_page = 0

    is_interaction = isinstance(ctx, discord.Interaction)

    if is_interaction:
        # For interactions, send an initial response and fetch the created message
        await ctx.response.send_message(embed=embeds[current_page])
        message = await ctx.original_response()
        author = ctx.user
    else:
        # Assume a commands.Context-like object
        message = await ctx.send(embed=embeds[current_page])
        author = ctx.author

    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return user == author and str(reaction.emoji) in ["⬅️", "➡️"]
    
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=timeout, check=check)

            if str(reaction.emoji) == "➡️" and current_page < len(embeds) - 1:
                current_page += 1
                await message.edit(embed=embeds[current_page])
            elif str(reaction.emoji) == "⬅️" and current_page > 0:
                current_page -= 1
                await message.edit(embed=embeds[current_page])

            # remove the user's reaction
            await message.remove_reaction(str(reaction.emoji), user)

        except asyncio.TimeoutError:
            break
