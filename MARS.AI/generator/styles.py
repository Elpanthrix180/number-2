"""Las 20 categorías de estilo de MARS.AI.

Cada estilo añade palabras clave al prompt y al negative prompt, propone
ajustes por defecto y trae prompts de ejemplo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

BASE_NEGATIVE = "blurry, low quality, lowres, jpeg artifacts, watermark, signature, text, deformed"


@dataclass(frozen=True)
class Style:
    name: str
    icon: str
    positive: str
    negative: str = ""
    steps: int = 25
    cfg: float = 7.0
    aspect: str = "1:1"
    examples: tuple[str, ...] = field(default_factory=tuple)


STYLES: list[Style] = [
    Style("Fotorealismo", "📷",
          "photorealistic, ultra realistic photo, 35mm lens, natural lighting, sharp focus, high detail, 8k",
          "cartoon, anime, painting, illustration, 3d render, cgi", 30, 6.5, "3:4",
          ("Retrato de una anciana pescadora en un puerto al amanecer",
           "Taza de café humeante sobre una mesa de madera, luz de ventana")),
    Style("Anime", "🌸",
          "anime style, cel shading, vibrant colors, detailed eyes, studio anime key visual",
          "photorealistic, 3d, realistic skin", 25, 7.0, "9:16",
          ("Chica samurái bajo cerezos en flor, viento",
           "Chico con chaqueta de cuero en una azotea de Tokio de noche")),
    Style("Manga", "🖋️",
          "manga style, black and white, screentone, ink lines, dramatic panel composition",
          "color, photorealistic, 3d", 25, 7.5, "3:4",
          ("Detective en un callejón lluvioso, viñeta dramática",
           "Duelo de espadachines en un tejado")),
    Style("Dibujos animados", "🎨",
          "cartoon style, bold outlines, flat colors, playful, clean vector look",
          "photorealistic, gritty, realistic", 22, 7.0, "1:1",
          ("Un perro con gafas de sol surfeando", "Un dragón simpático vendiendo helados")),
    Style("Animación 3D", "🧸",
          "3d animated movie style, stylized characters, soft global illumination, subsurface scattering, "
          "expressive face, octane render",
          "photo, 2d, sketch, flat", 28, 7.0, "16:9",
          ("Un robot pequeño regando plantas en Marte", "Una familia de zorros cenando en su madriguera")),
    Style("Fantasía", "🐉",
          "epic fantasy art, magical atmosphere, intricate details, dramatic lighting, concept art",
          "modern, mundane", 30, 7.5, "16:9",
          ("Castillo flotante entre nubes doradas", "Elfa arquera en un bosque luminoso")),
    Style("Ciencia ficción", "🚀",
          "science fiction, futuristic, neon lights, high-tech, cinematic, concept art",
          "medieval, rustic", 30, 7.5, "16:9",
          ("Ciudad cyberpunk con coches voladores bajo la lluvia",
           "Astronauta frente a un planeta con anillos")),
    Style("Terror", "🕯️",
          "horror, dark atmosphere, eerie, ominous fog, dim lighting, unsettling, cinematic",
          "cheerful, bright, cute", 30, 7.5, "3:4",
          ("Casa abandonada en el bosque con una luz en la ventana",
           "Pasillo de hospital antiguo con niebla")),
    Style("Arte digital", "💠",
          "digital art, trending on artstation, highly detailed, vibrant, sharp",
          "", 25, 7.0, "1:1",
          ("Ballena cósmica nadando entre galaxias", "Tigre hecho de cristales de colores")),
    Style("Pintura artística", "🖼️",
          "oil painting, visible brush strokes, impasto, classical composition, fine art, canvas texture",
          "photo, 3d render, digital", 30, 7.5, "4:3",
          ("Campo de girasoles al atardecer", "Retrato de un caballero renacentista")),
    Style("Acuarela", "💧",
          "watercolor painting, soft washes, paper texture, delicate, bleeding colors, pastel tones",
          "photo, 3d, harsh lines", 25, 7.0, "4:3",
          ("Pueblo costero mediterráneo", "Ramo de flores silvestres en un jarrón")),
    Style("Caricaturas", "😜",
          "caricature, exaggerated features, humorous, expressive, editorial illustration",
          "photorealistic", 25, 7.0, "3:4",
          ("Chef con un bigote enorme y gorro gigante", "Científico despeinado con gafas enormes")),
    Style("Retratos", "👤",
          "portrait, headshot, detailed face, studio lighting, shallow depth of field, bokeh",
          "multiple people, cropped head, deformed face", 30, 6.5, "3:4",
          ("Mujer con pecas y pelo rizado, luz suave", "Hombre mayor con barba blanca, luz de Rembrandt")),
    Style("Superhéroes", "🦸",
          "superhero, comic book style, dynamic pose, heroic, dramatic lighting, cape flowing",
          "", 28, 7.5, "9:16",
          ("Superheroína volando sobre una metrópolis", "Héroe con armadura de energía azul")),
    Style("Criaturas y monstruos", "👹",
          "creature design, monster, highly detailed anatomy, concept art, dramatic",
          "cute, cartoon", 30, 7.5, "1:1",
          ("Gólem de musgo en un pantano", "Criatura marina bioluminiscente gigante")),
    Style("Paisajes", "🏔️",
          "landscape photography, wide angle, golden hour, breathtaking scenery, high detail",
          "people, text", 30, 7.0, "16:9",
          ("Fiordo noruego con aurora boreal", "Desierto con dunas rojas al atardecer")),
    Style("Arquitectura", "🏛️",
          "architectural photography, modern architecture, clean lines, realistic materials, wide shot",
          "people, distorted perspective", 30, 7.0, "16:9",
          ("Casa minimalista de hormigón sobre un acantilado", "Biblioteca futurista llena de plantas")),
    Style("Diseño de productos", "📦",
          "product photography, studio lighting, clean background, commercial, high detail, centered",
          "clutter, people, text", 28, 7.0, "1:1",
          ("Zapatillas deportivas futuristas flotando", "Botella de perfume de cristal sobre mármol")),
    Style("Logotipos", "🔷",
          "logo design, minimalist, vector, flat, simple shapes, white background, iconic",
          "photo, realistic, complex background, gradient noise", 25, 8.0, "1:1",
          ("Logo de una cafetería con un búho", "Logo minimalista de una startup espacial")),
    Style("Ilustraciones infantiles", "🧒",
          "children's book illustration, whimsical, soft colors, friendly, storybook style",
          "scary, violent, realistic, dark", 25, 7.0, "4:3",
          ("Un conejo leyendo un libro bajo una seta", "Niña y su gato explorando la luna")),
]

NONE_STYLE = Style("Ninguno", "✨", "", "", 25, 7.0, "1:1", ())
_BY_NAME = {s.name: s for s in [NONE_STYLE, *STYLES]}


def style_names() -> list[str]:
    return [NONE_STYLE.name, *[s.name for s in STYLES]]


def get_style(name: str | None) -> Style:
    return _BY_NAME.get(name or "", NONE_STYLE)


def apply_style(prompt: str, negative: str, style_name: str | None) -> tuple[str, str]:
    """Devuelve (prompt, negative) con las palabras clave del estilo añadidas."""
    st = get_style(style_name)
    p = prompt.strip()
    if st.positive:
        p = f"{p}, {st.positive}" if p else st.positive
    negs = [n for n in (negative.strip(), st.negative, BASE_NEGATIVE) if n]
    return p, ", ".join(negs)
