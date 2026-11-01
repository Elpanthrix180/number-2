"""Restauración de caras con IA: GFPGAN v1.4 + detector de caras YuNet (OpenCV).

Flujo: detectar caras y sus 5 puntos (ojos, nariz, comisuras) → alinear cada cara
a 512×512 → restaurarla con GFPGAN → devolverla a su sitio con una máscara suave.

Archivos (se descargan SOLO con autorización, se verifican con SHA-256):
  - GFPGANv1.4.pth (~333 MB) — TencentARC/GFPGAN, Apache 2.0
  - face_detection_yunet_2023mar.onnx (~230 KB) — opencv/opencv_zoo, MIT
Los pesos se cargan con `weights_only=True` (sin ejecutar código del archivo).
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
from PIL import Image
from core.i18n import t

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class _File:
    name: str
    url: str
    sha256: str
    mb: float


GFPGAN_FILE = _File("GFPGANv1.4.pth",
                    "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth",
                    "e2cd4703ab14f4d01fd1383a8a8b266f9a5833dacee8e6a79d3bf21a1b6be5ad", 333)
YUNET_FILE = _File("face_detection_yunet_2023mar.onnx",
                   "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/"
                   "face_detection_yunet/face_detection_yunet_2023mar.onnx",
                   "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4", 0.2)
FILES = (GFPGAN_FILE, YUNET_FILE)
TOTAL_MB = round(sum(f.mb for f in FILES))
LICENSE = "GFPGAN: Apache 2.0 (TencentARC) · YuNet: MIT (OpenCV Zoo)"

FACE_SIZE = 512
# Posición de los 5 puntos en una cara alineada de 512×512 (plantilla FFHQ de GFPGAN/facexlib).
TEMPLATE_512 = np.array([[192.98138, 239.94708], [318.90277, 240.1936], [256.63416, 314.01935],
                         [201.26117, 371.41043], [313.08905, 371.15118]], dtype=np.float32)
MAX_SIDE = 4096
_MASK_CACHE: list = []


def _face_mask() -> np.ndarray:
    """Máscara elíptica difuminada (en la cara alineada de 512×512): cubre rostro y pelo cercano
    y se desvanece antes del borde del recorte, así no se ven costuras con el fondo original."""
    if not _MASK_CACHE:
        import cv2

        m = np.zeros((FACE_SIZE, FACE_SIZE), np.float32)
        cv2.ellipse(m, (256, 270), (190, 225), 0, 0, 360, 1.0, -1)
        _MASK_CACHE.append(cv2.GaussianBlur(m, (0, 0), 28))
    return _MASK_CACHE[0]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


class FaceRestorer:
    def __init__(self, models_dir: Path):
        self.folder = Path(models_dir) / "gfpgan"
        self._net = None
        self._device = "cpu"
        self._lock = threading.Lock()

    # ---------------------------------------------------------- estado
    def path(self, f: _File) -> Path:
        return self.folder / f.name

    def installed(self) -> bool:
        return all(self.path(f).is_file() for f in FILES)

    @staticmethod
    def deps_ready() -> tuple[bool, str]:
        missing = [m for m, pkg in (("torch", "PyTorch"), ("cv2", "opencv-python-headless"))
                   if importlib.util.find_spec(m) is None]
        if missing:
            return False, "Faltan dependencias: " + ", ".join(missing) + " (ejecuta install_windows.bat)"
        return True, ""

    def status(self) -> str:
        ok, msg = self.deps_ready()
        if not ok:
            return f"🔴 {msg}"
        return t("🟢 Instalado") if self.installed() else t("⚪ No instalado (descarga de ~{mb} MB)", mb=TOTAL_MB)

    # -------------------------------------------------------- descarga
    def download(self, authorized: bool) -> str:
        if not authorized:
            return t("⚠️ Marca la casilla de autorización antes de descargar.")
        if self.installed():
            return t("La restauración de caras ya está instalada.")
        self.folder.mkdir(parents=True, exist_ok=True)
        for f in FILES:
            dest = self.path(f)
            if dest.is_file():
                continue
            tmp = dest.with_suffix(".part")
            try:
                sha = hashlib.sha256()
                with urllib.request.urlopen(f.url, timeout=60) as r, open(tmp, "wb") as fh:
                    while chunk := r.read(1 << 20):
                        sha.update(chunk)
                        fh.write(chunk)
                if sha.hexdigest() != f.sha256:
                    tmp.unlink(missing_ok=True)
                    return t("❌ {name} no coincide con la huella oficial (SHA-256). Se ha descartado.", name=f.name)
                tmp.replace(dest)
            except Exception as exc:  # noqa: BLE001
                tmp.unlink(missing_ok=True)
                return t("❌ Error al descargar {name}: {err}", name=f.name, err=f"{type(exc).__name__}: {str(exc)[:150]}")
        return t("✅ GFPGAN y el detector de caras están instalados y verificados.")

    # ------------------------------------------------------------ carga
    def _load(self):
        if self._net is not None:
            return self._net
        if not self.installed():
            raise RuntimeError(t("La restauración de caras no está instalada. Descárgala en Herramientas → Caras IA."))
        import torch

        from tools.gfpgan_arch.gfpganv1_clean_arch import GFPGANv1Clean

        net = GFPGANv1Clean(out_size=512, num_style_feat=512, channel_multiplier=2, decoder_load_path=None,
                            fix_decoder=False, num_mlp=8, input_is_latent=True, different_w=True, narrow=1,
                            sft_half=True)
        state = torch.load(self.path(GFPGAN_FILE), map_location="cpu", weights_only=True)
        state = state.get("params_ema", state.get("params", state))
        net.load_state_dict(state, strict=True)
        net.eval()
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._net = net.to(self._device)
        return self._net

    def unload(self):
        with self._lock:
            self._net = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    # ------------------------------------------------------- detección
    def detect(self, rgb: np.ndarray, min_score: float = 0.7, min_size: int = 16) -> list[np.ndarray]:
        """Devuelve, por cada cara, sus 5 puntos en el orden de la plantilla (de mayor a menor)."""
        import cv2

        h, w = rgb.shape[:2]
        det = cv2.FaceDetectorYN.create(str(self.path(YUNET_FILE)), "", (w, h), min_score, 0.3, 5000)
        _, faces = det.detect(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        out = []
        if faces is None:
            return out
        for f in sorted(faces, key=lambda r: -r[2] * r[3]):
            if min(f[2], f[3]) < min_size:
                continue
            pts = f[4:14].reshape(5, 2).astype(np.float32)
            eyes = pts[:2][np.argsort(pts[:2, 0])]       # ojo izquierdo de la imagen primero
            mouth = pts[3:5][np.argsort(pts[3:5, 0])]
            out.append(np.vstack([eyes, pts[2:3], mouth]))
        return out

    # ------------------------------------------------------ restauración
    def restore(self, img: Image.Image, weight: float = 0.6, upscale: int = 1, max_faces: int = 10,
                upscaler=None, progress=None, cancel: threading.Event | None = None) -> tuple[Image.Image, int]:
        """Restaura las caras de `img`. Devuelve (imagen, número de caras restauradas).

        weight: 0 = original, 1 = totalmente restaurada (0.5–0.7 conserva mejor la identidad).
        upscale: 1 o 2; con 2 amplía antes todo el fondo (Real-ESRGAN si se pasa `upscaler`).
        """
        import cv2
        import torch

        if upscale not in (1, 2):
            raise ValueError(t("La ampliación debe ser 1 o 2."))
        if not 0.0 <= weight <= 1.0:
            raise ValueError(t("La intensidad debe estar entre 0 y 1."))
        alpha = img.getchannel("A") if img.mode in ("RGBA", "LA") else None
        base = img.convert("RGB")
        if max(base.size) * upscale > MAX_SIDE:
            raise ValueError(t("El resultado superaría {px}px de lado.", px=MAX_SIDE))
        if upscale == 2:
            if upscaler is not None and upscaler.installed():
                base = upscaler.upscale(base, 2, cancel=cancel)
            else:
                base = base.resize((base.width * 2, base.height * 2), Image.LANCZOS)

        with self._lock:
            net = self._load()
            rgb = np.asarray(base).copy()
            faces = self.detect(rgb)[:max_faces]
            h, w = rgb.shape[:2]
            result = rgb.astype(np.float32)
            for i, lm in enumerate(faces):
                if cancel is not None and cancel.is_set():
                    raise InterruptedError(t("Cancelado"))
                affine, _ = cv2.estimateAffinePartial2D(lm, TEMPLATE_512, method=cv2.LMEDS)
                if affine is None:
                    continue
                crop = cv2.warpAffine(rgb, affine, (FACE_SIZE, FACE_SIZE), borderMode=cv2.BORDER_CONSTANT,
                                      borderValue=(132, 133, 135))
                x = torch.from_numpy(crop).permute(2, 0, 1).float().div(255).sub(0.5).div(0.5).unsqueeze(0)
                with torch.inference_mode():
                    y = net(x.to(self._device), return_rgb=False, weight=0.5)[0]
                face = ((y.squeeze(0).float().cpu().clamp(-1, 1) + 1) * 127.5).permute(1, 2, 0).numpy()
                face = weight * face + (1 - weight) * crop.astype(np.float32)

                inv = cv2.invertAffineTransform(affine)
                back = cv2.warpAffine(face, inv, (w, h), flags=cv2.INTER_LINEAR)
                mask = cv2.warpAffine(_face_mask(), inv, (w, h), flags=cv2.INTER_LINEAR)[..., None]
                result = mask * back + (1 - mask) * result
                if progress:
                    progress(i + 1, len(faces))
        out = Image.fromarray(np.clip(result, 0, 255).round().astype(np.uint8))
        if alpha is not None:
            out.putalpha(alpha.resize(out.size, Image.LANCZOS))
        return out, len(faces)
