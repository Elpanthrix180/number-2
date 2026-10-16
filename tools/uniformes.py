"""Generador generico de uniformes de Panthrix Jobs.
Cada profesion se describe con un diccionario (colores + detalles) y aqui se
dibujan sus dos capas de armadura (64x32) y sus cuatro iconos (16x16)."""
from PIL import Image

T = (0, 0, 0, 0)
OUT = (10, 12, 20, 255)
BODY_FACES = ((16, 4), (20, 8), (28, 4), (32, 8))   # derecha, frente, izquierda, espalda
ARM_FACES = (40, 44, 48, 52)
LEG_FACES = (0, 4, 8, 12)
HEAD_FACES = (0, 8, 16, 24)


def tone(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)


def rgba(c):
    return tuple(c) + (255,) if len(c) == 3 else tuple(c)


def rect(img, x, y, w, h, c):
    for i in range(x, x + w):
        for j in range(y, y + h):
            img.putpixel((i, j), c)


def box(img, ox, oy, w, h, d, c):
    base, dark, light = c, tone(c, 0.72), tone(c, 1.18)
    rect(img, ox + d, oy, w, d, light)
    rect(img, ox + d + w, oy, w, d, dark)
    for x, fw in ((ox, d), (ox + d, w), (ox + d + w, d), (ox + 2 * d + w, w)):
        rect(img, x, oy + d, fw, h, base)
        rect(img, x, oy + d, fw, 1, light)
        rect(img, x, oy + d + h - 1, fw, 1, dark)


# ---------------------------------------------------------------- cabeza
def draw_head(img, s):
    kind, c = s["head"], rgba(s["head_color"])
    acc = rgba(s.get("head_accent", (20, 20, 24)))
    rect(img, 8, 0, 8, 8, c)
    rect(img, 9, 1, 6, 6, tone(c, 1.12))
    if kind == "cap":                       # gorra de plato / de visera
        for fx in HEAD_FACES:
            rect(img, fx, 8, 8, 2, c)
            rect(img, fx, 10, 8, 1, acc)
        rect(img, 8, 11, 8, 1, rgba(s.get("visor", (24, 24, 28))))
        if "badge" in s:
            rect(img, 11, 8, 2, 2, rgba(s["badge"]))
    elif kind == "striped_cap":             # gorra ferroviaria a rayas
        for fx in HEAD_FACES:
            for i in range(8):
                rect(img, fx + i, 8, 1, 3, c if i % 2 == 0 else acc)
        rect(img, 8, 0, 8, 8, c)
        for i in range(0, 8, 2):
            rect(img, 8 + i, 0, 1, 8, acc)
        rect(img, 8, 11, 8, 1, tone(c, 0.6))
    elif kind == "hardhat":                 # casco de obra
        for fx in HEAD_FACES:
            rect(img, fx, 8, 8, 3, c)
            rect(img, fx, 8, 8, 1, tone(c, 1.15))
            rect(img, fx, 11, 8, 1, tone(c, 0.7))
        rect(img, 11, 0, 2, 8, tone(c, 1.2))
        rect(img, 10, 9, 4, 1, acc)         # pegatina reflectante
    elif kind == "scrub":                   # gorro quirurgico de tela
        for fx in HEAD_FACES:
            rect(img, fx, 8, 8, 3, c)
            rect(img, fx, 10, 8, 1, tone(c, 0.82))
        rect(img, 27, 10, 2, 2, tone(c, 0.7))   # lazo atras
        for x in (10, 13):
            img.putpixel((x, 9), acc)
    elif kind == "chef":                    # gorro alto de cocinero (pliegues)
        rect(img, 8, 0, 8, 8, c)
        for i in range(1, 7, 2):
            rect(img, 8 + i, 1, 1, 6, tone(c, 0.9))
        for fx in HEAD_FACES:
            for i in range(8):
                rect(img, fx + i, 8, 1, 4, c if i % 2 == 0 else tone(c, 0.9))
            rect(img, fx, 12, 8, 1, acc)    # banda del gorro


