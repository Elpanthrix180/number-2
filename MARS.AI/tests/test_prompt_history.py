import pytest

from database.db import Database
from gallery import prompt_history as PH
from gallery.prompt_history import PromptHistory


@pytest.fixture
def hist(tmp_path):
    return PromptHistory(Database(tmp_path / "h.db"))


def test_record_and_dedup(hist):
    a = hist.record("Un panda guerrero", "borroso", "Anime", "sd15", 768, "16:9", 30, 6.5, -1, 1234)
    assert a.uses == 1 and a.resolution == 768 and a.last_seed == 1234
    b = hist.record("  Un panda guerrero ", "borroso", "Anime", "sdxl", 1024, "1:1", 20, 7.0, 5, 5)
    assert b.id == a.id and b.uses == 2 and b.model == "sdxl" and b.steps == 20   # ajustes actualizados
    c = hist.record("Un panda guerrero", "borroso", "Fantasía")                     # otro estilo = otra entrada
    assert c.id != a.id and hist.count() == 2
    assert hist.record("   ") is None and hist.count() == 2


def test_search_order_and_pin(hist):
    first = hist.record("castillo flotante")
    hist.record("ciudad cyberpunk")
    assert [e.prompt for e in hist.search()] == ["ciudad cyberpunk", "castillo flotante"]  # más reciente primero
    assert hist.toggle_pin(first.id) is True
    assert hist.search()[0].id == first.id                    # los fijados van arriba
    assert [e.id for e in hist.search(pinned_only=True)] == [first.id]
    assert [e.prompt for e in hist.search("cyber")] == ["ciudad cyberpunk"]
    assert hist.search("%") == [] and hist.search("'; DROP TABLE prompts; --") == []
    assert hist.count() == 2


def test_rename_delete_clear(hist):
    a = hist.record("retrato al óleo")
    b = hist.record("paisaje nevado")
    hist.rename(a.id, "  Mi retrato  ")
    assert hist.get(a.id).name == "Mi retrato" and hist.get(a.id).title() == "Mi retrato"
    hist.toggle_pin(a.id)
    assert hist.clear(keep_pinned=True) == 1 and hist.get(a.id) and hist.get(b.id) is None
    assert hist.delete(a.id) and hist.count() == 0


def test_prune_keeps_pinned(hist, monkeypatch):
    monkeypatch.setattr(PH, "MAX_UNPINNED", 3)
    keep = hist.record("fijado")
    hist.toggle_pin(keep.id)
    for i in range(6):
        hist.record(f"prompt {i}")
    prompts = {e.prompt for e in hist.search()}
    assert prompts == {"fijado", "prompt 3", "prompt 4", "prompt 5"}


def test_title_truncates():
    e = PH.PromptEntry(1, "x " * 100, "", "", "", 512, "1:1", 25, 7.0, -1, -1, 1, True, "", "", "")
    assert e.title(20).startswith("📌 ") and e.title(20).endswith("…") and len(e.title(20)) <= 23
