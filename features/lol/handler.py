from .stats import obtener_elo
from .embed import crear_embed_lol
from .link import vincular_lol

async def manejar_lol(message):
    contenido = message.content.strip()
    contenido_lower = contenido.lower()

    if "vincular" in contenido_lower:
        await vincular_lol(message)
        return

    partes = contenido.split(" ", 1)

    if len(partes) < 2 or "#" not in partes[1]:
        await message.channel.send("❌ Usá: `!lol Nombre#TAG` (Ej: `!lol Faker#KR1`)")
        return

    game_name, tag = partes[1].split("#", 1)
    msg_cargando = await message.channel.send(f"🔍 Buscando a **{game_name}#{tag}**...")

    try:
        resultado = await obtener_elo(game_name, tag)

        if resultado is None:
            await msg_cargando.edit(content="❌ No encontré la cuenta. Revisá el Nombre#TAG y que sea de LAS (la2).")
            return

        league_data = resultado.get("league", [])

        stats_rank = next((l for l in league_data if l.get("queueType") == "RANKED_SOLO_5x5"), None)
        if not stats_rank:
            stats_rank = next((l for l in league_data if l.get("queueType") == "RANKED_FLEX_SR"), None)

        if not stats_rank:
            await msg_cargando.edit(content=f"🎮 **{game_name}#{tag}** no tiene partidas rankeadas en esta región.")
            return

        datos_finales = {
            "nombre": game_name,
            "tag": tag,
            "tier": stats_rank.get("tier", "UNRANKED"),
            "rank": stats_rank.get("rank", ""),
            "lp": stats_rank.get("leaguePoints", 0),
            "wins": stats_rank.get("wins", 0),
            "losses": stats_rank.get("losses", 0),
            "queue": "SoloQ" if stats_rank.get("queueType") == "RANKED_SOLO_5x5" else "Flex",
            "profile_icon_url": resultado.get("profile_icon_url"),
            "summoner_level": resultado.get("summoner_level"),
            "campeon_nombre": resultado.get("campeon_nombre"),
            "campeon_imagen": resultado.get("campeon_imagen"),
            "campeon_puntos": resultado.get("campeon_puntos"),
            "historial": resultado.get("historial", []),
        }

        embed = crear_embed_lol(datos_finales)
        await msg_cargando.delete()
        await message.channel.send(embed=embed)

    except Exception as e:
        print(f"❌ Error en handler de LoL: {e}")
        try:
            await msg_cargando.edit(content="❌ Hubo un fallo interno al procesar los datos de Riot.")
        except Exception:
            await message.channel.send("❌ Hubo un fallo crítico en el comando.")