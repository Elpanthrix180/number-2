"""Historial de prompts reutilizables.

Cada generación correcta guarda el prompt tal como lo escribió el usuario (antes de
aplicar el estilo o el potenciador) junto con sus ajustes. Un mismo prompt
(texto + negativo + estilo) no se duplica: se actualizan sus ajustes y se cuenta un uso.
Los prompts fijados no se borran nunca automáticamente; el resto se limita a MAX_UNPINNED.
"""
from __future__ import annotations

from dataclasses import dataclass

from database.db import Database, like_pattern

MAX_UNPINNED = 200
MAX_PROMPT_CHARS = 4000

SCHEMA = """
CREATE TABLE IF NOT EXISTS prompts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt      TEXT NOT NULL,
    negative    TEXT NOT NULL DEFAULT '',
    style       TEXT NOT NULL DEFAULT '',
    model       TEXT NOT NULL DEFAULT '',
    resolution  INTEGER NOT NULL DEFAULT 512,
    aspect      TEXT NOT NULL DEFAULT '1:1',
    steps       INTEGER NOT NULL DEFAULT 25,
    cfg         REAL NOT NULL DEFAULT 7.0,
    seed        INTEGER NOT NULL DEFAULT -1,
    last_seed   INTEGER NOT NULL DEFAULT -1,
    uses        INTEGER NOT NULL DEFAULT 1,
    pinned      INTEGER NOT NULL DEFAULT 0,
    name        TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    last_used   TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE (prompt, negative, style)
);
CREATE INDEX IF NOT EXISTS idx_prompts_last ON prompts(last_used);
"""


@dataclass
class PromptEntry:
    id: int
    prompt: str
    negative: str
    style: str
    model: str
    resolution: int
    aspect: str
    steps: int
    cfg: float
    seed: int
    last_seed: int
    uses: int
    pinned: bool
    name: str
    created_at: str
    last_used: str

    @classmethod
    def from_row(cls, row) -> "PromptEntry":
        d = dict(row)
        d["pinned"] = bool(d["pinned"])
        return cls(**d)

    def title(self, width: int = 70) -> str:
        text = self.name or " ".join(self.prompt.split())
        if len(text) > width:
            text = text[: width - 1] + "…"
        return f"{'📌 ' if self.pinned else ''}{text}"


class PromptHistory:
    def __init__(self, db: Database):
        self.db = db
        with db._lock:
            db._conn.executescript(SCHEMA)
            db._conn.commit()

    # --------------------------------------------------------- escritura
    def record(self, prompt: str, negative: str = "", style: str = "", model: str = "", resolution: int = 512,
               aspect: str = "1:1", steps: int = 25, cfg: float = 7.0, seed: int = -1,
               last_seed: int = -1) -> PromptEntry | None:
        prompt = (prompt or "").strip()[:MAX_PROMPT_CHARS]
        negative = (negative or "").strip()[:MAX_PROMPT_CHARS]
        if not prompt:
            return None
        style = style or ""
        self.db.execute(
            """INSERT INTO prompts(prompt, negative, style, model, resolution, aspect, steps, cfg, seed, last_seed)
               VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(prompt, negative, style) DO UPDATE SET
                 model=excluded.model, resolution=excluded.resolution, aspect=excluded.aspect,
                 steps=excluded.steps, cfg=excluded.cfg, seed=excluded.seed, last_seed=excluded.last_seed,
                 uses=uses+1, last_used=datetime('now','localtime')""",
            (prompt, negative, style, model, int(resolution), aspect, int(steps), float(cfg), int(seed),
             int(last_seed)),
        )
        self._prune()
        rows = self.db.query("SELECT * FROM prompts WHERE prompt=? AND negative=? AND style=?",
                             (prompt, negative, style))
        return PromptEntry.from_row(rows[0]) if rows else None

    def _prune(self):
        self.db.execute(
            """DELETE FROM prompts WHERE pinned=0 AND id NOT IN (
                 SELECT id FROM prompts WHERE pinned=0 ORDER BY last_used DESC, id DESC LIMIT ?)""",
            (MAX_UNPINNED,))

    def toggle_pin(self, entry_id: int) -> bool:
        self.db.execute("UPDATE prompts SET pinned = 1 - pinned WHERE id=?", (entry_id,))
        e = self.get(entry_id)
        return bool(e and e.pinned)

    def rename(self, entry_id: int, name: str) -> None:
        self.db.execute("UPDATE prompts SET name=? WHERE id=?", ((name or "").strip()[:80], entry_id))

    def delete(self, entry_id: int) -> bool:
        return self.db.execute("DELETE FROM prompts WHERE id=?", (entry_id,)).rowcount > 0

    def clear(self, keep_pinned: bool = True) -> int:
        sql = "DELETE FROM prompts" + (" WHERE pinned=0" if keep_pinned else "")
        return self.db.execute(sql).rowcount

    # ----------------------------------------------------------- lectura
    def get(self, entry_id: int) -> PromptEntry | None:
        rows = self.db.query("SELECT * FROM prompts WHERE id=?", (entry_id,))
        return PromptEntry.from_row(rows[0]) if rows else None

    def search(self, text: str = "", pinned_only: bool = False, limit: int = 100) -> list[PromptEntry]:
        sql, params = "SELECT * FROM prompts WHERE 1=1", []
        if text and text.strip():
            like = like_pattern(text.strip())
            sql += (" AND (prompt LIKE ? ESCAPE '\\' OR negative LIKE ? ESCAPE '\\' OR name LIKE ? ESCAPE '\\'"
                    " OR style LIKE ? ESCAPE '\\')")
            params += [like, like, like, like]
        if pinned_only:
            sql += " AND pinned=1"
        sql += " ORDER BY pinned DESC, last_used DESC, id DESC LIMIT ?"
        params.append(int(limit))
        return [PromptEntry.from_row(r) for r in self.db.query(sql, tuple(params))]

    def count(self) -> int:
        return int(self.db.query("SELECT COUNT(*) AS n FROM prompts")[0]["n"])
