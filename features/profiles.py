import json
from pathlib import Path

DATA_PATH = Path("data/profiles.json")
perfiles = {}

def cargar_perfiles():
    """Carga los perfiles desde el JSON y normaliza las claves faltantes."""
    global perfiles
    if DATA_PATH.exists() and DATA_PATH.stat().st_size > 0:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            perfiles.update(json.load(f))
    else:
        perfiles.clear()

    # Normalizar perfiles existentes para que no falten claves
    for user_id, perfil in perfiles.items():
        perfil.setdefault("nombre", f"Usuario {user_id}")
        perfil.setdefault("mensajes", 0)
        perfil.setdefault("nivel", 1)
        perfil.setdefault("rol", "Nuevo")
        perfil.setdefault("estilo", "Indefinido")
        perfil.setdefault("lol", None)

def guardar():
    """Guarda los perfiles en el JSON."""
    DATA_PATH.parent.mkdir(exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(perfiles, f, indent=4, ensure_ascii=False)

def actualizar_perfil(user):
    """Actualiza el perfil del usuario, sube nivel y asigna rol según actividad."""
    user_id = str(user.id)

    # Si el perfil no existe, crear con valores por defecto
    if user_id not in perfiles:
        perfiles[user_id] = {
            "nombre": user.name,
            "mensajes": 0,
            "nivel": 1,
            "rol": "Nuevo",
            "estilo": "Indefinido",
            "lol": None
        }

    # Normalizar claves por si falta algo en perfiles antiguos
    perfil = perfiles[user_id]
    perfil.setdefault("mensajes", 0)
    perfil.setdefault("nivel", 1)
    perfil.setdefault("rol", "Nuevo")
    perfil.setdefault("estilo", "Indefinido")
    perfil.setdefault("lol", None)

    # Actualizar mensajes
    perfil["mensajes"] += 1

    # Subir nivel cada 30 mensajes
    if perfil["mensajes"] % 30 == 0:
        perfil["nivel"] += 1

    # Asignar rol según nivel
    lvl = perfil["nivel"]
    if lvl >= 10:
        perfil["rol"] = "Veterano"
    elif lvl >= 5:
        perfil["rol"] = "Activo"
    else:
        perfil["rol"] = "Nuevo"

    guardar()

def aplicar_estilo(user_id, personalidad):
    """Aplica un estilo de personalidad al perfil de un usuario."""
    if user_id in perfiles and personalidad:
        perfiles[user_id]["estilo"] = (
            f"{personalidad.get('tono', 'Indefinido')} / "
            f"{personalidad.get('nivel_tecnico', 'Indefinido')} / "
            f"{personalidad.get('humor', 'Indefinido')}"
        )
        guardar()
