"""MARS.AI — Transforma tu imaginación en imágenes.

Uso:
    python main.py                 # abre la interfaz en el navegador
    python main.py --no-browser    # no abre el navegador automáticamente
    python main.py --check         # solo muestra el diagnóstico del equipo
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")   # sin telemetría
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")


def main() -> int:
    ap = argparse.ArgumentParser(description="MARS.AI — estudio de generación de imágenes con IA")
    ap.add_argument("--port", type=int, default=7860)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--check", action="store_true", help="mostrar diagnóstico del sistema y salir")
    args = ap.parse_args()

    from core.system_info import collect, format_report

    if args.check:
        print(format_report(collect()))
        return 0

    from config.settings import default_data_dir
    from core.logging_setup import setup_logging

    setup_logging(default_data_dir())
    from config.settings import SLOGAN
    from core.app_context import AppContext
    from core.i18n import t
    from interface.app import launch

    ctx = AppContext()
    print("=" * 60)
    print(f"  MARS.AI — {t(SLOGAN)}")
    print("=" * 60)
    print(format_report(ctx.system))
    print("\n" + t("Imágenes : {path}", path=ctx.settings.output_path))
    print(t("Modelos  : {path}", path=ctx.settings.models_path))
    print("\n" + t("Abre http://127.0.0.1:{port} si el navegador no se abre solo. Ctrl+C para salir.", port=args.port) + "\n")
    launch(ctx, port=args.port, inbrowser=not args.no_browser)
    return 0


if __name__ == "__main__":
    sys.exit(main())
