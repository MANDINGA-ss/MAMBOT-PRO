"""
MAMBOT - Asistente de voz standalone
Correr con: py -3.11 asistente.py

Flujo:
1. Escucha el micrófono constantemente
2. Cuando detecta voz, graba hasta que haya silencio
3. Manda el audio a Groq Whisper
4. Si el texto contiene "mambot", genera respuesta con LLaMA
5. Lee la respuesta con Edge TTS
"""

import asyncio
import io
import os
import tempfile
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
import edge_tts
from groq import Groq
from dotenv import load_dotenv

load_dotenv("keys.env")

# ================= CONFIG =================
TRIGGER = "mambot"
VOZ = "es-AR-ElenaNeural"
SAMPLE_RATE = 16000
UMBRAL_SILENCIO = 0.01       # sensibilidad del micrófono (bajar si no detecta, subir si hay ruido)
SEGUNDOS_SILENCIO = 1.5      # segundos de silencio para cortar la grabación
MAX_SEGUNDOS_GRABACION = 10  # máximo de grabación por turno

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
historial = []

# ================= UTILIDADES =================

def grabar_hasta_silencio() -> np.ndarray | None:
    """Graba audio del micrófono hasta detectar silencio."""
    print("🎙️ Escuchando...")

    frames = []
    frames_silencio = 0
    max_frames = int(SAMPLE_RATE * MAX_SEGUNDOS_GRABACION)
    frames_silencio_max = int(SAMPLE_RATE * SEGUNDOS_SILENCIO / 512)
    hablando = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32', blocksize=512) as stream:
        while True:
            frame, _ = stream.read(512)
            volumen = np.abs(frame).mean()

            if volumen > UMBRAL_SILENCIO:
                if not hablando:
                    print("🔴 Grabando...")
                    hablando = True
                frames.append(frame.copy())
                frames_silencio = 0
            elif hablando:
                frames.append(frame.copy())
                frames_silencio += 1
                if frames_silencio >= frames_silencio_max:
                    print("⏹️ Silencio detectado, procesando...")
                    break

            if len(frames) >= max_frames // 512:
                print("⏹️ Tiempo máximo alcanzado.")
                break

    if not frames:
        return None

    return np.concatenate(frames, axis=0)

def audio_a_wav(audio: np.ndarray) -> bytes:
    """Convierte numpy array a bytes WAV."""
    audio_int16 = (audio * 32767).astype(np.int16)
    buffer = io.BytesIO()
    wav.write(buffer, SAMPLE_RATE, audio_int16)
    return buffer.getvalue()

def transcribir(audio_bytes: bytes) -> str | None:
    """Transcribe audio con Groq Whisper."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=("audio.wav", f),
                language="es"
            )

        os.unlink(tmp_path)
        return result.text.strip()

    except Exception as e:
        print(f"🔥 Error transcribiendo: {e}")
        return None

def generar_respuesta(texto: str) -> str:
    """Genera respuesta con LLaMA via Groq."""
    global historial

    mensajes = [
        {
            "role": "system",
            "content": (
                "Tu nombre es MAMBOT. Sos un asistente de voz argentino. "
                "Respondés de forma corta y concisa — máximo 2-3 oraciones — "
                "porque tu respuesta se va a leer en voz alta. "
                "Usás un tono informal argentino. Podés ser gracioso pero breve. "
                "Nunca uses markdown, asteriscos ni listas — solo texto plano."
            )
        }
    ]

    mensajes.extend(historial[-6:])
    mensajes.append({"role": "user", "content": texto})

    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=mensajes
        )
        respuesta = completion.choices[0].message.content.strip()

        historial.append({"role": "user", "content": texto})
        historial.append({"role": "assistant", "content": respuesta})

        return respuesta

    except Exception as e:
        print(f"🔥 Error generando respuesta: {e}")
        return "No pude procesar eso, intentá de nuevo."

async def hablar(texto: str):
    """Lee el texto en voz alta con Edge TTS."""
    try:
        communicate = edge_tts.Communicate(texto, VOZ)
        buffer = io.BytesIO()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])

        buffer.seek(0)
        audio_bytes = buffer.read()

        # Reproducir con sounddevice
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        sample_rate, audio_data = wav.read(tmp_path)
        os.unlink(tmp_path)

        if audio_data.dtype == np.int16:
            audio_float = audio_data.astype(np.float32) / 32767
        else:
            audio_float = audio_data

        sd.play(audio_float, sample_rate)
        sd.wait()

    except Exception as e:
        print(f"🔥 Error reproduciendo audio: {e}")

# ================= LOOP PRINCIPAL =================

async def main():
    print("=" * 40)
    print("🤖 MAMBOT - Asistente de voz")
    print(f"   Palabra clave: '{TRIGGER}'")
    print(f"   Umbral micrófono: {UMBRAL_SILENCIO}")
    print("   Ctrl+C para salir")
    print("=" * 40)

    await hablar("Hola, soy MAMBOT. Estoy escuchando.")

    while True:
        try:
            audio = grabar_hasta_silencio()
            if audio is None:
                continue

            audio_bytes = audio_a_wav(audio)
            texto = transcribir(audio_bytes)

            if not texto:
                continue

            print(f"🎙️ Escuché: {texto}")

            if TRIGGER not in texto.lower():
                print(f"   (sin trigger '{TRIGGER}', ignorando)")
                continue

            respuesta = generar_respuesta(texto)
            print(f"🤖 MAMBOT: {respuesta}")

            await hablar(respuesta)

        except KeyboardInterrupt:
            print("\n👋 Cerrando MAMBOT...")
            break
        except Exception as e:
            print(f"🔥 Error en el loop: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(main())
