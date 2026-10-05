import discord

def crear_embed_lol(datos):
    wins = datos.get("wins", 0)
    losses = datos.get("losses", 0)
    total = wins + losses
    winrate = round((wins / total) * 100, 1) if total > 0 else 0
    queue = datos.get("queue", "SoloQ")
    level = datos.get("summoner_level")

    titulo = f"🎮 {datos['nombre']}#{datos['tag']}"
    if level:
        titulo += f"  •  Nivel {level}"

    embed = discord.Embed(
        title=titulo,
        description=f"Estadísticas Ranked {queue}",
        color=0x1abc9c
    )

    if datos.get("profile_icon_url"):
        embed.set_thumbnail(url=datos["profile_icon_url"])

    embed.add_field(
        name="🏆 Rango",
        value=f"{datos['tier']} {datos['rank']} ({datos['lp']} LP)",
        inline=False
    )

    embed.add_field(
        name="📊 Victorias / Derrotas",
        value=f"{wins}W / {losses}L",
        inline=True
    )

    embed.add_field(
        name="🔥 Winrate",
        value=f"{winrate}%",
        inline=True
    )

    if datos.get("campeon_nombre"):
        puntos = datos.get("campeon_puntos", 0)
        puntos_fmt = f"{puntos:,}".replace(",", ".")
        embed.add_field(
            name="👑 Campeón más jugado",
            value=f"{datos['campeon_nombre']} ({puntos_fmt} pts)",
            inline=False
        )
        if datos.get("campeon_imagen"):
            embed.set_image(url=datos["campeon_imagen"])

    # Historial últimas 5 partidas
    historial = datos.get("historial", [])
    if historial:
        lineas = []
        for p in historial:
            resultado = "✅" if p["victoria"] else "❌"
            kda = f"{p['kills']}/{p['deaths']}/{p['assists']}"
            lineas.append(f"{resultado} **{p['campeon']}** {kda} — {p['duracion']}min")

        embed.add_field(
            name="📜 Últimas partidas (SoloQ)",
            value="\n".join(lineas),
            inline=False
        )

    embed.set_footer(text="Datos obtenidos desde Riot Games API")
    return embed