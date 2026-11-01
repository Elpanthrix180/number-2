"""Quitafondos con IA integrado (sin rembg ni onnxruntime: usa el motor DNN de OpenCV).

Modelos de segmentación de objeto principal, en formato ONNX:
  - «Rápido»  : U²-Netp (~4,6 MB)  — Xuebin Qin et al., Apache 2.0
  - «Calidad» : IS-Net general (~179 MB) — DIS, Xuebin Qin et al., Apache 2.0
Se descargan SOLO con autorización desde las publicaciones del proyecto rembg en
GitHub (conversiones ONNX de los pesos oficiales) y se verifican con SHA-256.
"""
from __future__ import annotations

import hashlib
import importlib.util
import logging
import threading
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from core.i18n import N_, t

log = logging.getLogger(__name__)

_BASE = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/"


@dataclass(frozen=True)
class BGModel:
    id: str
    label: str
    file: str
    sha256: str
    mb: float
    size: int                       # resolución de entrada del modelo
    mean: tuple[float, float, float]
    std: tuple[float, float, float]
    license: str

    @property
    def url(self) -> str:
        return _BASE + self.file


MODELS = {
    "rapido": BGModel("rapido", N_("Rápido (U²-Netp, ~4,6 MB)"), "u2netp.onnx",
                      "309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8", 4.6, 320,
                      (0.485, 0.456, 0.406), (0.229, 0.224, 0.225), "Apache 2.0 (U²-Net)"),
    "calidad": BGModel("calidad", N_("Calidad (IS-Net, ~179 MB)"), "isnet-general-use.onnx",
                       "60920e99c45464f2ba57bee2ad08c919a52bbf852739e96947fbb4358c0d964a", 179, 1024,
                       (0.5, 0.5, 0.5), (1.0, 1.0, 1.0), "Apache 2.0 (DIS / IS-Net)"),
}
MAX_SIDE = 8192


class BackgroundRemover:
    def __init__(self, models_dir: Path):
        self.folder = Path(models_dir) / "background"
        self._nets: dict[str, object] = {}
        self._lock = threading.Lock()

    # ---------------------------------------------------------- estado
    def path(self, model_id: str) -> Path:
        return self.folder / MODELS[model_id].file

    def installed(self, model_id: str) -> bool:
        return self.path(model_id).is_file()

    @staticmethod
    def deps_ready() -> bool:
        return importlib.util.find_spec("cv2") is not None

    def status(self) -> str:
        if not self.deps_ready():
            return t("🔴 Falta opencv-python-headless (ejecuta install_windows.bat)")
        parts = [f"{'🟢' if self.installed(m.id) else '⚪'} {t(m.label)}" for m in MODELS.values()]
        return " · ".join(parts)

    # -------------------------------------------------------- descarga
    def download(self, model_id: str, authorized: bool) -> str:
        m = MODELS.get(model_id)
        if m is None:
            return t("❌ Modelo desconocido.")
        if not authorized:
            return t("⚠️ Marca la casilla de autorización antes de descargar.")
        if self.installed(model_id):
            return t("{name} ya está instalado.", name=t(m.label))
        self.folder.mkdir(parents=True, exist_ok=True)
        dest = self.path(model_id)
        tmp = dest.with_suffix(".part")
        try:
            sha = hashlib.sha256()
            with urllib.request.urlopen(m.url, timeout=60) as r, open(tmp, "wb") as fh:
                while chunk := r.read(1 << 20):
                    sha.update(chunk)
                    fh.write(chunk)
            if sha.hexdigest() != m.sha256:
                tmp.unlink(missing_ok=True)
                return t("❌ El archivo descargado no coincide con la huella oficial (SHA-256). Se ha descartado.")
            tmp.replace(dest)
            return t("✅ {name} instalado y verificado.", name=t(m.label))
        except Exception as exc:  # noqa: BLE001
            tmp.unlink(missing_ok=True)
            return t("❌ Error al descargar: {err}", err=f"{type(exc).__name__}: {str(exc)[:150]}")

    def unload(self):
        with self._lock:
            self._nets.clear()

    # ------------------------------------------------------- inferencia
    def _net(self, model_id: str):
        import cv2

        if model_id not in self._nets:
            if not self.installed(model_id):
                raise RuntimeError(t("{name} no está instalado. Descárgalo arriba.", name=t(MODELS[model_id].label)))
            self._nets[model_id] = cv2.dnn.readNetFromONNX(str(self.path(model_id)))
        return self._nets[model_id]

    def mask(self, img: Image.Image, model_id: str = "rapido") -> Image.Image:
        """Máscara del objeto principal (L, 255 = objeto) al tamaño original."""
        m = MODELS[model_id]
        rgb = img.convert("RGB")
        if max(rgb.size) > MAX_SIDE:
            raise ValueError(t("Imagen demasiado grande (máx. {px}px de lado).", px=MAX_SIDE))
        x = np.asarray(rgb.resize((m.size, m.size), Image.LANCZOS), dtype=np.float32)
        x = x / max(float(x.max()), 1e-6)
        x = (x - np.array(m.mean, np.float32)) / np.array(m.std, np.float32)
        blob = x.transpose(2, 0, 1)[None].astype(np.float32)
        with self._lock:
            net = self._net(model_id)
            net.setInput(blob)
            pred = net.forward()            # primera salida = máscara final fusionada
        pred = pred.reshape(pred.shape[-2:]).astype(np.float32)
        lo, hi = float(pred.min()), float(pred.max())
        pred = (pred - lo) / (hi - lo) if hi > lo else np.zeros_like(pred)
        out = Image.fromarray((pred * 255).clip(0, 255).astype(np.uint8), "L")
        return out.resize(rgb.size, Image.LANCZOS)

    def remove(self, img: Image.Image, model_id: str = "rapido", background: str = "transparente",
               color: str = "#ffffff", feather: int = 0, threshold: int = 0) -> Image.Image:
        """Quita el fondo.

        background: "transparente", "color" o "mascara" (devuelve solo la máscara en blanco y negro).
        feather: px de suavizado del borde. threshold: 0 = bordes suaves; 1–254 = recorte duro.
        """
        mask = self.mask(img, model_id)
        if threshold:
            mask = mask.point(lambda v: 255 if v >= threshold else 0)
        if feather:
            mask = mask.filter(ImageFilter.GaussianBlur(feather))
        if background == "mascara":
            return mask.convert("RGB")
        rgba = img.convert("RGBA")
        if img.mode in ("RGBA", "LA"):     # respeta la transparencia que ya tuviera
            mask = Image.fromarray(np.minimum(np.asarray(mask), np.asarray(img.getchannel("A"))))
        rgba.putalpha(mask)
        if background == "color":
            bg = Image.new("RGBA", rgba.size, _parse_color(color))
            return Image.alpha_composite(bg, rgba).convert("RGB")
        return rgba


def _parse_color(value: str) -> tuple[int, int, int, int]:
    v = (value or "#ffffff").strip()
    if v.startswith("rgb"):
        nums = [int(float(n)) for n in v[v.index("(") + 1:v.index(")")].split(",")[:3]]
        return (*nums, 255)
    v = v.lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    try:
        return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16), 255)
    except ValueError:
        return (255, 255, 255, 255)
