from pathlib import Path
import os

# límites
MAX_MENSAJES_CANAL = 200
MAX_MENSAJES_USUARIO = 100


# archivos
MEMORIA_CANALES_FILE = Path("memoria_canales.json")
MEMORIA_USUARIOS_FILE = Path("memoria_usuarios.json")
BASE_DIR = Path(__file__).resolve().parent
PERFILES_FILE = BASE_DIR / "data" / "perfiles.json"
PERSONALIDAD_FILE = Path("personalidad.json")

# API KEYS
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
