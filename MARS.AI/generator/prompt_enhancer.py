"""Potenciador de prompts local, sin modelos ni conexión.

Los modelos de Stable Diffusion entienden mejor el inglés. Este módulo:
1. Traduce términos frecuentes del español al inglés con un diccionario.
2. Añade descriptores de calidad, iluminación y composición si faltan.
No pretende ser un traductor completo: el texto que no reconoce se conserva.
"""
from __future__ import annotations

import re

_DICT = {
    # sujetos
    "panda": "panda", "guerrero": "warrior", "guerrera": "female warrior", "gato": "cat", "perro": "dog",
    "dragón": "dragon", "dragon": "dragon", "robot": "robot", "mujer": "woman", "hombre": "man",
    "niña": "girl", "niño": "boy", "chica": "young woman", "chico": "young man", "anciana": "old woman",
    "anciano": "old man", "caballero": "knight", "princesa": "princess", "astronauta": "astronaut",
    "zorro": "fox", "lobo": "wolf", "tigre": "tiger", "león": "lion", "búho": "owl", "conejo": "rabbit",
    "ballena": "whale", "criatura": "creature", "monstruo": "monster", "samurái": "samurai",
    # lugares
    "ciudad": "city", "bosque": "forest", "montaña": "mountain", "montañas": "mountains", "playa": "beach",
    "mar": "sea", "océano": "ocean", "desierto": "desert", "castillo": "castle", "casa": "house",
    "calle": "street", "callejón": "alley", "espacio": "outer space", "planeta": "planet", "lago": "lake",
    "río": "river", "cielo": "sky", "nubes": "clouds", "selva": "jungle", "pueblo": "village",
    # adjetivos
    "futurista": "futuristic", "japonesa": "japanese", "japonés": "japanese", "antiguo": "ancient",
    "antigua": "ancient", "mágico": "magical", "mágica": "magical", "oscuro": "dark", "oscura": "dark",
    "gigante": "giant", "pequeño": "small", "pequeña": "small", "hermoso": "beautiful", "hermosa": "beautiful",
    "abandonada": "abandoned", "abandonado": "abandoned", "brillante": "glowing", "dorado": "golden",
    "dorada": "golden", "rojo": "red", "roja": "red", "azul": "blue", "verde": "green", "negro": "black",
    "negra": "black", "blanco": "white", "blanca": "white", "morado": "purple", "morada": "purple",
    "lluvioso": "rainy", "nevado": "snowy", "épico": "epic", "épica": "epic",
    # escena / técnica
    "armadura": "armor", "espada": "sword", "noche": "night", "atardecer": "sunset", "amanecer": "sunrise",
    "lluvia": "rain", "niebla": "fog", "nieve": "snow", "fuego": "fire", "luz": "light",
    "iluminación": "lighting", "cinematográfica": "cinematic", "cinematográfico": "cinematic",
    "ultra": "ultra", "detallado": "detailed", "detallada": "detailed", "retrato": "portrait",
    "paisaje": "landscape", "flores": "flowers", "árboles": "trees", "estrellas": "stars", "luna": "moon",
    "sol": "sun", "volando": "flying", "corriendo": "running", "leyendo": "reading", "libro": "book",
    # conectores (se eliminan o traducen)
    "un": "a", "una": "a", "unos": "", "unas": "", "el": "the", "la": "the", "los": "the", "las": "the",
    "con": "with", "en": "in", "de": "of", "del": "of the", "y": "and", "sobre": "on", "bajo": "under",
    "entre": "among", "frente": "in front", "a": "", "al": "at the", "por": "", "para": "for",
}

_QUALITY = "masterpiece, best quality, highly detailed"
_LIGHT_WORDS = ("light", "lighting", "lit", "sunset", "sunrise", "night", "golden hour", "neon")
_COMPOSITION = "beautiful composition"


def translate_es_en(text: str) -> str:
    tokens = re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)
    out: list[str] = []
    for tok in tokens:
        low = tok.lower()
        if low in _DICT:
            if _DICT[low]:
                out.append(_DICT[low])
        else:
            out.append(tok)
    s = " ".join(out)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    return re.sub(r"\s{2,}", " ", s).strip()


def enhance_prompt(prompt: str, translate: bool = True) -> str:
    p = prompt.strip()
    if not p:
        return ""
    if translate:
        p = translate_es_en(p)
    low = p.lower()
    extras = []
    if "masterpiece" not in low and "best quality" not in low:
        extras.append(_QUALITY)
    if not any(w in low for w in _LIGHT_WORDS):
        extras.append("dramatic lighting")
    if "composition" not in low:
        extras.append(_COMPOSITION)
    if "sharp focus" not in low:
        extras.append("sharp focus")
    return ", ".join([p, *extras])
