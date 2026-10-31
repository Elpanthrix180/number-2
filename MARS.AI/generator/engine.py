"""Motor de generación: valida parámetros, aplica estilos, ejecuta el backend
en un hilo con progreso y cancelación, y guarda los resultados en la galería."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field

from PIL import Image

from generator.styles import apply_style
from models.backends import Backend, BackendUnavailable, GenerationCancelled, GenRequest

log = logging.getLogger(__name__)

ASPECTS = {"1:1": (1, 1), "16:9": (16, 9), "9:16": (9, 16), "4:3": (4, 3), "3:4": (3, 4)}
RESOLUTIONS = [512, 768, 1024]


def dimensions(base: int, aspect: str, max_side: int = 1024) -> tuple[int, int]:
    """Calcula ancho/alto con área ≈ base², múltiplos de 8 y lado máximo acotado."""
    aw, ah = ASPECTS.get(aspect, (1, 1))
    area = base * base
    w = (area * aw / ah) ** 0.5
    h = w * ah / aw
    scale = min(1.0, max_side / max(w, h))
    w, h = w * scale, h * scale
    return max(64, int(w // 8 * 8)), max(64, int(h // 8 * 8))


@dataclass
class JobResult:
    images: list[Image.Image] = field(default_factory=list)
    seed: int = -1
    seconds: float = 0.0
    error: str | None = None
    cancelled: bool = False


class GenerationJob:
    """Ejecuta una generación en segundo plano."""

    def __init__(self, backend: Backend, req: GenRequest):
        self.backend = backend
        self.req = req
        self.cancel_event = threading.Event()
        self.step = 0
        self.total = max(1, req.steps)
        self.result: JobResult | None = None
        self.started = time.perf_counter()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> "GenerationJob":
        self._thread.start()
        return self

    def _progress(self, step: int, total: int):
        self.step, self.total = step, max(1, total)

    def _run(self):
        res = JobResult()
        try:
            res.images = self.backend.generate(self.req, self._progress, self.cancel_event)
            res.seed = int(self.req.extra.get("seed_used", self.req.seed))
        except GenerationCancelled:
            res.cancelled = True
        except BackendUnavailable as exc:
            res.error = str(exc)
        except MemoryError:
            res.error = "Memoria insuficiente. Activa el modo de bajo consumo o reduce la resolución."
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            if "out of memory" in msg.lower():
                res.error = ("Memoria de GPU insuficiente. Reduce la resolución o el número de imágenes, "
                             "o activa el modo de bajo consumo.")
            else:
                log.exception("Error de generación")
                res.error = f"{type(exc).__name__}: {msg[:300]}"
        res.seconds = time.perf_counter() - self.started
        self.result = res

    @property
    def done(self) -> bool:
        return self.result is not None

    @property
    def elapsed(self) -> float:
        return time.perf_counter() - self.started

    def cancel(self):
        self.cancel_event.set()

    def wait(self, timeout: float | None = None) -> JobResult | None:
        self._thread.join(timeout)
        return self.result


def build_request(prompt: str, negative: str, style: str, base_res: int, aspect: str,
                  num_images: int, seed: int, steps: int, cfg: float, max_side: int = 1024,
                  max_batch: int = 4) -> GenRequest:
    if not prompt or not prompt.strip():
        raise ValueError("Escribe una descripción (prompt) para generar.")
    p, n = apply_style(prompt, negative or "", style)
    w, h = dimensions(int(base_res), aspect, max_side)
    return GenRequest(
        prompt=p, negative=n, width=w, height=h,
        steps=int(min(max(steps, 1), 150)), cfg=float(min(max(cfg, 0.0), 30.0)),
        seed=int(seed) if seed is not None else -1,
        num_images=int(min(max(num_images, 1), max_batch)),
    )