# ---------------------------------------------------------------- cuerpo
def draw_body(img, s):
    c = rgba(s["chest"])
    box(img, 16, 16, 8, 12, 4, c)
    box(img, 40, 16, 4, 12, 4, rgba(s.get("sleeve", s["chest"])))
    f = set(s.get("features", ()))
    acc = rgba(s.get("accent", (230, 190, 60)))
    if "vest" in f:                         # chaleco sobre camisa
        v = rgba(s["vest"])
        for x, w in BODY_FACES:
            rect(img, x, 20, w, 11, v)
        for x, w in BODY_FACES:
            rect(img, x, 24, w, 1, (220, 224, 228, 255))
            rect(img, x, 28, w, 1, (220, 224, 228, 255))
        rect(img, 20, 20, 1, 11, (220, 224, 228, 255))
        rect(img, 27, 20, 1, 11, (220, 224, 228, 255))
        rect(img, 23, 20, 2, 2, c)          # cuello de la camisa visible
    if "collar" in f:
        col = rgba(s.get("collar_color", (236, 236, 240)))
        rect(img, 21, 20, 2, 1, col)
        rect(img, 25, 20, 2, 1, col)
        rect(img, 32, 20, 8, 1, col)
    if "tie" in f:
        t = rgba(s["tie"])
        rect(img, 23, 20, 2, 1, t)
        rect(img, 23, 21, 2, 5, t)
        img.putpixel((23, 26), t)
    if "neckerchief" in f:
        n = rgba(s["neckerchief"])
        rect(img, 21, 20, 6, 1, n)
        rect(img, 22, 21, 4, 1, n)
        rect(img, 23, 22, 2, 1, n)
    if "zip" in f:
        rect(img, 23, 21, 2, 11, tone(c, 0.7))
        rect(img, 24, 21, 1, 11, (180, 184, 190, 255))
    if "buttons" in f:
        rect(img, 23, 20, 2, 12, tone(c, 0.82))
        for y in (22, 25, 28):
            img.putpixel((23, y), acc)
    if "double" in f:                       # doble botonadura (cocinero)
        for y in (22, 25, 28):
            img.putpixel((21, y), acc)
            img.putpixel((26, y), acc)
        rect(img, 24, 20, 1, 12, tone(c, 0.85))
    if "pocket" in f:
        rect(img, 20, 23, 3, 2, tone(c, 0.8))
        rect(img, 20, 23, 3, 1, tone(c, 1.1))
    if "badge" in f:
        rect(img, 25, 22, 2, 2, acc)
    if "epaulettes" in f:
        for x in (40, 44, 48, 52):
            rect(img, x, 20, 4, 1, acc)
        rect(img, 44, 22, 4, 1, acc)
        rect(img, 44, 23, 4, 1, acc)
    if "stethoscope" in f:
        g = (60, 64, 72, 255)
        for (x, y) in ((21, 20), (21, 21), (21, 22), (21, 23), (22, 24), (26, 20), (26, 21), (26, 22), (26, 23), (25, 24)):
            img.putpixel((x, y), g)
        rect(img, 23, 24, 2, 1, g)
        rect(img, 23, 25, 2, 2, (200, 204, 212, 255))
        rect(img, 20, 26, 2, 2, (110, 160, 220, 255))   # identificacion
    if "wrench" in f:
        m = (190, 196, 204, 255)
        rect(img, 20, 23, 3, 3, tone(c, 0.8))
        for (x, y) in ((21, 21), (21, 22), (21, 23), (21, 24), (20, 21), (22, 21)):
            img.putpixel((x, y), m)
        rect(img, 26, 26, 1, 3, (200, 40, 40, 255))      # trapo rojo
    if "bag" in f:                          # correa cruzada (bolsa en el pantalon)
        b = rgba(s.get("bag_color", (120, 76, 40)))
        for i in range(8):
            img.putpixel((20 + i, 20 + i + 2), b)
            img.putpixel((39 - i, 20 + i + 2), b)
        rect(img, 18, 20, 2, 2, b)
        rect(img, 31, 20, 1, 2, b)
        rect(img, 25, 22, 2, 1, acc)
    if "stripes" in f:                      # bandas reflectantes
        for x, w in BODY_FACES:
            rect(img, x, 26, w, 1, acc)
        for x in ARM_FACES:
            rect(img, x, 26, 4, 1, acc)
    cuff = s.get("cuff")
    if cuff:
        for x in ARM_FACES:
            rect(img, x, 30, 4, 1, rgba(cuff))
    if "rolled" in f:                       # mangas remangadas
        for x in ARM_FACES:
            rect(img, x, 26, 4, 6, T)
            rect(img, x, 25, 4, 1, tone(rgba(s.get("sleeve", s["chest"])), 0.8))
        rect(img, 48, 16, 4, 4, T)


