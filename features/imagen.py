import aiohttp
import asyncio
import io
import random
import urllib.parse
import discord
import os
import time
from ai.client import crear_completion
from collections import defaultdict

# ================= RATE LIMITING =================
COOLDOWN_SEGUNDOS = 60      # 1 minuto entre imágenes por usuario
LIMITE_DIARIO = 5           # máximo 5 imágenes por día por usuario

_ultimo_uso = {}            # user_id -> timestamp último uso
_contador_diario = defaultdict(lambda: {"count": 0, "fecha": None})  # user_id -> {count, fecha}

def verificar_limite(user_id: str) -> tuple[bool, str]:
    """
    Devuelve (puede_generar, mensaje_error)
    """
    from datetime import date

    hoy = str(date.today())

    # Resetear contador si es un día nuevo
    if _contador_diario[user_id]["fecha"] != hoy:
        _contador_diario[user_id] = {"count": 0, "fecha": hoy}

    # Verificar límite diario
    if _contador_diario[user_id]["count"] >= LIMITE_DIARIO:
        return False, f"❌ Llegaste al límite de {LIMITE_DIARIO} imágenes por día. Volvé mañana."

    # Verificar cooldown
    ultimo = _ultimo_uso.get(user_id, 0)
    tiempo_restante = COOLDOWN_SEGUNDOS - (time.time() - ultimo)
    if tiempo_restante > 0:
        return False, f"⏳ Esperá {int(tiempo_restante)} segundos antes de generar otra imagen."

    return True, ""

def registrar_uso(user_id: str):
    _ultimo_uso[user_id] = time.time()
    _contador_diario[user_id]["count"] += 1

# ================= GENERACIÓN =================

async def traducir_prompt(prompt: str) -> str:
    try:
        mensajes = [
            {
                "role": "system",
                "content": "Translate the following image generation prompt to English. Return ONLY the translated prompt, nothing else."
            },
            {"role": "user", "content": prompt}
        ]
        completion = await asyncio.to_thread(crear_completion, mensajes)
        return completion.choices[0].message.content.strip()
    except Exception:
        return prompt

async def generar_imagen(canal, prompt: str, user_id: str):
    # Verificar límites antes de hacer cualquier request
    puede, error_msg = verificar_limite(user_id)
    if not puede:
        await canal.send(error_msg)
        return

    msg_cargando = await canal.send(f"🎨 Generando imagen: *{prompt}*...")

    try:
        api_key = os.getenv("POLLINATIONS_API_KEY")
        prompt_en = await traducir_prompt(prompt)
        prompt_encoded = urllib.parse.quote(prompt_en.strip())
        seed = random.randint(1, 999999)

        url = (
            f"https://gen.pollinations.ai/image/{prompt_encoded}"
            f"?model=flux&width=1024&height=1024&seed={seed}&enhance=false&key={api_key}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=90)) as r:
                content_type = r.headers.get("Content-Type", "")

                if r.status != 200 or "image" not in content_type:
                    texto_error = await r.text()
                    print(f"⚠️ Pollinations error {r.status}: {texto_error[:200]}")
                    await msg_cargando.edit(content="❌ No pude generar la imagen. Intentá de nuevo.")
                    return

                imagen_bytes = await r.read()

        # Registrar uso solo si la generación fue exitosa
        registrar_uso(user_id)

        restantes = LIMITE_DIARIO - _contador_diario[user_id]["count"]

        archivo = discord.File(fp=io.BytesIO(imagen_bytes), filename="imagen.png")
        embed = discord.Embed(description=f"🎨 *{prompt}*", color=0x9b59b6)
        embed.set_image(url="attachment://imagen.png")
        embed.set_footer(text=f"Generado con Pollinations.AI  •  Te quedan {restantes} imágenes hoy")

        await msg_cargando.delete()
        await canal.send(file=archivo, embed=embed)

    except asyncio.TimeoutError:
        await msg_cargando.edit(content="❌ Tardó demasiado. Intentá en un momento.")
    except Exception as e:
        print(f"🔥 Error generando imagen: {e}")
        await msg_cargando.edit(content="❌ Error inesperado generando la imagen.")