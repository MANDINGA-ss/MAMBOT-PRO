import asyncio
import io
import os
import tempfile
import struct
import wave
import discord
from discord.ext import commands
from groq import Groq
from features.voz import generar_audio
from ai.client import crear_completion
from memory.channels import memoria_canales

TRIGGER = "mambot"
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
conexiones_activas = {}

# ================= TRANSCRIPCIÓN =================

async def transcribir_audio(audio_bytes: bytes) -> str | None:
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        with open(tmp_path, "rb") as f:
            transcripcion = await asyncio.to_thread(
                client_groq.audio.transcriptions.create,
                model="whisper-large-v3",
                file=("audio.wav", f),
                language="es"
            )

        os.unlink(tmp_path)
        return transcripcion.text.strip()

    except Exception as e:
        print(f"🔥 Error transcribiendo: {e}")
        return None

# ================= RESPUESTA IA =================

async def generar_respuesta_voz(texto: str, canal_id: str) -> str:
    mensajes = [
        {
            "role": "system",
            "content": (
                "Tu nombre es MAMBOT. Sos una IA argentina en un canal de voz de Discord. "
                "Respondés de forma corta y concisa — máximo 2 oraciones — porque tu respuesta se va a leer en voz alta. "
                "Usás un tono informal argentino. Podés ser gracioso pero breve."
            )
        }
    ]
    historial = memoria_canales.get(canal_id, [])[-6:]
    mensajes.extend(historial)
    mensajes.append({"role": "user", "content": texto})

    try:
        completion = await asyncio.to_thread(crear_completion, mensajes)
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"🔥 Error generando respuesta: {e}")
        return "No pude procesar eso, intentá de nuevo."

# ================= GRABADOR DE AUDIO =================

class AudioGrabber(discord.VoiceClient):
    """Extiende VoiceClient para capturar audio entrante."""
    pass

class PCMRecorder:
    """Graba audio PCM de un usuario específico."""

    def __init__(self):
        self.frames = []
        self.recording = False

    def write(self, data):
        if self.recording:
            self.frames.append(data)

    def to_wav(self) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(48000)
            wf.writeframes(b''.join(self.frames))
        return buffer.getvalue()

    def clear(self):
        self.frames = []

# ================= COMANDOS =================

def setup_voice_commands(bot):

    @bot.command()
    async def unirse(ctx):
        if not ctx.author.voice:
            await ctx.send("❌ Tenés que estar en un canal de voz primero.")
            return

        canal_voz = ctx.author.voice.channel
        guild_id = ctx.guild.id

        if guild_id in conexiones_activas:
            try:
                await conexiones_activas[guild_id].disconnect()
            except Exception:
                pass

        try:
            vc = await canal_voz.connect()
            conexiones_activas[guild_id] = vc
            await ctx.send(
                f"🎙️ Me uní a **{canal_voz.name}**.\n"
                f"Usá `!escuchar` para que empiece a grabarte y `!procesar` para que responda."
            )
        except Exception as e:
            print(f"🔥 Error uniéndose: {e}")
            await ctx.send("❌ No pude unirme al canal de voz.")

    @bot.command()
    async def salir(ctx):
        guild_id = ctx.guild.id
        if guild_id not in conexiones_activas:
            await ctx.send("❌ No estoy en ningún canal de voz.")
            return

        vc = conexiones_activas.pop(guild_id)
        await vc.disconnect()
        await ctx.send("👋 Me fui del canal de voz.")

    @bot.command()
    async def escuchar(ctx):
        """Graba 5 segundos de audio y responde si detecta 'mambot'."""
        guild_id = ctx.guild.id

        if guild_id not in conexiones_activas:
            await ctx.send("❌ Primero usá `!unirse`.")
            return

        vc = conexiones_activas[guild_id]

        if not vc.is_connected():
            await ctx.send("❌ No estoy conectado al canal de voz.")
            return

        await ctx.send("🎙️ Escuchando 5 segundos... hablá ahora.")

        recorder = PCMRecorder()
        recorder.recording = True

        # Capturar audio crudo via recv
        frames = []
        try:
            for _ in range(250):  # 250 * 20ms = 5 segundos
                frame = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, vc.recv),
                    timeout=0.1
                )
                if frame:
                    frames.append(frame.pcm)
        except Exception:
            pass

        if not frames:
            await ctx.send("❌ No capturé audio. Asegurate de estar hablando.")
            return

        # Construir WAV
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(48000)
            wf.writeframes(b''.join(frames))
        audio_bytes = buffer.getvalue()

        # Transcribir
        await ctx.send("🔄 Transcribiendo...")
        texto = await transcribir_audio(audio_bytes)

        if not texto:
            await ctx.send("❌ No pude transcribir el audio.")
            return

        await ctx.send(f"🎙️ Escuché: *{texto}*")

        if TRIGGER not in texto.lower():
            await ctx.send(f"💬 *(no mencionaste '{TRIGGER}', no respondo)*")
            return

        # Generar respuesta
        respuesta = await generar_respuesta_voz(texto, str(ctx.channel.id))
        await ctx.send(f"🤖 {respuesta}")

        # Reproducir en voz
        buffer_audio = await generar_audio(respuesta)
        if buffer_audio and vc.is_connected():
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                f.write(buffer_audio.read())
                tmp_path = f.name

            vc.play(
                discord.FFmpegPCMAudio(tmp_path),
                after=lambda e: os.unlink(tmp_path) if os.path.exists(tmp_path) else None
            )