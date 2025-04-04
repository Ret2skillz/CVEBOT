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
    current_page = 0
    message = await ctx.send(embed=embeds[current_page])

    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]
    
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=timeout, check=check)

            if str(reaction.emoji) == "➡️" and current_page < len(embeds) - 1:
                current_page += 1
                await message.edit(embed=embeds[current_page])
            elif str(reaction.emoji) == "⬅️" and current_page > 0:
                current_page -= 1
                await message.edit(embed=embeds[current_page])

            await message.remove_reaction(reaction, user)

        except asyncio.TimeoutError:
            break