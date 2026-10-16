"""Genera las texturas pixel art de Panthrix Jobs (todos los uniformes).
Uso: python tools/generar_texturas.py  (requiere Pillow: pip install pillow)
Plantilla de armadura 64x32 (formato clasico de skin de Minecraft)."""
from pathlib import Path
import sys
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent / "src/main/resources/assets/panthrixjobs/textures"
ARMOR = ROOT / "models/armor"
ITEM = ROOT / "item"

NAVY = (28, 38, 74, 255)
NAVY_D = (18, 25, 52, 255)
NAVY_L = (44, 58, 104, 255)
BLACK = (24, 24, 28, 255)
BLACK_L = (44, 44, 50, 255)
GOLD = (222, 180, 60, 255)
SILVER = (196, 200, 210, 255)
WHITE = (236, 236, 240, 255)
OUT = (10, 12, 26, 255)


def rect(img, x, y, w, h, c):
    for i in range(x, x + w):
        for j in range(y, y + h):
            img.putpixel((i, j), c)


def shade(img, x, y, w, h, base, dark, light):
    """Relleno con borde inferior oscuro y superior claro, para dar volumen."""
    rect(img, x, y, w, h, base)
    rect(img, x, y, w, 1, light)
    rect(img, x, y + h - 1, w, 1, dark)


def box(img, ox, oy, w, h, d, base, dark, light):
    """Rellena todas las caras de una caja UV (top, bottom, right, front, left, back)."""
    rect(img, ox + d, oy, w, d, light)            # arriba
    rect(img, ox + d + w, oy, w, d, dark)         # abajo
    shade(img, ox, oy + d, d, h, base, dark, light)            # derecha
    shade(img, ox + d, oy + d, w, h, base, dark, light)        # frente
    shade(img, ox + d + w, oy + d, d, h, base, dark, light)    # izquierda
    shade(img, ox + 2 * d + w, oy + d, w, h, base, dark, light)  # espalda


def layer1():
    img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    # --- Gorra (cabeza: caja en 0,0 de 8x8x8). Solo la parte superior de la cabeza.
    rect(img, 8, 0, 8, 8, NAVY)                     # copa
    rect(img, 9, 1, 6, 6, NAVY_L)
    for fx in (0, 8, 16, 24):                       # 4 caras laterales: 3 filas de gorra
        rect(img, fx, 8, 8, 2, NAVY)
        rect(img, fx, 10, 8, 1, BLACK)              # cinta negra
    rect(img, 8, 11, 8, 1, BLACK_L)                 # visera (frente)
    rect(img, 11, 8, 2, 2, GOLD)                    # placa dorada
    rect(img, 12, 8, 1, 1, (255, 222, 120, 255))
    # --- Camisa/chaqueta (cuerpo: caja en 16,16 de 8x12x4)
    box(img, 16, 16, 8, 12, 4, NAVY, NAVY_D, NAVY_L)
    rect(img, 23, 20, 2, 12, NAVY_D)                # cierre central
    for y in (22, 25, 28):
        img.putpixel((23, y), SILVER)               # botones
    rect(img, 21, 20, 2, 1, WHITE)                  # cuello
    rect(img, 25, 20, 2, 1, WHITE)
    rect(img, 25, 22, 2, 2, GOLD)                   # placa en el pecho
    rect(img, 20, 23, 3, 2, NAVY_D)                 # bolsillo
    rect(img, 20, 23, 3, 1, NAVY_L)
    rect(img, 33, 21, 6, 1, NAVY_L)                 # costura espalda
    # --- Mangas (brazo: caja en 40,16 de 4x12x4)
    box(img, 40, 16, 4, 12, 4, NAVY, NAVY_D, NAVY_L)
    for fx in (40, 44, 48, 52):
        rect(img, fx, 30, 4, 1, BLACK)              # puño
    rect(img, 40, 21, 4, 1, GOLD)                   # galon en el hombro
    # --- Botas (pierna: caja en 0,16 de 4x12x4) solo las 4 filas inferiores
    for fx in (0, 4, 8, 12):
        rect(img, fx, 28, 4, 4, BLACK)
        rect(img, fx, 28, 4, 1, BLACK_L)
    rect(img, 4, 30, 4, 1, BLACK_L)                 # brillo puntera
    rect(img, 8, 16, 4, 4, BLACK)                   # suela
    return img


