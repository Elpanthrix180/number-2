"""Upscaler con IA: Real-ESRGAN x4plus (licencia BSD-3, Xintao Wang et al.).

Arquitectura RRDBNet implementada aquí para no depender de `basicsr`.
Los pesos (~64 MB) se descargan del repositorio oficial en GitHub SOLO con
autorización del usuario, se verifican con SHA-256 y se cargan con
`weights_only=True` (sin ejecutar código del archivo).
Procesa por mosaicos (tiles) para usar poca memoria.
"""
from __future__ import annotations

import hashlib
import logging
import threading
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

log = logging.getLogger(__name__)

MODEL_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
MODEL_SHA256 = "4fa0d38905f75ac06eb49a7951b426670021be3018265fd191d2125df9d682f1"
MODEL_FILE = "RealESRGAN_x4plus.pth"
MODEL_MB = 64
LICENSE = "BSD-3-Clause (https://github.com/xinntao/Real-ESRGAN)"


def _build_net():
    import torch
    from torch import nn
    from torch.nn import functional as F

    class RDB(nn.Module):
        def __init__(self, nf=64, gc=32):
            super().__init__()
            self.conv1 = nn.Conv2d(nf, gc, 3, 1, 1)
            self.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
            self.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1)
            self.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
            self.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1)
            self.lrelu = nn.LeakyReLU(0.2, inplace=True)

        def forward(self, x):
            x1 = self.lrelu(self.conv1(x))
            x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
            x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
            x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
            x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
            return x5 * 0.2 + x

    class RRDB(nn.Module):
        def __init__(self, nf=64, gc=32):
            super().__init__()
            self.rdb1, self.rdb2, self.rdb3 = RDB(nf, gc), RDB(nf, gc), RDB(nf, gc)

        def forward(self, x):
            return self.rdb3(self.rdb2(self.rdb1(x))) * 0.2 + x

    class RRDBNet(nn.Module):
        def __init__(self, nf=64, nb=23, gc=32):
            super().__init__()
            self.conv_first = nn.Conv2d(3, nf, 3, 1, 1)
            self.body = nn.Sequential(*[RRDB(nf, gc) for _ in range(nb)])
            self.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
            self.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1)
            self.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
            self.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1)
            self.conv_last = nn.Conv2d(nf, 3, 3, 1, 1)
            self.lrelu = nn.LeakyReLU(0.2, inplace=True)

        def forward(self, x):
            feat = self.conv_first(x)
            feat = feat + self.conv_body(self.body(feat))
            feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode="nearest")))
            feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode="nearest")))
            return self.conv_last(self.lrelu(self.conv_hr(feat)))

    return RRDBNet()


class RealESRGAN:
    def __init__(self, models_dir: Path):
        self.path = Path(models_dir) / "realesrgan" / MODEL_FILE
        self._net = None
        self._device = "cpu"
        self._lock = threading.Lock()

    # ---------------------------------------------------------- estado
    def installed(self) -> bool:
        return self.path.is_file()

    @staticmethod
    def torch_ready() -> bool:
        import importlib.util

        return importlib.util.find_spec("torch") is not None

    def status(self) -> str:
        if not self.torch_ready():
            return "🔴 Falta PyTorch (ejecuta install_windows.bat)"
        return "🟢 Instalado" if self.installed() else f"⚪ No instalado (descarga de ~{MODEL_MB} MB)"

    # -------------------------------------------------------- descarga
    def download(self, authorized: bool) -> str:
        if not authorized:
            return "⚠️ Marca la casilla de autorización antes de descargar."
        if self.installed():
            return "Real-ESRGAN ya está instalado."
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".part")
        try:
            sha = hashlib.sha256()
            with urllib.request.urlopen(MODEL_URL, timeout=60) as r, open(tmp, "wb") as fh:
                while chunk := r.read(1 << 20):
                    sha.update(chunk)
                    fh.write(chunk)
            if sha.hexdigest() != MODEL_SHA256:
                tmp.unlink(missing_ok=True)
                return "❌ El archivo descargado no coincide con la huella oficial (SHA-256). Se ha descartado."
            tmp.replace(self.path)
            return "✅ Real-ESRGAN instalado y verificado."
        except Exception as exc:  # noqa: BLE001
            tmp.unlink(missing_ok=True)
            return f"❌ Error al descargar: {type(exc).__name__}: {str(exc)[:150]}"

    # ------------------------------------------------------------ carga
    def _load(self):
        import torch

        if self._net is not None:
            return self._net
        if not self.installed():
            raise RuntimeError("Real-ESRGAN no está instalado. Descárgalo en Herramientas → Upscaler IA.")
        state = torch.load(self.path, map_location="cpu", weights_only=True)
        state = state.get("params_ema", state.get("params", state))
        net = _build_net()
        net.load_state_dict(state, strict=True)
        net.eval()
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        if self._device == "cuda":
            net = net.half()
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

    # ------------------------------------------------------- inferencia
    def upscale(self, img: Image.Image, outscale: float = 4.0, tile: int = 192, pad: int = 10,
                progress=None, cancel: threading.Event | None = None) -> Image.Image:
        import torch

        if outscale not in (2, 3, 4):
            raise ValueError("La escala debe ser 2, 3 o 4.")
        if max(img.size) * 4 > 8192 * 2:
            raise ValueError("Imagen demasiado grande para ampliar (máx. 4096 px de lado).")
        alpha = img.getchannel("A") if img.mode in ("RGBA", "LA") else None
        rgb = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
        h, w = rgb.shape[:2]
        with self._lock:
            net = self._load()
            dtype = torch.float16 if self._device == "cuda" else torch.float32
            x = torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0)
            out = torch.zeros((1, 3, h * 4, w * 4), dtype=torch.float32)
            tiles = [(ty, tx) for ty in range(0, h, tile) for tx in range(0, w, tile)]
            with torch.inference_mode():
                for i, (ty, tx) in enumerate(tiles):
                    if cancel is not None and cancel.is_set():
                        raise InterruptedError("Cancelado")
                    y0, y1 = max(ty - pad, 0), min(ty + tile + pad, h)
                    x0, x1 = max(tx - pad, 0), min(tx + tile + pad, w)
                    patch = x[:, :, y0:y1, x0:x1].to(self._device, dtype)
                    res = net(patch).float().cpu()
                    oy, ox = (ty - y0) * 4, (tx - x0) * 4
                    th, tw = (min(ty + tile, h) - ty) * 4, (min(tx + tile, w) - tx) * 4
                    out[:, :, ty * 4:ty * 4 + th, tx * 4:tx * 4 + tw] = res[:, :, oy:oy + th, ox:ox + tw]
                    if progress:
                        progress(i + 1, len(tiles))
        arr = (out.squeeze(0).permute(1, 2, 0).clamp(0, 1).numpy() * 255).round().astype(np.uint8)
        result = Image.fromarray(arr)
        if outscale != 4:
            result = result.resize((int(w * outscale), int(h * outscale)), Image.LANCZOS)
        if alpha is not None:
            result.putalpha(alpha.resize(result.size, Image.LANCZOS))
        return result
