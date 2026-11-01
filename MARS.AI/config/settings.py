"""Configuración persistente de MARS.AI y almacenamiento seguro de claves API.

- Los ajustes se guardan en JSON en la carpeta de datos del usuario
  (%APPDATA%\\MARS.AI en Windows).
- Las claves API se guardan en el Administrador de credenciales de Windows a
  través de `keyring`. Nunca se escriben en el JSON ni en los registros.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field, asdict, fields
from pathlib import Path
from core.i18n import N_, t

APP_NAME = "MARS.AI"
SLOGAN = N_("Transforma tu imaginación en imágenes.")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KEYRING_SERVICE = "MARS.AI"

log = logging.getLogger(__name__)


def default_data_dir() -> Path:
    env = os.environ.get("MARSAI_DATA_DIR")
    if env:
        return Path(env)
    if os.name == "nt" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / APP_NAME
    return Path.home() / ".marsai"


@dataclass
class Settings:
    language: str = "es"
    theme: str = "oscuro"
    output_dir: str = ""
    models_dir: str = ""
    default_model: str = "sd15"
    default_style: str = "Ninguno"
    default_steps: int = 25
    default_cfg: float = 7.0
    default_resolution: int = 512
    default_aspect: str = "1:1"
    low_power_mode: bool = True
    unload_after_generation: bool = False
    max_batch: int = 4
    hf_api_model: str = "black-forest-labs/FLUX.1-schnell"
    custom_models: list = field(default_factory=list)  # [{id, name, path, base}]
    accepted_api_cost_warning: bool = False

    # ------------------------------------------------------------------ paths
    @property
    def output_path(self) -> Path:
        return Path(self.output_dir) if self.output_dir else self._base() / "outputs"

    @property
    def models_path(self) -> Path:
        return Path(self.models_dir) if self.models_dir else self._base() / "models"

    def _base(self) -> Path:
        return getattr(self, "_data_dir", None) or default_data_dir()


class SettingsStore:
    """Carga/guarda Settings en disco de forma segura entre hilos."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir) if data_dir else default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file = self.data_dir / "settings.json"
        self._lock = threading.Lock()
        self.settings = self._load()
        self.settings._data_dir = self.data_dir

    def _load(self) -> Settings:
        if not self.file.exists():
            return Settings()
        try:
            raw = json.loads(self.file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            log.warning("settings.json dañado, se usan valores por defecto: %s", exc)
            return Settings()
        valid = {f.name for f in fields(Settings)}
        return Settings(**{k: v for k, v in raw.items() if k in valid})

    def save(self) -> None:
        with self._lock:
            tmp = self.file.with_suffix(".tmp")
            tmp.write_text(json.dumps(asdict(self.settings), indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.file)

    def update(self, **changes) -> Settings:
        valid = {f.name for f in fields(Settings)}
        for k, v in changes.items():
            if k not in valid:
                raise KeyError(f"Ajuste desconocido: {k}")
            setattr(self.settings, k, v)
        self.save()
        return self.settings


# ------------------------------------------------------------------ API keys
class SecretStore:
    """Guarda claves API en el almacén seguro del sistema (keyring).

    Si keyring no está disponible se usa solo la variable de entorno
    correspondiente (p. ej. HF_TOKEN) y nunca se escribe en disco en claro.
    """

    ENV_FALLBACK = {"huggingface": "HF_TOKEN"}

    def __init__(self):
        try:
            import keyring  # type: ignore

            self._kr = keyring
        except Exception:
            self._kr = None

    @property
    def secure_backend_available(self) -> bool:
        return self._kr is not None

    def get(self, name: str) -> str | None:
        if self._kr is not None:
            try:
                val = self._kr.get_password(KEYRING_SERVICE, name)
                if val:
                    return val
            except Exception as exc:  # backend del sistema no disponible
                log.debug("keyring no disponible: %s", type(exc).__name__)
        env = self.ENV_FALLBACK.get(name)
        return os.environ.get(env) if env else None

    def set(self, name: str, value: str) -> bool:
        if self._kr is None:
            return False
        try:
            if value:
                self._kr.set_password(KEYRING_SERVICE, name, value)
            else:
                self.delete(name)
            return True
        except Exception as exc:
            log.warning("No se pudo guardar la clave '%s' (%s)", name, type(exc).__name__)
            return False

    def delete(self, name: str) -> None:
        if self._kr is None:
            return
        try:
            self._kr.delete_password(KEYRING_SERVICE, name)
        except Exception:
            pass

    @staticmethod
    def mask(value: str | None) -> str:
        if not value:
            return t("(no configurada)")
        return f"••••••••{value[-4:]}" if len(value) > 8 else "••••"
