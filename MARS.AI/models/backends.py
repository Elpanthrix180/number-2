"""Backends de generación.

- DiffusersBackend: modelos locales con PyTorch + Diffusers (carga bajo demanda).
- HFInferenceBackend: API de Hugging Face (opcional, requiere token).

Todos los imports pesados (torch, diffusers) se hacen dentro de las funciones
para que la interfaz arranque rápido y con poca RAM.
"""
from __future__ import annotations

import gc
import logging
import threading
from dataclasses import dataclass, field
from typing import Callable

from PIL import Image

from models.catalog import ModelSpec
from core.i18n import t

log = logging.getLogger(__name__)


class GenerationCancelled(Exception):
    pass


class BackendUnavailable(RuntimeError):
    """El modelo no está instalado/conectado o faltan recursos."""


@dataclass
class GenRequest:
    prompt: str
    negative: str = ""
    width: int = 512
    height: int = 512
    steps: int = 25
    cfg: float = 7.0
    seed: int = -1
    num_images: int = 1
    mode: str = "txt2img"           # txt2img | img2img | inpaint
    init_image: Image.Image | None = None
    mask_image: Image.Image | None = None
    strength: float = 0.6
    extra: dict = field(default_factory=dict)


ProgressFn = Callable[[int, int], None]


class Backend:
    spec: ModelSpec

    def generate(self, req: GenRequest, progress: ProgressFn, cancel: threading.Event) -> list[Image.Image]:
        raise NotImplementedError

    def supports(self, mode: str) -> bool:
        return mode == "txt2img"

    def unload(self) -> None:
        pass


