import os
from groq import Groq

def crear_completion(mensajes):
    # Leer la key en cada llamada para asegurarse de que el .env ya fue cargado
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    try:
        return client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=mensajes
        )
    except Exception as e:
        print(f"⚠️ Fallback activado: {e}")
        return client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=mensajes
        )