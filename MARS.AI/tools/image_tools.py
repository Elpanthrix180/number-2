"""Herramientas de edición.

Herramientas clásicas (siempre disponibles, solo Pillow/NumPy):
  - upscale_classic, enhance, restore
Herramientas con IA (requieren dependencias o un modelo de difusión instalado):
  - remove_background (rembg, opcional)
  - img2img / variations / inpaint / outpaint (usan el modelo de difusión activo)
"""
from __future__ import annotations

import importlib.util

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

MAX_UPSCALED_SIDE = 8192


# ------------------------------------------------------------ clásicas
def upscale_classic(img: Image.Image, factor: int = 2, sharpen: bool = True) -> Image.Image:
    """Aumenta la resolución con Lanczos + enfoque. No inventa detalle (no es IA)."""
    if factor not in (2, 3, 4):
        raise ValueError("El factor debe ser 2, 3 o 4.")
    w, h = img.size
    if max(w, h) * factor > MAX_UPSCALED_SIDE:
        raise ValueError(f"El resultado superaría {MAX_UPSCALED_SIDE}px de lado.")
    out = img.convert("RGB").resize((w * factor, h * factor), Image.LANCZOS)
    if sharpen:
        out = out.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
    return out


def enhance(img: Image.Image, sharpness: float = 1.5, contrast: float = 1.1,
            color: float = 1.1, detail: bool = True) -> Image.Image:
    out = img.convert("RGB")
    if detail:
        out = out.filter(ImageFilter.DETAIL)
    out = ImageEnhance.Sharpness(out).enhance(sharpness)
    out = ImageEnhance.Contrast(out).enhance(contrast)
    out = ImageEnhance.Color(out).enhance(color)
    return out


def restore(img: Image.Image, denoise: int = 3, fix_colors: bool = True,
            scratches: bool = True) -> Image.Image:
    """Restauración básica de fotos antiguas: reduce ruido y rayas finas,
    corrige contraste y dominantes de color."""
    out = img.convert("RGB")
    if scratches:
        out = out.filter(ImageFilter.MedianFilter(3))
    if denoise:
        size = denoise if denoise % 2 == 1 else denoise + 1
        out = Image.blend(out, out.filter(ImageFilter.MedianFilter(size)), 0.5)
    if fix_colors:
        out = ImageOps.autocontrast(out, cutoff=1)
        arr = np.asarray(out).astype(np.float32)
        means = arr.reshape(-1, 3).mean(axis=0)
        arr *= means.mean() / np.maximum(means, 1)   # balance de blancos «gray world»
        out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return out.filter(ImageFilter.UnsharpMask(radius=1.5, percent=60, threshold=3))


# --------------------------------------------------------------- fondos
def rembg_available() -> bool:
    return importlib.util.find_spec("rembg") is not None


_rembg_session = None


def remove_background(img: Image.Image) -> Image.Image:
    if not rembg_available():
        raise RuntimeError("El quitafondos con IA no está instalado. Ejecuta install_optional_tools.bat "
                           "(instala rembg y descarga un modelo de ~170 MB con tu autorización).")
    global _rembg_session
    from rembg import new_session, remove

    if _rembg_session is None:
        _rembg_session = new_session("u2net")
    return remove(img.convert("RGB"), session=_rembg_session)


# ------------------------------------------------------- outpainting
def prepare_outpaint(img: Image.Image, left: int, right: int, top: int, bottom: int,
                     multiple: int = 8) -> tuple[Image.Image, Image.Image]:
    """Amplía el lienzo y crea la máscara (blanco = zona a generar)."""
    if min(left, right, top, bottom) < 0:
        raise ValueError("Los márgenes no pueden ser negativos.")
    if left + right + top + bottom == 0:
        raise ValueError("Indica al menos un margen para ampliar.")
    src = img.convert("RGB")
    w = src.width + left + right
    h = src.height + top + bottom
    # redondea a múltiplos de 8 (requisito de los modelos de difusión)
    pad_w = (-w) % multiple
    pad_h = (-h) % multiple
    right += pad_w
    bottom += pad_h
    w += pad_w
    h += pad_h
    # rellena con los bordes estirados para dar contexto de color al modelo
    arr = np.pad(np.asarray(src), ((top, bottom), (left, right), (0, 0)), mode="edge")
    canvas = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(8))
    canvas.paste(src, (left, top))
    mask = Image.new("L", (w, h), 255)
    overlap = 8  # pequeño solape para que la unión sea suave
    x0 = left + (overlap if left else 0)
    y0 = top + (overlap if top else 0)
    x1 = left + src.width - (overlap if right else 0)
    y1 = top + src.height - (overlap if bottom else 0)
    mask.paste(0, (x0, y0, x1, y1))
    return canvas, mask


def fit_for_diffusion(img: Image.Image, max_side: int = 768) -> Image.Image:
    """Redimensiona para que quepa en max_side manteniendo proporción, múltiplo de 8."""
    img = img.convert("RGB")
    scale = min(1.0, max_side / max(img.size))
    w = max(64, int(img.width * scale) // 8 * 8)
    h = max(64, int(img.height * scale) // 8 * 8)
    return img.resize((w, h), Image.LANCZOS)


def mask_from_editor(editor_value) -> tuple[Image.Image, Image.Image]:
    """Convierte el valor de gr.ImageEditor en (imagen, máscara L).

    Lo pintado en las capas (cualquier color con alfa > 0) se convierte en blanco."""
    if not editor_value or editor_value.get("background") is None:
        raise ValueError("Sube una imagen y pinta la zona a modificar.")
    bg = editor_value["background"]
    bg = bg if isinstance(bg, Image.Image) else Image.fromarray(np.asarray(bg))
    mask = Image.new("L", bg.size, 0)
    for layer in editor_value.get("layers") or []:
        layer = layer if isinstance(layer, Image.Image) else Image.fromarray(np.asarray(layer))
        alpha = layer.convert("RGBA").split()[-1]
        if alpha.size != bg.size:
            alpha = alpha.resize(bg.size)
        mask = Image.fromarray(np.maximum(np.asarray(mask), (np.asarray(alpha) > 10).astype(np.uint8) * 255))
    if not np.asarray(mask).any():
        raise ValueError("No has pintado ninguna zona. Usa el pincel sobre lo que quieras cambiar.")
    return bg.convert("RGB"), mask