# ---------------------------------------------------------------- Diffusers
class DiffusersBackend(Backend):
    def __init__(self, spec: ModelSpec, models_dir: str, low_power: bool = True):
        self.spec = spec
        self.models_dir = models_dir
        self.low_power = low_power
        self._pipes: dict[str, object] = {}
        self._lock = threading.Lock()
        self.device = "cpu"

    def supports(self, mode: str) -> bool:
        if self.spec.family == "flux":
            return mode in ("txt2img", "img2img", "inpaint")
        return mode in ("txt2img", "img2img", "inpaint")

    # -- carga
    def _load_base(self):
        try:
            import torch
            from diffusers import AutoPipelineForText2Image, StableDiffusionPipeline, \
                StableDiffusionXLPipeline
        except ImportError as exc:
            raise BackendUnavailable(
                "PyTorch/Diffusers no están instalados. Ejecuta install_windows.bat."
            ) from exc

        cuda = torch.cuda.is_available()
        self.device = "cuda" if cuda else "cpu"
        dtype = torch.float16 if cuda else torch.float32
        spec = self.spec
        log.info("Cargando %s en %s", spec.name, self.device)

        if spec.connection == "local-file":
            cls = StableDiffusionXLPipeline if spec.family == "sdxl" else StableDiffusionPipeline
            pipe = cls.from_single_file(spec.repo_id, torch_dtype=dtype)
        else:
            kwargs = dict(torch_dtype=dtype if spec.family != "flux" else torch.bfloat16,
                          cache_dir=self.models_dir, local_files_only=True)
            if spec.fp16_variant:
                kwargs["variant"] = "fp16"
            if spec.family == "sd15":
                kwargs["safety_checker"] = None
                kwargs["requires_safety_checker"] = False
            try:
                pipe = AutoPipelineForText2Image.from_pretrained(spec.repo_id, **kwargs)
            except (OSError, EnvironmentError) as exc:
                raise BackendUnavailable(
                    f"{spec.name} no está descargado. Instálalo desde «Modelos IA»."
                ) from exc

        # optimizaciones de memoria. El attention slicing solo compensa en GPU con poca
        # VRAM: en CPU con PyTorch 2 (SDPA) lo hace hasta 5 veces más lento.
        if cuda and self.low_power:
            try:
                pipe.enable_attention_slicing()
            except Exception:
                pass
        try:
            pipe.vae.enable_tiling()
        except Exception:
            pass
        if cuda and (self.low_power or spec.family == "flux"):
            try:
                pipe.enable_model_cpu_offload()
            except Exception:
                pipe.to("cuda")
        else:
            pipe.to(self.device)
        try:
            pipe.set_progress_bar_config(disable=True)
        except Exception:
            pass
        return pipe

    def _pipe(self, mode: str):
        with self._lock:
            if "txt2img" not in self._pipes:
                self._pipes["txt2img"] = self._load_base()
            if mode == "txt2img":
                return self._pipes["txt2img"]
            if mode not in self._pipes:
                from diffusers import AutoPipelineForImage2Image, AutoPipelineForInpainting
                base = self._pipes["txt2img"]
                cls = AutoPipelineForImage2Image if mode == "img2img" else AutoPipelineForInpainting
                derived = cls.from_pipe(base)  # reutiliza pesos, sin RAM extra
                try:
                    derived.set_progress_bar_config(disable=True)
                except Exception:
                    pass
                self._pipes[mode] = derived
            return self._pipes[mode]

    def generate(self, req, progress, cancel):
        import torch

        pipe = self._pipe(req.mode)
        gen_device = "cpu" if self.low_power or self.device == "cpu" else self.device
        seed = req.seed if req.seed is not None and req.seed >= 0 else int(torch.seed() % 2**32)
        generator = torch.Generator(gen_device).manual_seed(seed)
        total = max(1, req.steps if req.mode == "txt2img" else int(req.steps * req.strength) or 1)

        def on_step(p, step, timestep, kwargs):
            if cancel.is_set():
                p._interrupt = True
            progress(min(step + 1, total), total)
            return kwargs

        args = dict(prompt=req.prompt, num_inference_steps=req.steps,
                    num_images_per_prompt=req.num_images, generator=generator,
                    callback_on_step_end=on_step)
        if self.spec.family != "flux":
            args["negative_prompt"] = req.negative or None
            args["guidance_scale"] = req.cfg
        else:
            args["guidance_scale"] = req.cfg
            args["max_sequence_length"] = 256
        if req.mode == "txt2img":
            args.update(width=req.width, height=req.height)
        else:
            args["image"] = req.init_image
            args["strength"] = req.strength
            if req.mode == "inpaint":
                args["mask_image"] = req.mask_image
                args.update(width=req.width, height=req.height)

        with torch.inference_mode():
            result = pipe(**args)
        if cancel.is_set():
            raise GenerationCancelled()
        req.extra["seed_used"] = seed
        return list(result.images)

    def unload(self):
        with self._lock:
            self._pipes.clear()
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass


# --------------------------------------------------------- Hugging Face API
class HFInferenceBackend(Backend):
    def __init__(self, spec: ModelSpec, token: str | None, model: str):
        self.spec = spec
        self.token = token
        self.model = model

    def generate(self, req, progress, cancel):
        if not self.token:
            raise BackendUnavailable(t("Falta el token de Hugging Face. Añádelo en Configuración → APIs."))
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise BackendUnavailable(t("Falta huggingface_hub. Ejecuta install_windows.bat.")) from exc
        client = InferenceClient(token=self.token, timeout=180)
        images = []
        for i in range(req.num_images):
            if cancel.is_set():
                raise GenerationCancelled()
            progress(i, req.num_images)
            kwargs = dict(model=self.model, width=req.width, height=req.height,
                          num_inference_steps=req.steps)
            if req.negative:
                kwargs["negative_prompt"] = req.negative
            if req.cfg:
                kwargs["guidance_scale"] = req.cfg
            if req.seed is not None and req.seed >= 0:
                kwargs["seed"] = req.seed + i
            try:
                images.append(client.text_to_image(req.prompt, **kwargs))
            except Exception as exc:
                # nunca mostrar cabeceras ni el token
                raise BackendUnavailable(t("La API de Hugging Face respondió con error: {err}",
                                           err=f"{type(exc).__name__}: {str(exc)[:200]}")) from None
        progress(req.num_images, req.num_images)
        return images
