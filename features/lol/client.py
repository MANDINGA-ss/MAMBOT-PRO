import os
import requests

API_KEY = os.getenv("RIOT_API_KEY")
BASE_URL = "https://la2.api.riotgames.com"  # Argentina / LAS

HEADERS = {
    "X-Riot-Token": API_KEY
}

def obtener_summoner(nombre):
    url = f"{BASE_URL}/lol/summoner/v4/summoners/by-name/{nombre}"
    r = requests.get(url, headers=HEADERS)
    return r.json() if r.status_code == 200 else None

def obtener_rank(summoner_id):
    url = f"{BASE_URL}/lol/league/v4/entries/by-summoner/{summoner_id}"
    r = requests.get(url, headers=HEADERS)
    return r.json() if r.status_code == 200 else []
