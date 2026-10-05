import aiohttp
import random
import re
import os
import discord

async def buscar_gif(query):
    try:
        api_key = os.getenv("GIPHY_API_KEY")
        url = f"https://api.giphy.com/v1/gifs/search?api_key={api_key}&q={query}&limit=10"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get("data"):
                    return random.choice(data["data"])["images"]["original"]["url"]
    except Exception as e:
        print(f"⚠️ Error buscando GIF: {e}")
    return None

async def enviar_con_gif(canal, texto):
    match = re.search(r"\[GIF:\s*(.*?)\]", texto)
    if not match:
        await canal.send(texto)
        return

    query = match.group(1)
    texto_limpio = re.sub(r"\[GIF:.*?\]", "", texto).strip()

    gif = await buscar_gif(query)

    embed = discord.Embed(description=texto_limpio)
    if gif:
        embed.set_image(url=gif)

    await canal.send(embed=embed)