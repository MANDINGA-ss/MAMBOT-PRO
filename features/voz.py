import asyncio
import io
import re
import discord
import edge_tts

VOZ = "es-AR-ElenaNeural"

async def generar_audio(texto: str) -> io.BytesIO | None:
    """Genera audio a partir de texto y devuelve un buffer. No manda nada al canal."""
    try:
        # Limpiar el texto de markdown y tags de GIF antes de leerlo
        texto_limpio = re.sub(r"\[GIF:.*?\]", "", texto)
        texto_limpio = re.sub(r"\*+", "", texto_limpio)
        texto_limpio = re.sub(r"#+\s?", "", texto_limpio)
        texto_limpio = texto_limpio.strip()

        if not texto_limpio:
            return None

        # Truncar si es muy largo para no generar audios eternos
        if len(texto_limpio) > 500:
            texto_limpio = texto_limpio[:500] + "..."

        communicate = edge_tts.Communicate(texto_limpio, VOZ)
        buffer = io.BytesIO()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])

        buffer.seek(0)
        return buffer if buffer.getbuffer().nbytes > 0 else None

    except Exception as e:
        print(f"🔥 Error generando audio: {e}")
        return None


async def generar_voz(canal, texto: str):
    """Comando !voz texto — solo TTS sin IA."""
    if len(texto) > 500:
        await canal.send("❌ Máximo 500 caracteres.")
        return

    msg_cargando = await canal.send("🎙️ Generando audio...")

    buffer = await generar_audio(texto)

    if not buffer:
        await msg_cargando.edit(content="❌ No se pudo generar el audio.")
        return

    archivo = discord.File(fp=buffer, filename="voice-message.ogg")
    await msg_cargando.delete()
    await canal.send(file=archivo)