"""Une todas las piezas de MARS.AI (configuración, modelos, galería, motor)."""
from __future__ import annotations

import logging
import threading
from pathlib import Path

from config.settings import SecretStore, SettingsStore
from core.system_info import SystemReport, collect
from database.db import Database
from gallery.library import Library
from generator.engine import GenerationJob
from models.manager import ModelManager
from tools.background_remover import BackgroundRemover
from tools.face_restore import FaceRestorer
from tools.realesrgan import RealESRGAN

log = logging.getLogger(__name__)


class AppContext:
    def __init__(self, data_dir: Path | None = None, system: SystemReport | None = None):
        self.store = SettingsStore(data_dir)
        self.secrets = SecretStore()
        s = self.store.settings
        self.system = system or collect(str(self.store.data_dir))
        self.db = Database(self.store.data_dir / "marsai.db")
        self.library = Library(self.db, s.output_path)
        self.models = ModelManager(self.store, self.secrets, self.system)
        self.current_job: GenerationJob | None = None
        self.upscaler = RealESRGAN(s.models_path)
        self.upscale_cancel = threading.Event()
        self.faces = FaceRestorer(s.models_path)
        self.faces_cancel = threading.Event()
        self.bgremover = BackgroundRemover(s.models_path)

    def free_memory(self) -> str:
        self.models.unload()
        self.upscaler.unload()
        self.faces.unload()
        self.bgremover.unload()
        return "Memoria liberada (difusión, Real-ESRGAN, GFPGAN y quitafondos)."

    @property
    def settings(self):
        return self.store.settings

    def cancel_current(self) -> str:
        if self.current_job and not self.current_job.done:
            self.current_job.cancel()
            return "Cancelando… (se detendrá al terminar el paso actual)"
        return "No hay ninguna generación en curso."
