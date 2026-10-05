from collections import defaultdict
import json
from config import MEMORIA_USUARIOS_FILE, MAX_MENSAJES_USUARIO
 
memoria_usuarios = defaultdict(list)
 
def cargar():
    if MEMORIA_USUARIOS_FILE.exists():
        with open(MEMORIA_USUARIOS_FILE, "r", encoding="utf-8") as f:
            memoria_usuarios.update(json.load(f))
 
def guardar():
    # Recortar cada usuario antes de guardar para no crecer indefinidamente
    for user_id in memoria_usuarios:
        memoria_usuarios[user_id] = memoria_usuarios[user_id][-MAX_MENSAJES_USUARIO:]
 
    with open(MEMORIA_USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria_usuarios, f, ensure_ascii=False, indent=2)