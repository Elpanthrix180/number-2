"""Las 20 categorías de estilo de MARS.AI.

Cada estilo añade palabras clave al prompt y al negative prompt, propone
ajustes por defecto y trae prompts de ejemplo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.i18n import N_

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
    Style(N_("Fotorealismo"), "📷",
          "photorealistic, ultra realistic photo, 35mm lens, natural lighting, sharp focus, high detail, 8k",
          "cartoon, anime, painting, illustration, 3d render, cgi", 30, 6.5, "3:4",
          (N_("Retrato de una anciana pescadora en un puerto al amanecer"),
           N_("Taza de café humeante sobre una mesa de madera, luz de ventana"))),
    Style(N_("Anime"), "🌸",
          "anime style, cel shading, vibrant colors, detailed eyes, studio anime key visual",
          "photorealistic, 3d, realistic skin", 25, 7.0, "9:16",
          (N_("Chica samurái bajo cerezos en flor, viento"),
           N_("Chico con chaqueta de cuero en una azotea de Tokio de noche"))),
    Style(N_("Manga"), "🖋️",
          "manga style, black and white, screentone, ink lines, dramatic panel composition",
          "color, photorealistic, 3d", 25, 7.5, "3:4",
          (N_("Detective en un callejón lluvioso, viñeta dramática"),
           N_("Duelo de espadachines en un tejado"))),
    Style(N_("Dibujos animados"), "🎨",
          "cartoon style, bold outlines, flat colors, playful, clean vector look",
          "photorealistic, gritty, realistic", 22, 7.0, "1:1",
          (N_("Un perro con gafas de sol surfeando"), N_("Un dragón simpático vendiendo helados"))),
    Style(N_("Animación 3D"), "🧸",
          "3d animated movie style, stylized characters, soft global illumination, subsurface scattering, "
          "expressive face, octane render",
          "photo, 2d, sketch, flat", 28, 7.0, "16:9",
          (N_("Un robot pequeño regando plantas en Marte"), N_("Una familia de zorros cenando en su madriguera"))),
    Style(N_("Fantasía"), "🐉",
          "epic fantasy art, magical atmosphere, intricate details, dramatic lighting, concept art",
          "modern, mundane", 30, 7.5, "16:9",
          (N_("Castillo flotante entre nubes doradas"), N_("Elfa arquera en un bosque luminoso"))),
    Style(N_("Ciencia ficción"), "🚀",
          "science fiction, futuristic, neon lights, high-tech, cinematic, concept art",
          "medieval, rustic", 30, 7.5, "16:9",
          (N_("Ciudad cyberpunk con coches voladores bajo la lluvia"),
           N_("Astronauta frente a un planeta con anillos"))),
    Style(N_("Terror"), "🕯️",
          "horror, dark atmosphere, eerie, ominous fog, dim lighting, unsettling, cinematic",
          "cheerful, bright, cute", 30, 7.5, "3:4",
          (N_("Casa abandonada en el bosque con una luz en la ventana"),
           N_("Pasillo de hospital antiguo con niebla"))),
    Style(N_("Arte digital"), "💠",
          "digital art, trending on artstation, highly detailed, vibrant, sharp",
          "", 25, 7.0, "1:1",
          (N_("Ballena cósmica nadando entre galaxias"), N_("Tigre hecho de cristales de colores"))),
    Style(N_("Pintura artística"), "🖼️",
          "oil painting, visible brush strokes, impasto, classical composition, fine art, canvas texture",
          "photo, 3d render, digital", 30, 7.5, "4:3",
          (N_("Campo de girasoles al atardecer"), N_("Retrato de un caballero renacentista"))),
    Style(N_("Acuarela"), "💧",
          "watercolor painting, soft washes, paper texture, delicate, bleeding colors, pastel tones",
          "photo, 3d, harsh lines", 25, 7.0, "4:3",
          (N_("Pueblo costero mediterráneo"), N_("Ramo de flores silvestres en un jarrón"))),
    Style(N_("Caricaturas"), "😜",
          "caricature, exaggerated features, humorous, expressive, editorial illustration",
          "photorealistic", 25, 7.0, "3:4",
          (N_("Chef con un bigote enorme y gorro gigante"), N_("Científico despeinado con gafas enormes"))),
    Style(N_("Retratos"), "👤",
          "portrait, headshot, detailed face, studio lighting, shallow depth of field, bokeh",
          "multiple people, cropped head, deformed face", 30, 6.5, "3:4",
          (N_("Mujer con pecas y pelo rizado, luz suave"), N_("Hombre mayor con barba blanca, luz de Rembrandt"))),
    Style(N_("Superhéroes"), "🦸",
          "superhero, comic book style, dynamic pose, heroic, dramatic lighting, cape flowing",
          "", 28, 7.5, "9:16",
          (N_("Superheroína volando sobre una metrópolis"), N_("Héroe con armadura de energía azul"))),
    Style(N_("Criaturas y monstruos"), "👹",
          "creature design, monster, highly detailed anatomy, concept art, dramatic",
          "cute, cartoon", 30, 7.5, "1:1",
          (N_("Gólem de musgo en un pantano"), N_("Criatura marina bioluminiscente gigante"))),
    Style(N_("Paisajes"), "🏔️",
          "landscape photography, wide angle, golden hour, breathtaking scenery, high detail",
          "people, text", 30, 7.0, "16:9",
          (N_("Fiordo noruego con aurora boreal"), N_("Desierto con dunas rojas al atardecer"))),
    Style(N_("Arquitectura"), "🏛️",
          "architectural photography, modern architecture, clean lines, realistic materials, wide shot",
          "people, distorted perspective", 30, 7.0, "16:9",
          (N_("Casa minimalista de hormigón sobre un acantilado"), N_("Biblioteca futurista llena de plantas"))),
    Style(N_("Diseño de productos"), "📦",
          "product photography, studio lighting, clean background, commercial, high detail, centered",
          "clutter, people, text", 28, 7.0, "1:1",
          (N_("Zapatillas deportivas futuristas flotando"), N_("Botella de perfume de cristal sobre mármol"))),
    Style(N_("Logotipos"), "🔷",
          "logo design, minimalist, vector, flat, simple shapes, white background, iconic",
          "photo, realistic, complex background, gradient noise", 25, 8.0, "1:1",
          (N_("Logo de una cafetería con un búho"), N_("Logo minimalista de una startup espacial"))),
    Style(N_("Ilustraciones infantiles"), "🧒",
          "children's book illustration, whimsical, soft colors, friendly, storybook style",
          "scary, violent, realistic, dark", 25, 7.0, "4:3",
          (N_("Un conejo leyendo un libro bajo una seta"), N_("Niña y su gato explorando la luna"))),
]

NONE_STYLE = Style(N_("Ninguno"), "✨", "", "", 25, 7.0, "1:1", ())
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
