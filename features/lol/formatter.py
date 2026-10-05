def formatear_stats(nombre, nivel, ranks):
    if not ranks:
        return f"🎮 **{nombre}**\nNivel {nivel}\nNo rankeado (o escondiendo elo 👀)"

    r = ranks[0]
    return (
        f"🎮 **Perfil LoL de {nombre}**\n"
        f"🏆 {r['tier']} {r['rank']} ({r['leaguePoints']} LP)\n"
        f"✅ Winrate: {int(r['wins'] / (r['wins'] + r['losses']) * 100)}%\n"
        f"📊 {r['wins']}W / {r['losses']}L"
    )
