from dotenv import load_dotenv
load_dotenv("keys.env")

import discord
import os
from discord.ext import commands
from events.on_message import on_message_handler
from features.profiles import cargar_perfiles
from memory.channels import cargar as cargar_canales
from memory.users import cargar as cargar_usuarios
from features.voice_handler import setup_voice_commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Registrar comandos de voz
setup_voice_commands(bot)

@bot.event
async def on_ready():
    cargar_perfiles()
    cargar_canales()
    cargar_usuarios()
    print(f"✅ Conectado como {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await on_message_handler(bot, message)

bot.run(os.getenv("DISCORD_TOKEN"))