def layer2():
    img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    # --- Pantalon (pierna)
    box(img, 0, 16, 4, 12, 4, NAVY_D, OUT, NAVY)
    rect(img, 4, 20, 1, 12, NAVY)                   # raya lateral
    rect(img, 0, 20, 1, 12, NAVY_L)
    # --- Cinturon (parte baja del cuerpo)
    for fx, w in ((16, 4), (20, 8), (28, 4), (32, 8)):
        rect(img, fx, 26, w, 2, NAVY_D)
        rect(img, fx, 26, w, 1, BLACK)
    rect(img, 23, 26, 2, 1, SILVER)                 # hebilla
    rect(img, 21, 26, 1, 1, BLACK_L)                # funda decorativa
    return img


def icon(pixels, palette):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(pixels):
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), palette[ch])
    return img


PAL = {"o": OUT, "n": NAVY, "d": NAVY_D, "l": NAVY_L, "k": BLACK, "g": GOLD, "s": SILVER, "w": WHITE}

HELMET = [
    "................",
    "................",
    "................",
    "....oooooooo....",
    "...olllllllno...",
    "..olnnnggnnnno..",
    "..onnnnggnnnno..",
    "..onnnnnnnnnno..",
    "..okkkkkkkkkko..",
    "..oooooooooooo..",
    "....okkkkkkko...",
    ".....ooooooo....",
    "................",
    "................",
    "................",
    "................",
]
CHEST = [
    "................",
    "..ooo..oo..ooo..",
    ".olnnowwwwonnlo.",
    "olnnnnowwonnnnlo",
    "onnnnnndsnnnggno",
    "onnnoonndnnnggno",
    "oddoonnsdnnnnodo",
    "okko.onndnnno.ko",
    ".oo..onnsnnno.o.",
    ".....onndnnno...",
    ".....odddddddo..",
    ".....okkkskkko..",
    ".....ooooooooo..",
    "................",
    "................",
    "................",
]
LEGS = [
    "................",
    "....oooooooo....",
    "....okkksskko...",
    "....odddddddo...",
    "....oddddnddo...",
    "....oddooddo....",
    "....oddooddo....",
    "....oddooddo....",
    "....oddooddo....",
    "....oddooddo....",
    "....oddooddo....",
    "....oddooddo....",
    "....oddooddo....",
    "....oooooooo....",
    "................",
    "................",
]
BOOTS = [
    "................",
    "................",
    "................",
    "................",
    "................",
    "...oooo..oooo...",
    "...okko..okko...",
    "...okko..okko...",
    "...okko..okko...",
    "...okko..okko...",
    "..ookko..okkoo..",
    ".okkkko..okkkko.",
    ".osskko..okkkso.",
    ".oooooo..oooooo.",
    "................",
    "................",
]


# ====================== BOMBERO ======================
TAN = (176, 142, 84, 255)
TAN_D = (130, 102, 58, 255)
TAN_L = (202, 172, 112, 255)
REFL = (232, 226, 70, 255)       # banda reflectante amarilla
REFL_S = (210, 214, 218, 255)    # banda plateada
RED = (186, 32, 30, 255)
RED_D = (128, 18, 18, 255)
RED_L = (224, 70, 56, 255)


def fire_layer1():
    img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    # --- Casco rojo: cubre la parte superior y un ala alrededor
    rect(img, 8, 0, 8, 8, RED)
    rect(img, 11, 0, 2, 8, RED_L)                   # cresta central
    for fx in (0, 8, 16, 24):
        rect(img, fx, 8, 8, 3, RED)
        rect(img, fx, 8, 8, 1, RED_L)
        rect(img, fx, 11, 8, 1, RED_D)              # ala del casco
    rect(img, 10, 8, 4, 3, GOLD)                    # escudo frontal
    rect(img, 11, 9, 2, 1, RED_D)
    # --- Chaqueta de proteccion
    box(img, 16, 16, 8, 12, 4, TAN, TAN_D, TAN_L)
    for fx, w in ((16, 4), (20, 8), (28, 4), (32, 8)):
        rect(img, fx, 26, w, 1, REFL)               # banda inferior
        rect(img, fx, 27, w, 1, REFL_S)
    rect(img, 23, 20, 2, 12, TAN_D)                 # cierre
    for y in (22, 24):
        img.putpixel((23, y), BLACK)                # broches
        img.putpixel((24, y), BLACK)
    rect(img, 20, 20, 2, 1, TAN_D)                  # cuello alto
    rect(img, 26, 20, 2, 1, TAN_D)
    rect(img, 33, 22, 6, 2, REFL)                   # banda espalda
    # --- Mangas
    box(img, 40, 16, 4, 12, 4, TAN, TAN_D, TAN_L)
    for fx in (40, 44, 48, 52):
        rect(img, fx, 26, 4, 1, REFL)
        rect(img, fx, 27, 4, 1, REFL_S)
        rect(img, fx, 31, 4, 1, BLACK)              # puno
    # --- Botas de goma negras con puntera amarilla
    for fx in (0, 4, 8, 12):
        rect(img, fx, 27, 4, 5, BLACK)
        rect(img, fx, 27, 4, 1, BLACK_L)
    rect(img, 4, 31, 4, 1, REFL)
    rect(img, 8, 16, 4, 4, BLACK)
    return img


