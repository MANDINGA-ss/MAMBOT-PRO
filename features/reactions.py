import random

# emojis posibles por tipo
REACCIONES = {
    "humor": ["😂", "🤣", "💀"],
    "enojo": ["😬", "👀", "🫣"],
    "bardeo": ["💀", "🔥"],
    "triste": ["😔", "🫂"],
    "random": ["🤨", "😶", "🗿"]
}

PALABRAS_HUMOR = ["jaja", "lol", "xd", "lmao", "ajaja"]
PALABRAS_BARDEO = ["boludo", "pelotudo", "gil", "tarado"]
PALABRAS_ENOJO = ["odio", "mierda", "cansado", "harto"]

def detectar_tipo(texto: str) -> str:
    t = texto.lower()

    if any(p in t for p in PALABRAS_HUMOR):
        return "humor"
    if any(p in t for p in PALABRAS_BARDEO):
        return "bardeo"
    if any(p in t for p in PALABRAS_ENOJO):
        return "enojo"

    return "random"


async def reaccionar_si_corresponde(message) -> bool:
    """
    Devuelve True si reaccionó (y quizá no haga falta responder)
    """

    # probabilidad base
    if random.random() > 0.35:  # 35% de chance
        return False

    tipo = detectar_tipo(message.content)
    emoji = random.choice(REACCIONES.get(tipo, REACCIONES["random"]))

    try:
        await message.add_reaction(emoji)
        return True
    except:
        return False
