"""Acceso a SQLite para la biblioteca de imágenes."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS images (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path   TEXT NOT NULL UNIQUE,
    prompt      TEXT NOT NULL DEFAULT '',
    negative    TEXT NOT NULL DEFAULT '',
    model       TEXT NOT NULL DEFAULT '',
    style       TEXT NOT NULL DEFAULT '',
    width       INTEGER, height INTEGER,
    steps       INTEGER, cfg REAL, seed INTEGER,
    kind        TEXT NOT NULL DEFAULT 'txt2img',
    seconds     REAL,
    favorite    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_images_created ON images(created_at);
CREATE INDEX IF NOT EXISTS idx_images_fav ON images(favorite);
"""


class Database:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return cur

    def query(self, sql: str, params: tuple | dict = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def close(self):
        with self._lock:
            self._conn.close()