def draw_boots(img, s):
    b = rgba(s["boots"])
    for fx in LEG_FACES:
        rect(img, fx, 28, 4, 4, b)
        rect(img, fx, 28, 4, 1, tone(b, 1.25))
    rect(img, 4, 30, 4, 1, rgba(s.get("toe", tone(b, 1.4))))
    rect(img, 8, 16, 4, 4, tone(b, 0.6))


def layer1(s):
    img = Image.new("RGBA", (64, 32), T)
    draw_head(img, s)
    draw_body(img, s)
    draw_boots(img, s)
    return img


def layer2(s):
    img = Image.new("RGBA", (64, 32), T)
    p = rgba(s["pants"])
    box(img, 0, 16, 4, 12, 4, p)
    f = set(s.get("pant_features", ()))
    if "check" in f:                        # cuadros de cocinero
        for fx in LEG_FACES:
            for y in range(20, 32):
                for x in range(fx, fx + 4):
                    if (x + y) % 2 == 0:
                        img.putpixel((x, y), (236, 236, 240, 255))
    if "side_stripe" in f:
        rect(img, 0, 20, 1, 12, rgba(s.get("pant_accent", tone(p, 1.3))))
    if "knee" in f:
        rect(img, 4, 24, 4, 2, tone(p, 0.75))
    if "reflect" in f:
        for fx in LEG_FACES:
            rect(img, fx, 27, 4, 1, (220, 224, 228, 255))
    if "bag" in f:                          # bolsa de correo en la cadera
        b = rgba(s.get("bag_color", (120, 76, 40)))
        rect(img, 0, 20, 4, 5, b)
        rect(img, 0, 20, 4, 1, tone(b, 1.3))
        rect(img, 1, 22, 2, 1, rgba(s.get("accent", (230, 190, 60))))
    belt = s.get("belt")
    if belt:
        for x, w in BODY_FACES:
            rect(img, x, 26, w, 2, tone(p, 0.8))
            rect(img, x, 26, w, 1, rgba(belt))
        rect(img, 23, 26, 2, 1, (200, 204, 212, 255))
    if "bib" in f:                          # peto del mono
        for x, w in BODY_FACES:
            rect(img, x, 20, w, 8, p)
        rect(img, 22, 20, 4, 4, tone(p, 0.85))
    return img


