"""Catálogo de modelos conocidos (solo fuentes oficiales de Hugging Face).

Los tamaños son aproximados para los archivos que descarga MARS.AI (variante
fp16 cuando existe). Las licencias deben revisarse en la página del modelo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from core.i18n import N_


@dataclass(frozen=True)
class ModelSpec:
    id: str
    name: str
    family: str            # "sd15", "sdxl", "flux"
    connection: str        # "local" o "hf-api"
    repo_id: str
    license: str
    license_url: str
    download_gb: float = 0.0
    min_vram_gb: float = 0.0
    min_ram_gb: float = 8.0
    default_resolution: int = 512
    default_steps: int = 25
    default_cfg: float = 7.0
    max_resolution: int = 768
    fp16_variant: bool = True
    gated: bool = False
    notes: str = ""
    allow_patterns: tuple[str, ...] = field(default_factory=tuple)


_SD_PATTERNS_FP16 = ("model_index.json", "*.json", "*.txt", "*.fp16.safetensors")

CATALOG: list[ModelSpec] = [
    ModelSpec(
        id="sd15", name="Stable Diffusion 1.5", family="sd15", connection="local",
        repo_id="stable-diffusion-v1-5/stable-diffusion-v1-5",
        license="CreativeML OpenRAIL-M",
        license_url="https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5",
        download_gb=2.6, min_vram_gb=4, min_ram_gb=8, default_resolution=512, max_resolution=768,
        notes=N_("El más ligero. Recomendado para equipos modestos y para CPU."),
        allow_patterns=_SD_PATTERNS_FP16,
    ),
    ModelSpec(
        id="sdxl-turbo", name="SDXL Turbo", family="sdxl", connection="local",
        repo_id="stabilityai/sdxl-turbo",
        license=N_("Stability AI Community / no comercial (revisar)"),
        license_url="https://huggingface.co/stabilityai/sdxl-turbo",
        download_gb=7.0, min_vram_gb=8, min_ram_gb=16, default_resolution=512, max_resolution=768,
        default_steps=4, default_cfg=0.0,
        notes=N_("Muy rápido (1–4 pasos). Uso comercial sujeto a la licencia de Stability AI."),
        allow_patterns=_SD_PATTERNS_FP16,
    ),
    ModelSpec(
        id="sdxl", name="Stable Diffusion XL 1.0", family="sdxl", connection="local",
        repo_id="stabilityai/stable-diffusion-xl-base-1.0",
        license="CreativeML OpenRAIL++-M",
        license_url="https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0",
        download_gb=7.0, min_vram_gb=8, min_ram_gb=16, default_resolution=1024, max_resolution=1024,
        default_steps=30,
        notes=N_("Alta calidad a 1024×1024. Necesita GPU con 8 GB+ de VRAM."),
        allow_patterns=_SD_PATTERNS_FP16,
    ),
    ModelSpec(
        id="flux-schnell", name="FLUX.1 [schnell]", family="flux", connection="local",
        repo_id="black-forest-labs/FLUX.1-schnell",
        license="Apache 2.0",
        license_url="https://huggingface.co/black-forest-labs/FLUX.1-schnell",
        download_gb=34.0, min_vram_gb=16, min_ram_gb=32, default_resolution=1024, max_resolution=1024,
        default_steps=4, default_cfg=0.0, fp16_variant=False,
        notes=N_("Calidad excelente pero muy pesado. Solo para GPUs de 16 GB+ (o 12 GB con descarga a CPU, lento)."),
        allow_patterns=("model_index.json", "*.json", "*.txt", "*.model",
                        "transformer/*.safetensors", "text_encoder/*.safetensors",
                        "text_encoder_2/*.safetensors", "vae/*.safetensors"),
    ),
    ModelSpec(
        id="hf-api", name=N_("API de Hugging Face (Inference Providers)"), family="api", connection="hf-api",
        repo_id="black-forest-labs/FLUX.1-schnell",
        license=N_("Según el modelo elegido"),
        license_url="https://huggingface.co/docs/inference-providers/pricing",
        min_ram_gb=2, default_resolution=1024, max_resolution=1024, default_steps=4, default_cfg=0.0,
        notes=N_("Genera en la nube. Requiere token gratuito de Hugging Face. Las cuentas gratuitas tienen un "
               "crédito mensual pequeño; al agotarlo las peticiones fallan o pueden tener coste. "
               "Consulta las condiciones actuales antes de usarla."),
    ),
]

_BY_ID = {m.id: m for m in CATALOG}


def get_spec(model_id: str) -> ModelSpec | None:
    return _BY_ID.get(model_id)


def custom_spec(entry: dict) -> ModelSpec:
    """Crea un ModelSpec para un archivo .safetensors local añadido por el usuario."""
    base = entry.get("base", "sd15")
    is_xl = base == "sdxl"
    return ModelSpec(
        id=entry["id"], name=entry.get("name") or entry["id"], family=base, connection="local-file",
        repo_id=entry["path"], license=N_("Según el autor del archivo"), license_url="",
        min_vram_gb=8 if is_xl else 4, min_ram_gb=16 if is_xl else 8,
        default_resolution=1024 if is_xl else 512, max_resolution=1024 if is_xl else 768,
        notes=N_("Modelo local añadido por el usuario (archivo único)."),
    )
