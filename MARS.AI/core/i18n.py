"""Traducción de la interfaz (estilo gettext).

El texto original en español es la clave: el código sigue siendo legible y, si
faltara una traducción, se muestra el español. Las traducciones al inglés están en
`core/i18n_en.py`; `tests/test_i18n.py` comprueba que no falte ninguna.

    t("Hola {nombre}", nombre="Ana")   # traduce y luego aplica .format()
    N_("Texto")                          # solo marca un texto para traducir más tarde
"""
from __future__ import annotations

LANGUAGES = {"es": "Español", "en": "English"}
_lang = "es"


def set_language(lang: str) -> str:
    global _lang
    _lang = lang if lang in LANGUAGES else "es"
    return _lang


def get_language() -> str:
    return _lang


def t(text: str, **kwargs) -> str:
    if _lang == "en":
        from core.i18n_en import EN

        text = EN.get(text, text)
    return text.format(**kwargs) if kwargs else text


def N_(text: str) -> str:  # noqa: N802 (convención gettext)
    """Marca un texto como traducible sin traducirlo aún (se traduce al mostrarlo con t())."""
    return text
