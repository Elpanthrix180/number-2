"""Une todas las piezas de MARS.AI (configuración, modelos, galería, motor)."""
from __future__ import annotations

import logging
from pathlib import Path

from config.settings import SecretStore, SettingsStore
from core.system_info import SystemReport, collect
from database.db import Database
from gallery.library import Library
from generator.engine import GenerationJob
from models.manager import ModelManager

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

    @property
    def settings(self):
        return self.store.settings

    def cancel_current(self) -> str:
        if self.current_job and not self.current_job.done:
            self.current_job.cancel()
            return "Cancelando… (se detendrá al terminar el paso actual)"
        return "No hay ninguna generación en curso."
