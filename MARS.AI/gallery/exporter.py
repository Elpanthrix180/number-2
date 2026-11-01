"""Exportación de la galería a un archivo ZIP.

El ZIP contiene:
  imagenes/0001_<nombre original>.png …   las imágenes (sin recomprimir: los PNG ya lo están)
  metadata.csv                           una fila por imagen (UTF-8 con BOM, se abre bien en Excel)
  metadata.json                          lo mismo en JSON
Solo se incluyen archivos PNG que existen y que creó MARS.AI. Se escribe primero en un
archivo temporal y se renombra al terminar, así nunca queda un ZIP a medias.
"""
from __future__ import annotations

import csv
import io
import json
import shutil
import threading
import zipfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from core.i18n import t
from gallery.library import ImageRecord

KEEP_EXPORTS = 5          # ZIP antiguos que se conservan en la carpeta de exportaciones
CSV_FIELDS = ["id", "file", "created_at", "prompt", "negative", "model", "style", "kind", "width", "height",
              "steps", "cfg", "seed", "seconds", "favorite"]


class ExportCancelled(Exception):
    pass


def _exportable(r: ImageRecord) -> bool:
    p = Path(r.file_path)
    return p.suffix.lower() == ".png" and p.name.startswith("marsai_") and p.is_file()


def estimate_size(records: list[ImageRecord]) -> int:
    return sum(Path(r.file_path).stat().st_size for r in records if _exportable(r))


def export_zip(records: list[ImageRecord], dest_dir: Path, include_metadata: bool = True,
               progress=None, cancel: threading.Event | None = None) -> tuple[Path, int]:
    """Crea el ZIP en dest_dir. Devuelve (ruta del ZIP, número de imágenes incluidas)."""
    items = [r for r in records if _exportable(r)]
    if not items:
        raise ValueError(t("No hay imágenes que exportar con los filtros actuales."))
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    needed = estimate_size(items) * 1.05 + 1_000_000
    if shutil.disk_usage(dest_dir).free < needed:
        raise OSError(t("No hay espacio suficiente en el disco para el ZIP (~{mb} MB).",
                        mb=round(needed / 1024**2)))

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    final = dest_dir / f"marsai_galeria_{stamp}.zip"
    tmp = final.with_suffix(".zip.part")
    rows = []
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_STORED) as zf:
            for i, r in enumerate(items, 1):
                if cancel is not None and cancel.is_set():
                    raise ExportCancelled(t("Exportación cancelada."))
                arcname = f"imagenes/{i:04d}_{Path(r.file_path).name}"
                zf.write(r.file_path, arcname)
                row = {k: v for k, v in asdict(r).items() if k != "file_path"}
                row["file"] = arcname
                rows.append(row)
                if progress:
                    progress(i, len(items))
            if include_metadata:
                buf = io.StringIO()
                w = csv.DictWriter(buf, fieldnames=CSV_FIELDS, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)
                zf.writestr("metadata.csv", "﻿" + buf.getvalue(), compress_type=zipfile.ZIP_DEFLATED)
                zf.writestr("metadata.json", json.dumps(rows, ensure_ascii=False, indent=2),
                            compress_type=zipfile.ZIP_DEFLATED)
        tmp.replace(final)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    _cleanup(dest_dir)
    return final, len(items)


def _cleanup(dest_dir: Path) -> None:
    """Conserva solo los KEEP_EXPORTS ZIP más recientes creados por MARS.AI."""
    zips = sorted(dest_dir.glob("marsai_galeria_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in zips[KEEP_EXPORTS:]:
        old.unlink(missing_ok=True)
