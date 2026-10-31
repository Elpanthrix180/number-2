"""Carga la configuración de ONIX desde config.json."""
import json
from pathlib import Path

RUTA = Path(__file__).with_name("config.json")


def cargar(ruta=RUTA):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)
