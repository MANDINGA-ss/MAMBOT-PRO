def es_pedido_lol(texto):
    claves = ["lol", "rank", "elo", "perfil", "opgg"]
    return any(c in texto for c in claves)

def extraer_nombre(texto):
    partes = texto.split()
    return partes[-1]  # simple: "mambot rank faker"
