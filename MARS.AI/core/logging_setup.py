"""Registro de eventos con filtro que oculta claves API y tokens."""
from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

_SECRET_PATTERNS = [
    re.compile(r"hf_[A-Za-z0-9]{10,}"),                    # tokens Hugging Face
    re.compile(r"sk-[A-Za-z0-9_\-]{10,}"),                 # estilo OpenAI/otros
    re.compile(r"(?i)(api[_-]?key|token|authorization|bearer)(\s*[=:]\s*|\s+)([^\s,;'\"]+)"),
]


def redact(text: str) -> str:
    for pat in _SECRET_PATTERNS[:2]:
        text = pat.sub("[CLAVE OCULTA]", text)
    return _SECRET_PATTERNS[2].sub(lambda m: f"{m.group(1)}{m.group(2)}[CLAVE OCULTA]", text)


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        record.msg = redact(msg)
        record.args = ()
        return True


def setup_logging(data_dir: Path, level: int = logging.INFO) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(level)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    fh = RotatingFileHandler(data_dir / "marsai.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    sh = logging.StreamHandler()
    for h in (fh, sh):
        h.setFormatter(fmt)
        h.addFilter(RedactingFilter())
        root.addHandler(h)
    # librerías muy verbosas
    for noisy in ("httpx", "urllib3", "gradio", "huggingface_hub"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
