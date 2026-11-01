"""Biblioteca personal: guardar, buscar, filtrar, favoritos y eliminar imágenes."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, PngImagePlugin

from database.db import Database, like_pattern
from core.i18n import t

log = logging.getLogger(__name__)

MAX_IMPORT_PIXELS = 64_000_000  # protección ante imágenes «bomba»
Image.MAX_IMAGE_PIXELS = MAX_IMPORT_PIXELS


@dataclass
class ImageRecord:
    id: int
    file_path: str
    prompt: str
    negative: str
    model: str
    style: str
    width: int
    height: int
    steps: int
    cfg: float
    seed: int
    kind: str
    seconds: float
    favorite: bool
    created_at: str

    @classmethod
    def from_row(cls, row) -> "ImageRecord":
        d = dict(row)
        d["favorite"] = bool(d["favorite"])
        return cls(**d)

    def caption(self) -> str:
        star = "⭐ " if self.favorite else ""
        return f"{star}#{self.id} · {t(self.model)} · {self.created_at[:16]}"


class Library:
    def __init__(self, db: Database, output_dir: Path):
        self.db = db
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def set_output_dir(self, path: Path):
        self.output_dir = Path(path)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, image: Image.Image, *, prompt: str = "", negative: str = "", model: str = "",
             style: str = "", steps: int | None = None, cfg: float | None = None, seed: int | None = None,
             kind: str = "txt2img", seconds: float | None = None) -> ImageRecord:
        day = datetime.now().strftime("%Y-%m-%d")
        folder = self.output_dir / day
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%H%M%S_%f")
        path = folder / f"marsai_{kind}_{stamp}.png"
        meta = PngImagePlugin.PngInfo()
        meta.add_text("marsai", json.dumps({"prompt": prompt, "negative": negative, "model": model,
                                            "style": style, "steps": steps, "cfg": cfg, "seed": seed},
                                           ensure_ascii=False))
        image.convert("RGBA" if image.mode in ("RGBA", "LA") else "RGB").save(path, pnginfo=meta)
        cur = self.db.execute(
            "INSERT INTO images(file_path,prompt,negative,model,style,width,height,steps,cfg,seed,kind,seconds)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (str(path), prompt, negative, model, style, image.width, image.height, steps, cfg, seed, kind,
             seconds),
        )
        return self.get(cur.lastrowid)

    def get(self, image_id: int) -> ImageRecord | None:
        rows = self.db.query("SELECT * FROM images WHERE id=?", (image_id,))
        return ImageRecord.from_row(rows[0]) if rows else None

    def search(self, text: str = "", favorites_only: bool = False, date_from: str = "",
               date_to: str = "", limit: int = 200) -> list[ImageRecord]:
        sql = "SELECT * FROM images WHERE 1=1"
        params: list = []
        if text.strip():
            sql += " AND (prompt LIKE ? ESCAPE '\\' OR model LIKE ? ESCAPE '\\' OR style LIKE ? ESCAPE '\\')"
            like = like_pattern(text.strip())
            params += [like, like, like]
        if favorites_only:
            sql += " AND favorite=1"
        if date_from.strip():
            sql += " AND date(created_at) >= date(?)"
            params.append(date_from.strip())
        if date_to.strip():
            sql += " AND date(created_at) <= date(?)"
            params.append(date_to.strip())
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(int(limit))
        recs = [ImageRecord.from_row(r) for r in self.db.query(sql, tuple(params))]
        return [r for r in recs if Path(r.file_path).exists()]

    def toggle_favorite(self, image_id: int) -> bool:
        self.db.execute("UPDATE images SET favorite = 1 - favorite WHERE id=?", (image_id,))
        rec = self.get(image_id)
        return bool(rec and rec.favorite)

    def delete(self, image_id: int) -> bool:
        rec = self.get(image_id)
        if not rec:
            return False
        p = Path(rec.file_path)
        # solo borra archivos dentro de una carpeta de MARS.AI con nombre esperado
        if p.exists() and p.name.startswith("marsai_") and p.suffix == ".png":
            p.unlink()
        self.db.execute("DELETE FROM images WHERE id=?", (image_id,))
        return True

    def count(self) -> int:
        return int(self.db.query("SELECT COUNT(*) AS n FROM images")[0]["n"])


def load_user_image(path_or_img) -> Image.Image:
    """Carga una imagen de usuario de forma segura (formatos de imagen comunes, tamaño acotado)."""
    if isinstance(path_or_img, Image.Image):
        img = path_or_img
    else:
        p = Path(path_or_img)
        if p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            raise ValueError(t("Formato no admitido. Usa PNG, JPG, WEBP o BMP."))
        img = Image.open(p)
        img.load()
    if img.width * img.height > MAX_IMPORT_PIXELS:
        raise ValueError(t("La imagen es demasiado grande."))
    return img