def fire_layer2():
    img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    box(img, 0, 16, 4, 12, 4, TAN, TAN_D, TAN_L)
    for fx in (0, 4, 8, 12):
        rect(img, fx, 26, 4, 1, REFL)
        rect(img, fx, 27, 4, 1, REFL_S)
    rect(img, 4, 21, 3, 3, TAN_D)                   # bolsillo
    for fx, w in ((16, 4), (20, 8), (28, 4), (32, 8)):
        rect(img, fx, 26, w, 2, TAN_D)
        rect(img, fx, 26, w, 1, RED)                # tirantes/cinturon rojo
    rect(img, 21, 20, 1, 6, RED)                    # tirantes
    rect(img, 26, 20, 1, 6, RED)
    rect(img, 33, 20, 1, 6, RED)
    rect(img, 38, 20, 1, 6, RED)
    return img


FPAL = {"o": OUT, "n": TAN, "d": TAN_D, "l": TAN_L, "k": BLACK, "g": GOLD,
        "s": REFL_S, "w": TAN_D, "y": REFL, "r": RED, "R": RED_D, "L": RED_L}

FHELMET = [
    "................",
    "................",
    "......oooo......",
    "....ooLLrroo....",
    "...oLrrLrrrro...",
    "..orrrgggrrrro..",
    "..orrrgRgrrrro..",
    "..orrrgggrrrro..",
    ".oRRRRRRRRRRRRo.",
    "oRRRRRRRRRRRRRRo",
    ".oooooooooooooo.",
    "................",
    "................",
    "................",
    "................",
    "................",
]
FCHEST = [
    "................",
    "..ooo.oooo.ooo..",
    ".olnnoddddonnlo.",
    "olnnnnnkknnnnnlo",
    "onnnnnndnnnnnnno",
    "onnnoonkknoonnno",
    "onnoonndnnnoonno",
    "oyyo.onndnnno.yo",
    "osso.oyyyyyyo.so",
    ".oko.osssssso.k.",
    ".oo..onndnnno.o.",
    ".....onndnnno...",
    ".....ooooooooo..",
    "................",
    "................",
    "................",
]
FLEGS = [
    "................",
    "....oooooooo....",
    "....orrnnrro....",
    "....onnnnnno....",
    "....onddnnno....",
    "....onnoonno....",
    "....onnoonno....",
    "....onnoonno....",
    "....oyyooyyo....",
    "....ossoosso....",
    "....onnoonno....",
    "....onnoonno....",
    "....onnoonno....",
    "....oooooooo....",
    "................",
    "................",
]
FBOOTS = [
    "................",
    "................",
    "................",
    "................",
    "...oooo..oooo...",
    "...okko..okko...",
    "...okko..okko...",
    "...okko..okko...",
    "...okko..okko...",
    "...okko..okko...",
    "..ookko..okkoo..",
    ".okkkko..okkkko.",
    ".oyykko..okkyyo.",
    ".oooooo..oooooo.",
    "................",
    "................",
]


def save_set(job, l1, l2, arts, pal):
    l1.save(ARMOR / f"{job}_layer_1.png")
    l2.save(ARMOR / f"{job}_layer_2.png")
    for name, art in zip(("helmet", "chestplate", "leggings", "boots"), arts):
        assert len(art) == 16 and all(len(r) == 16 for r in art), (job, name)
        icon(art, pal).save(ITEM / f"{job}_{name}.png")


if __name__ == "__main__":
    ARMOR.mkdir(parents=True, exist_ok=True)
    ITEM.mkdir(parents=True, exist_ok=True)
    save_set("police", layer1(), layer2(), (HELMET, CHEST, LEGS, BOOTS), PAL)
    save_set("firefighter", fire_layer1(), fire_layer2(), (FHELMET, FCHEST, FLEGS, FBOOTS), FPAL)
    from uniformes import JOBS, layer1 as gl1, layer2 as gl2, icons
    for job, spec in JOBS.items():
        h, c, l, b = icons(spec)
        for name, im in zip(("helmet", "chestplate", "leggings", "boots"), (h, c, l, b)):
            im.save(ITEM / f"{job}_{name}.png")
        gl1(spec).save(ARMOR / f"{job}_layer_1.png")
        gl2(spec).save(ARMOR / f"{job}_layer_2.png")
    print("Texturas generadas en", ROOT)
