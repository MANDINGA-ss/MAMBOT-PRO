import json
import asyncio
from ai.client import crear_completion
from memory.users import memoria_usuarios
 
async def analizar_personalidad(user_id):
    recuerdos = memoria_usuarios.get(user_id, [])
    if len(recuerdos) < 10:
        return None
 
    mensajes = [
        {
            "role": "system",
            "content": (
                "Analizá el estilo del usuario y devolvé SOLO JSON sin ningún texto adicional:\n"
                "{\"tono\": ..., \"nivel_tecnico\": ..., \"humor\": ..., \"actitud\": ...}\n"
                "Valores posibles:\n"
                "tono: formal | informal\n"
                "nivel_tecnico: bajo | medio | alto\n"
                "humor: bajo | medio | alto\n"
                "actitud: tranquila | impulsiva | confrontativa"
            )
        },
        {
            "role": "user",
            "content": "\n".join(m["content"] for m in recuerdos[-20:])
        }
    ]
 
    try:
        # Groq es síncrono — lo corremos en un thread para no bloquear el event loop
        completion = await asyncio.to_thread(crear_completion, mensajes)
        contenido = completion.choices[0].message.content.strip()
 
        # Limpiar posibles backticks que el modelo agregue
        contenido = contenido.strip("`").removeprefix("json").strip()
 
        return json.loads(contenido)
    except Exception as e:
        print(f"⚠️ Error analizando personalidad: {e}")
        return None
 