# ---------------------------------------------------------------- iconos
HEAD_ICONS = {
    "cap": [
        "................", "................", "................", "....oooooooo....",
        "...olllllllno...", "..olnnnggnnnno..", "..onnnnggnnnno..", "..onnnnnnnnnno..",
        "..oaaaaaaaaaao..", "..oooooooooooo..", "....ovvvvvvvo...", ".....ooooooo....",
        "................", "................", "................", "................"],
    "striped_cap": [
        "................", "................", "................", "....oooooooo....",
        "...onanananano..", "..onanananananao", "..onanananananao", "..onanananananao",
        "..oddddddddddddo", "..oooooooooooooo", "....oddddddddo..", ".....oooooooo...",
        "................", "................", "................", "................"],
    "hardhat": [
        "................", "................", "................", "......oooo......",
        "....oollnnoo....", "...olnnlnnnno...", "..onnnnlnnnnno..", "..onnaaaannnno..",
        "..onnnnnnnnnno..", ".oddddddddddddo.", ".oooooooooooooo.", "................",
        "................", "................", "................", "................"],
    "scrub": [
        "................", "................", "................", "................",
        "....oooooooo....", "...olllllllno...", "..olnnnnnnnnno..", "..onnannannnno..",
        "..onnnnnnnnnno..", "..oddddddddddo..", "..oooooooooodo..", "............oo..",
        "................", "................", "................", "................"],
    "chef": [
        "...oooo..oooo...", "..ollnnoolnnno..", ".olnnnnnnnnnnno.", ".onnnnnnnnnnnno.",
        ".odnnnnnnnnnndo.", "..oddnnnnnnddo..", "...ondndndndo...", "...ondndndndo...",
        "...ondndndndo...", "...ondndndndo...", "...oaaaaaaaao...", "...oooooooooo...",
        "................", "................", "................", "................"],
}
CHEST_ICON = [
    "................", "..ooo..oo..ooo..", ".olnnowwwwonnlo.", "olnnnnowwonnnnlo",
    "onnnnnndsnnnggno", "onnnoonndnnnggno", "osdoonnsdnnnnodo", "occo.onndnnno.co",
    ".oo..onnsnnno.o.", ".....onndnnno...", ".....onnnnnnno..", ".....odddddddo..",
    ".....ooooooooo..", "................", "................", "................"]
LEGS_ICON = [
    "................", "....oooooooo....", "....obbbssbbo...", "....opppppppo...",
    "....oppppPppo...", "....oppooppo....", "....oppooppo....", "....oppooppo....",
    "....oppooppo....", "....oppooppo....", "....oppooppo....", "....oppooppo....",
    "....oPPooPPo....", "....oooooooo....", "................", "................"]
BOOTS_ICON = [
    "................", "................", "................", "................",
    "................", "...oooo..oooo...", "...okko..okko...", "...okko..okko...",
    "...okko..okko...", "...okko..okko...", "..ookko..okkoo..", ".okkkko..okkkko.",
    ".ottkko..okktto.", ".oooooo..oooooo.", "................", "................"]


def icon(art, pal):
    img = Image.new("RGBA", (16, 16), T)
    for y, row in enumerate(art):
        assert len(row) == 16, row
        for x, ch in enumerate(row):
            if ch != ".":
                img.putpixel((x, y), pal[ch])
    return img


def icons(s):
    hc = rgba(s["head_color"])
    head_pal = {"o": OUT, "n": hc, "l": tone(hc, 1.18), "d": tone(hc, 0.72),
                "a": rgba(s.get("head_accent", (20, 20, 24))),
                "g": rgba(s.get("badge", s.get("head_accent", hc))),
                "v": rgba(s.get("visor", (24, 24, 28)))}
    c = rgba(s["chest"])
    main = rgba(s["vest"]) if "vest" in s.get("features", ()) else c
    chest_pal = {"o": OUT, "n": main, "l": tone(main, 1.18), "d": tone(main, 0.72),
                 "w": rgba(s.get("tie", s.get("collar_color", tone(c, 1.15)))),
                 "s": rgba(s.get("accent", tone(c, 0.7))),
                 "g": rgba(s.get("accent", tone(c, 0.7))),
                 "c": rgba(s.get("cuff", tone(c, 0.6)))}
    p = rgba(s["pants"])
    legs_pal = {"o": OUT, "p": p, "P": tone(p, 0.72),
                "b": rgba(s.get("belt", tone(p, 0.6))), "s": (200, 204, 212, 255)}
    b = rgba(s["boots"])
    boots_pal = {"o": OUT, "k": b, "t": rgba(s.get("toe", tone(b, 1.4)))}
    return (icon(HEAD_ICONS[s["head"]], head_pal), icon(CHEST_ICON, chest_pal),
            icon(LEGS_ICON, legs_pal), icon(BOOTS_ICON, boots_pal))


