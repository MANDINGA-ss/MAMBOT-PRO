from collections import defaultdict
import json
from config import MEMORIA_CANALES_FILE, MAX_MENSAJES_CANAL
 
memoria_canales = defaultdict(list)
 
def cargar():
    if MEMORIA_CANALES_FILE.exists():
        with open(MEMORIA_CANALES_FILE, "r", encoding="utf-8") as f:
            memoria_canales.update(json.load(f))
 
def guardar():
    # Recortar cada canal antes de guardar para no crecer indefinidamente
    for canal_id in memoria_canales:
        memoria_canales[canal_id] = memoria_canales[canal_id][-MAX_MENSAJES_CANAL:]
 
    with open(MEMORIA_CANALES_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria_canales, f, ensure_ascii=False, indent=2)
 