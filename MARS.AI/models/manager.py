"""Administrador de modelos: estado, compatibilidad, descarga autorizada y carga."""
from __future__ import annotations

import logging
import shutil
import threading
from dataclasses import dataclass
from pathlib import Path

from config.settings import SettingsStore, SecretStore
from core.system_info import SystemReport
from models.backends import Backend, BackendUnavailable, DiffusersBackend, HFInferenceBackend
from models.catalog import CATALOG, ModelSpec, custom_spec, get_spec

log = logging.getLogger(__name__)


@dataclass
class ModelStatus:
    spec: ModelSpec
    installed: bool
    available: bool
    state: str          # texto para la interfaz
    compatibility: str  # "OK", "Justo", "No recomendado"


class ModelManager:
    def __init__(self, store: SettingsStore, secrets: SecretStore, system: SystemReport):
        self.store = store
        self.secrets = secrets
        self.system = system
        self._active: Backend | None = None
        self._active_id: str | None = None
        self._lock = threading.Lock()
        self.download_progress: dict[str, str] = {}

    # ---------------------------------------------------------- catálogo
    @property
    def models_dir(self) -> Path:
        p = self.store.settings.models_path
        p.mkdir(parents=True, exist_ok=True)
        return p

    def all_specs(self) -> list[ModelSpec]:
        return [*CATALOG, *[custom_spec(e) for e in self.store.settings.custom_models]]

    def spec(self, model_id: str) -> ModelSpec:
        s = get_spec(model_id)
        if s:
            return s
        for e in self.store.settings.custom_models:
            if e["id"] == model_id:
                return custom_spec(e)
        raise KeyError(model_id)

    def is_installed(self, spec: ModelSpec) -> bool:
        if spec.connection == "hf-api":
            return True
        if spec.connection == "local-file":
            return Path(spec.repo_id).is_file()
        folder = self.models_dir / ("models--" + spec.repo_id.replace("/", "--"))
        if not folder.is_dir():
            return False
        return any(folder.glob("snapshots/*/model_index.json")) and (folder / ".marsai_complete").exists()

    def torch_ready(self) -> bool:
        try:
            import importlib.util

            return all(importlib.util.find_spec(m) is not None for m in ("torch", "diffusers"))
        except Exception:
            return False

    def compatibility(self, spec: ModelSpec) -> str:
        if spec.connection == "hf-api":
            return "OK"
        vram = max((g.vram_gb for g in self.system.gpus if g.backend == "cuda"), default=0.0)
        ram = self.system.ram_total_gb or 0
        if ram and ram < spec.min_ram_gb * 0.75:
            return "No recomendado"
        if vram >= spec.min_vram_gb:
            return "OK"
        if vram == 0:
            return "Justo (CPU, lento)" if spec.family == "sd15" else "No recomendado"
        return "Justo" if vram >= spec.min_vram_gb * 0.6 else "No recomendado"

    def status(self, spec: ModelSpec) -> ModelStatus:
        installed = self.is_installed(spec)
        if spec.connection == "hf-api":
            has_token = bool(self.secrets.get("huggingface"))
            state = "🟢 Conectado (token configurado)" if has_token else "🟡 Requiere token de Hugging Face"
            return ModelStatus(spec, True, has_token, state, "OK")
        if spec.id in self.download_progress:
            return ModelStatus(spec, False, False, f"⏳ {self.download_progress[spec.id]}", self.compatibility(spec))
        if not self.torch_ready():
            return ModelStatus(spec, installed, False, "🔴 Falta PyTorch/Diffusers", self.compatibility(spec))
        if installed:
            loaded = " (cargado en memoria)" if self._active_id == spec.id else ""
            return ModelStatus(spec, True, True, f"🟢 Instalado{loaded}", self.compatibility(spec))
        return ModelStatus(spec, False, False, "⚪ No instalado", self.compatibility(spec))

    def statuses(self) -> list[ModelStatus]:
        return [self.status(s) for s in self.all_specs()]

    def available_choices(self) -> list[tuple[str, str]]:
        """(etiqueta, id) para el selector de modelos; incluye no disponibles marcados."""
        out = []
        for st in self.statuses():
            mark = "✅" if st.available else "⛔"
            out.append((f"{mark} {st.spec.name}", st.spec.id))
        return out

    # ----------------------------------------------------------- descarga
    def download(self, model_id: str, authorized: bool, token: str | None = None) -> str:
        spec = self.spec(model_id)
        if spec.connection != "local":
            return "Este modelo no se descarga (es una API o un archivo local)."
        if not authorized:
            return "⚠️ Debes marcar la casilla de autorización antes de descargar."
        if self.is_installed(spec):
            return f"{spec.name} ya está instalado."
        free = shutil.disk_usage(self.models_dir).free / 1024**3
        if free < spec.download_gb * 1.1:
            return f"❌ Espacio insuficiente: se necesitan ~{spec.download_gb} GB y hay {free:.1f} GB libres."
        try:
            from huggingface_hub import snapshot_download
        except ImportError:
            return "❌ Falta huggingface_hub. Ejecuta install_windows.bat."
        self.download_progress[spec.id] = f"Descargando (~{spec.download_gb} GB)…"
        try:
            path = snapshot_download(
                repo_id=spec.repo_id, cache_dir=str(self.models_dir),
                allow_patterns=list(spec.allow_patterns) or None,
                token=token or self.secrets.get("huggingface"),
            )
            (Path(path).parent.parent / ".marsai_complete").write_text("ok")
            log.info("Modelo %s descargado", spec.id)
            return f"✅ {spec.name} instalado correctamente."
        except Exception as exc:
            log.error("Descarga fallida de %s: %s", spec.id, type(exc).__name__)
            hint = " (modelo restringido: acepta la licencia en su página y configura tu token)" \
                if "401" in str(exc) or "403" in str(exc) or "gated" in str(exc).lower() else ""
            return f"❌ Error al descargar: {type(exc).__name__}{hint}"
        finally:
            self.download_progress.pop(spec.id, None)

    def delete(self, model_id: str) -> str:
        spec = self.spec(model_id)
        if spec.connection != "local":
            return "Solo se pueden eliminar modelos descargados."
        if self._active_id == model_id:
            self.unload()
        folder = self.models_dir / ("models--" + spec.repo_id.replace("/", "--"))
        if folder.is_dir() and folder.resolve().is_relative_to(self.models_dir.resolve()):
            shutil.rmtree(folder)
            return f"🗑️ {spec.name} eliminado."
        return "No estaba instalado."

    def add_custom(self, path: str, name: str, base: str) -> str:
        p = Path(path.strip().strip('"'))
        if p.suffix.lower() != ".safetensors" or not p.is_file():
            return "❌ Indica la ruta a un archivo .safetensors existente (no se aceptan .ckpt por seguridad)."
        mid = "custom-" + "".join(c if c.isalnum() else "-" for c in p.stem.lower())[:40]
        models = [e for e in self.store.settings.custom_models if e["id"] != mid]
        models.append({"id": mid, "name": name or p.stem, "path": str(p), "base": base})
        self.store.update(custom_models=models)
        return f"✅ Modelo añadido: {name or p.stem}"

    # -------------------------------------------------------------- carga
    def backend(self, model_id: str) -> Backend:
        with self._lock:
            if self._active is not None and self._active_id == model_id:
                if isinstance(self._active, DiffusersBackend):
                    self._active.low_power = self.store.settings.low_power_mode
                return self._active
            spec = self.spec(model_id)
            st = self.status(spec)
            if spec.connection == "hf-api":
                be: Backend = HFInferenceBackend(spec, self.secrets.get("huggingface"),
                                                 self.store.settings.hf_api_model)
            else:
                if not st.available:
                    raise BackendUnavailable(f"{spec.name}: {st.state}. Revísalo en «Modelos IA».")
                be = DiffusersBackend(spec, str(self.models_dir), self.store.settings.low_power_mode)
            if self._active is not None:  # libera el modelo anterior (bajo consumo)
                self._active.unload()
            self._active, self._active_id = be, model_id
            return be

    def unload(self) -> str:
        with self._lock:
            if self._active is not None:
                self._active.unload()
            self._active, self._active_id = None, None
        return "Memoria liberada."
