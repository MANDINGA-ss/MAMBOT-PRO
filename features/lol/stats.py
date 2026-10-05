import aiohttp
import os
import urllib.parse

async def obtener_version_ddragon(session):
    url = "https://ddragon.leagueoflegends.com/api/versions.json"
    async with session.get(url) as r:
        if r.status == 200:
            versions = await r.json()
            return versions[0]
    return "15.1.1"

async def obtener_nombre_campeon(session, champion_id, version):
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/es_AR/champion.json"
    async with session.get(url) as r:
        if r.status != 200:
            return None, None
        data = await r.json()
        for nombre, info in data["data"].items():
            if int(info["key"]) == champion_id:
                imagen = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{info['image']['full']}"
                return info["name"], imagen
    return None, None

async def obtener_historial(session, puuid, headers, version, champion_map):
    """Obtiene las últimas 5 partidas ranked del jugador."""
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&count=5"
    async with session.get(url, headers=headers) as r:
        if r.status != 200:
            return []
        match_ids = await r.json()

    partidas = []
    for match_id in match_ids:
        url_match = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"
        async with session.get(url_match, headers=headers) as r:
            if r.status != 200:
                continue
            data = await r.json()

        # Buscar al jugador en la partida
        participantes = data["info"]["participants"]
        jugador = next((p for p in participantes if p["puuid"] == puuid), None)
        if not jugador:
            continue

        champion_id = jugador["championId"]
        champion_name = champion_map.get(champion_id, f"Campeón {champion_id}")
        duracion = data["info"]["gameDuration"] // 60  # en minutos

        partidas.append({
            "campeon": champion_name,
            "victoria": jugador["win"],
            "kills": jugador["kills"],
            "deaths": jugador["deaths"],
            "assists": jugador["assists"],
            "duracion": duracion,
        })

    return partidas

async def obtener_elo(game_name: str, tag: str):
    api_key = os.getenv("RIOT_API_KEY")
    headers = {"X-Riot-Token": api_key}

    name_encoded = urllib.parse.quote(game_name.strip())
    tag_encoded = urllib.parse.quote(tag.strip())

    async with aiohttp.ClientSession() as session:
        try:
            # 1. Account-V1 — PUUID
            url_acc = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name_encoded}/{tag_encoded}"
            async with session.get(url_acc, headers=headers) as r:
                if r.status != 200:
                    print(f"⚠️ Account-V1 falló: {r.status}")
                    return None
                account = await r.json()
                puuid = account.get("puuid")

            # 2. Summoner-V4 — ícono y nivel
            url_sum = f"https://la2.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
            async with session.get(url_sum, headers=headers) as r:
                summoner = await r.json() if r.status == 200 else {}
                profile_icon_id = summoner.get("profileIconId")
                summoner_level = summoner.get("summonerLevel")

            # 3. League-V4 — elo
            url_league = f"https://la2.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
            async with session.get(url_league, headers=headers) as r:
                if r.status != 200:
                    print(f"⚠️ League-V4 falló: {r.status}")
                    return None
                league_data = await r.json()

            # 4. Champion-Mastery-V4 — campeón más jugado
            url_mastery = f"https://la2.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count=1"
            async with session.get(url_mastery, headers=headers) as r:
                mastery_data = await r.json() if r.status == 200 else []

            # 5. Data Dragon — versión y datos de campeones
            version = await obtener_version_ddragon(session)
            profile_icon_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/profileicon/{profile_icon_id}.png" if profile_icon_id else None

            campeon_nombre = None
            campeon_imagen = None
            campeon_puntos = None
            champion_map = {}

            # Cargar mapa de id -> nombre para el historial
            url_champs = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/es_AR/champion.json"
            async with session.get(url_champs) as r:
                if r.status == 200:
                    champ_data = await r.json()
                    for nombre, info in champ_data["data"].items():
                        champion_map[int(info["key"])] = info["name"]

            if mastery_data:
                champion_id = mastery_data[0].get("championId")
                campeon_puntos = mastery_data[0].get("championPoints", 0)
                campeon_nombre = champion_map.get(champion_id)
                if campeon_nombre:
                    champ_key = next((k for k, v in champ_data["data"].items() if v["name"] == campeon_nombre), None)
                    if champ_key:
                        campeon_imagen = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champ_data['data'][champ_key]['image']['full']}"

            # 6. Match-V5 — historial últimas 5 partidas ranked
            historial = await obtener_historial(session, puuid, headers, version, champion_map)

            return {
                "league": league_data,
                "profile_icon_url": profile_icon_url,
                "summoner_level": summoner_level,
                "campeon_nombre": campeon_nombre,
                "campeon_imagen": campeon_imagen,
                "campeon_puntos": campeon_puntos,
                "historial": historial,
            }

        except Exception as e:
            print(f"🔥 Error en stats: {e}")
            return None