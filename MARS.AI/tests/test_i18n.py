"""Comprueba que todos los textos marcados con t()/N_() tengan traducción al inglés."""
import ast
import re
from pathlib import Path

import pytest

from core import i18n
from core.i18n_en import EN

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = re.compile(r"\{(\w*)\}")


def collect_keys() -> dict[str, str]:
    keys = {}
    for f in ROOT.rglob("*.py"):
        rel = f.relative_to(ROOT).as_posix()
        if rel.startswith(("tests/", ".venv/")) or "gfpgan_arch" in rel:
            continue
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Call) and getattr(node.func, "id", None) in ("t", "N_") and node.args
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                keys[node.args[0].value] = f"{rel}:{node.lineno}"
    return keys


KEYS = collect_keys()


def test_some_keys_found():
    assert len(KEYS) > 200


def test_every_key_translated():
    missing = [f"{where}: {k!r}" for k, where in KEYS.items() if k not in EN]
    assert not missing, "Faltan traducciones:\n" + "\n".join(missing)


@pytest.mark.parametrize("key", sorted(k for k in KEYS if k in EN))
def test_placeholders_match(key):
    assert sorted(PLACEHOLDER.findall(key)) == sorted(PLACEHOLDER.findall(EN[key])), key


def test_no_stale_translations():
    stale = [k for k in EN if k not in KEYS]
    assert not stale, "Traducciones sin uso:\n" + "\n".join(map(repr, stale))


def test_translations_look_english():
    spanish = re.compile(r"[ñ¿¡]|\b(el|los|las|de la|para|con|una|está|imagen|modelo)\b", re.I)
    bad = [(k, v) for k, v in EN.items() if spanish.search(v)]
    assert not bad, bad


def test_t_switches_language():
    try:
        i18n.set_language("en")
        assert i18n.t("Listo.") == EN["Listo."]
        assert i18n.t("{n} imagen(es).", n=3) == EN["{n} imagen(es)."].format(n=3)
        assert i18n.t("texto sin traducir") == "texto sin traducir"
        i18n.set_language("es")
        assert i18n.t("Listo.") == "Listo."
        assert i18n.set_language("xx") == "es"
    finally:
        i18n.set_language("es")
