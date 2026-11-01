import csv
import io
import json
import threading
import zipfile

import pytest
from PIL import Image

from database.db import Database
from gallery import exporter
from gallery.exporter import ExportCancelled, export_zip
from gallery.library import Library


@pytest.fixture
def lib(tmp_path):
    lib = Library(Database(tmp_path / "t.db"), tmp_path / "out")
    lib.save(Image.new("RGB", (32, 32), "red"), prompt="Un panda «guerrero» con ñ", model="SD 1.5", style="Anime",
             seed=7)
    lib.save(Image.new("RGB", (16, 16), "blue"), prompt="castillo", model="SDXL")
    return lib


def test_export_contents(lib, tmp_path):
    recs = lib.search()
    path, n = export_zip(recs, tmp_path / "exp")
    assert n == 2 and path.name.startswith("marsai_galeria_") and path.suffix == ".zip"
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        assert sorted(x for x in names if x.startswith("imagenes/"))[0].startswith("imagenes/0001_marsai_")
        assert {"metadata.csv", "metadata.json"} <= set(names)
        meta = json.loads(zf.read("metadata.json"))
        assert {m["prompt"] for m in meta} == {"Un panda «guerrero» con ñ", "castillo"}
        assert all(m["file"] in names for m in meta) and "file_path" not in meta[0]   # sin rutas locales
        text = zf.read("metadata.csv").decode("utf-8")
        assert text.startswith("﻿")                                              # BOM para Excel
        rows = list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
        assert len(rows) == 2 and rows[0]["file"].startswith("imagenes/")
        img = Image.open(io.BytesIO(zf.read(meta[0]["file"])))
        assert img.size in {(32, 32), (16, 16)}
        assert zf.testzip() is None
    assert not list((tmp_path / "exp").glob("*.part"))


def test_export_without_metadata_and_filters(lib, tmp_path):
    path, n = export_zip(lib.search("panda"), tmp_path / "exp", include_metadata=False)
    with zipfile.ZipFile(path) as zf:
        assert n == 1 and zf.namelist() == [zf.namelist()[0]] and zf.namelist()[0].startswith("imagenes/")


def test_export_skips_missing_and_foreign_files(lib, tmp_path):
    recs = lib.search()
    from pathlib import Path
    Path(recs[0].file_path).unlink()                      # archivo borrado a mano
    foreign = tmp_path / "secreto.txt"
    foreign.write_text("no")
    recs[1].file_path = str(foreign)                      # ruta ajena a MARS.AI
    with pytest.raises(ValueError):
        export_zip(recs, tmp_path / "exp")
    assert export_zip(lib.search(), tmp_path / "exp2")[1] == 1


def test_export_cancel_leaves_nothing(lib, tmp_path):
    ev = threading.Event()
    ev.set()
    with pytest.raises(ExportCancelled):
        export_zip(lib.search(), tmp_path / "exp", cancel=ev)
    assert list((tmp_path / "exp").iterdir()) == []


def test_export_keeps_last_n(lib, tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, "KEEP_EXPORTS", 2)
    stamps = iter(f"2026-01-0{i}_000000" for i in range(1, 10))

    class FakeDT:
        @staticmethod
        def now():
            class S:
                def strftime(self, fmt):
                    return next(stamps)
            return S()
    monkeypatch.setattr(exporter, "datetime", FakeDT)
    import os
    for i in range(4):
        p, _ = export_zip(lib.search(), tmp_path / "exp")
        os.utime(p, (1_000_000 + i, 1_000_000 + i))
    left = sorted(p.name for p in (tmp_path / "exp").glob("*.zip"))
    assert left == ["marsai_galeria_2026-01-03_000000.zip", "marsai_galeria_2026-01-04_000000.zip"]
