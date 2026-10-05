from features.profiles import perfiles, guardar

async def vincular_lol(message):
    partes = message.content.strip().split(" ")

    # Formato esperado: !lol vincular lol Nombre#TAG
    # o desde on_message: mambot vincular lol Nombre#TAG
    cuenta = next((p for p in partes if "#" in p), None)

    if not cuenta:
        await message.channel.send("❌ Usá el formato: `!lol vincular Nombre#TAG`")
        return

    try:
        nombre, tag = cuenta.split("#", 1)
    except ValueError:
        await message.channel.send("❌ Usá el formato: `!lol vincular Nombre#TAG`")
        return

    user_id = str(message.author.id)

    if user_id not in perfiles:
        perfiles[user_id] = {}

    perfiles[user_id]["lol"] = {
        "summoner": nombre,
        "tag": tag,
        "region": "la2"
    }

    guardar()

    await message.channel.send(
        f"🎮 Cuenta de LoL vinculada: **{nombre}#{tag}** (LAS)"
    )