# ---------------------------------------------------------------- profesiones
JOBS = {
    "doctor": dict(
        head="scrub", head_color=(70, 168, 170), head_accent=(236, 236, 240),
        chest=(238, 240, 244), collar_color=(70, 168, 170), accent=(150, 156, 168),
        features=("collar", "buttons", "pocket", "stethoscope"), cuff=(205, 210, 218),
        pants=(70, 168, 170), pant_features=("knee",),
        boots=(232, 234, 238), toe=(170, 176, 186)),
    "builder": dict(
        head="hardhat", head_color=(240, 196, 30), head_accent=(230, 232, 236),
        chest=(92, 108, 132), vest=(244, 120, 24), accent=(230, 232, 236),
        features=("vest", "rolled"),
        pants=(80, 86, 96), belt=(110, 70, 36), pant_features=("knee",),
        boots=(122, 80, 44), toe=(170, 176, 186)),
    "pilot": dict(
        head="cap", head_color=(24, 26, 34), head_accent=(214, 174, 60), badge=(230, 196, 80),
        visor=(12, 12, 14),
        chest=(242, 242, 246), tie=(24, 26, 34), accent=(214, 174, 60),
        features=("tie", "epaulettes", "pocket"),
        pants=(30, 32, 40), belt=(14, 14, 16),
        boots=(20, 20, 24), toe=(70, 72, 80)),
    "bus_driver": dict(
        head="cap", head_color=(96, 104, 116), head_accent=(170, 40, 46), badge=(200, 204, 212),
        chest=(96, 104, 116), collar_color=(160, 200, 236), tie=(170, 40, 46), accent=(200, 204, 212),
        features=("collar", "tie", "pocket", "badge"), cuff=(60, 66, 76),
        pants=(62, 66, 76), belt=(20, 20, 24), pant_features=("side_stripe",), pant_accent=(170, 40, 46),
        boots=(24, 24, 28)),
    "train_driver": dict(
        head="striped_cap", head_color=(58, 84, 140), head_accent=(226, 230, 238),
        chest=(58, 84, 140), neckerchief=(200, 40, 40), accent=(226, 196, 90),
        features=("neckerchief", "buttons", "pocket"), cuff=(40, 58, 100),
        pants=(50, 72, 122), belt=(110, 70, 36), pant_features=("knee",),
        boots=(96, 62, 34)),
    "mechanic": dict(
        head="cap", head_color=(64, 70, 80), head_accent=(206, 60, 40), visor=(40, 44, 50),
        badge=(206, 60, 40),
        chest=(64, 70, 80), accent=(206, 60, 40),
        features=("zip", "wrench", "rolled"),
        pants=(64, 70, 80), belt=(206, 60, 40), pant_features=("bib", "knee"),
        boots=(30, 30, 34), toe=(170, 176, 186)),
    "mail_carrier": dict(
        head="cap", head_color=(36, 70, 140), head_accent=(242, 196, 40), badge=(242, 196, 40),
        chest=(150, 190, 228), collar_color=(36, 70, 140), accent=(242, 196, 40),
        bag_color=(124, 80, 42),
        features=("collar", "buttons", "bag"), cuff=(36, 70, 140),
        pants=(36, 70, 140), pant_features=("bag", "side_stripe"), pant_accent=(242, 196, 40),
        boots=(26, 26, 30)),
    "chef": dict(
        head="chef", head_color=(244, 244, 248), head_accent=(214, 218, 226),
        chest=(244, 244, 248), accent=(30, 30, 34),
        features=("double",), cuff=(30, 30, 34),
        pants=(36, 36, 40), pant_features=("check",),
        boots=(20, 20, 24)),
}
