import logging
import threading

import pytest
from PIL import Image

from config.settings import SecretStore, SettingsStore
from core.logging_setup import RedactingFilter, redact
from core.system_info import collect, format_report
from database.db import Database
from gallery.library import Library, load_user_image
from generator.engine import GenerationJob, build_request, dimensions
from generator.prompt_enhancer import enhance_prompt, translate_es_en
from generator.styles import STYLES, apply_style, get_style, style_names
from models.backends import Backend, BackendUnavailable, GenerationCancelled
from tools import image_tools as T


def test_system_report():
    rep = collect(".")
    assert rep.cpu_count >= 1 and rep.disk_free_gb > 0
    assert "Python" in format_report(rep)


def test_settings_roundtrip(tmp_path):
    st = SettingsStore(tmp_path)
    st.update(default_steps=33, low_power_mode=False)
    again = SettingsStore(tmp_path)
    assert again.settings.default_steps == 33 and again.settings.low_power_mode is False
    with pytest.raises(KeyError):
        st.update(nope=1)
    assert "token" not in (tmp_path / "settings.json").read_text().lower()


def test_secret_mask():
    assert SecretStore.mask(None) == "(no configurada)"
    assert SecretStore.mask("hf_abcdefghijkl").endswith("ijkl")


def test_log_redaction(caplog):
    assert "hf_" not in redact("token hf_ABCDEFGHIJKLMNOP usado")
    assert "secreto123" not in redact("api_key=secreto123")
    rec = logging.LogRecord("x", logging.INFO, "", 0, "clave %s", ("hf_ABCDEFGHIJKLMNOPQ",), None)
    RedactingFilter().filter(rec)
    assert "hf_ABC" not in rec.getMessage()


def test_styles():
    assert len(STYLES) == 20
    assert all(s.examples for s in STYLES)
    assert style_names()[0] == "Ninguno"
    p, n = apply_style("un gato", "", "Anime")
    assert "anime" in p and "blurry" in n
    assert get_style("inexistente").name == "Ninguno"


def test_prompt_enhancer():
    out = translate_es_en("Un panda guerrero con armadura futurista en una ciudad japonesa de noche")
    assert "warrior" in out and "armor" in out and "japanese" in out and "night" in out
    assert "masterpiece" in enhance_prompt("un gato")
    assert enhance_prompt("") == ""


@pytest.mark.parametrize("aspect", ["1:1", "16:9", "9:16", "4:3", "3:4"])
def test_dimensions(aspect):
    w, h = dimensions(768, aspect, 1024)
    assert w % 8 == 0 and h % 8 == 0 and max(w, h) <= 1024
    if aspect == "16:9":
        assert w > h


def test_build_request_validation():
    with pytest.raises(ValueError):
        build_request("  ", "", "Ninguno", 512, "1:1", 1, -1, 20, 7, max_batch=4)
    r = build_request("gato", "", "Fotorealismo", 512, "1:1", 99, 5, 500, 99, max_batch=4)
    assert r.num_images == 4 and r.steps == 150 and r.cfg == 30


class FakeBackend(Backend):
    def __init__(self, fail=None):
        self.fail = fail

    def generate(self, req, progress, cancel):
        for i in range(req.steps):
            if cancel.is_set():
                raise GenerationCancelled()
            progress(i + 1, req.steps)
            threading.Event().wait(0.01)
        if self.fail:
            raise self.fail
        req.extra["seed_used"] = 123
        return [Image.new("RGB", (req.width, req.height), "purple") for _ in range(req.num_images)]


def test_job_success_and_cancel():
    req = build_request("gato", "", "Ninguno", 512, "1:1", 2, -1, 10, 7)
    res = GenerationJob(FakeBackend(), req).start().wait(5)
    assert len(res.images) == 2 and res.seed == 123 and res.error is None
    req = build_request("gato", "", "Ninguno", 512, "1:1", 1, -1, 200, 7)
    job = GenerationJob(FakeBackend(), req).start()
    job.cancel()
    assert job.wait(5).cancelled


def test_job_errors():
    req = build_request("gato", "", "Ninguno", 512, "1:1", 1, -1, 2, 7)
    assert "falta" in GenerationJob(FakeBackend(BackendUnavailable("Falta modelo")), req).start().wait(5).error.lower()
    res = GenerationJob(FakeBackend(RuntimeError("CUDA out of memory")), req).start().wait(5)
    assert "insuficiente" in res.error


def test_library(tmp_path):
    lib = Library(Database(tmp_path / "t.db"), tmp_path / "out")
    rec = lib.save(Image.new("RGB", (64, 64)), prompt="panda guerrero", model="SD 1.5", style="Anime", seed=1)
    lib.save(Image.new("RGB", (64, 64)), prompt="castillo", model="SDXL")
    assert lib.count() == 2
    assert [r.id for r in lib.search("panda")] == [rec.id]
    assert lib.toggle_favorite(rec.id) is True
    assert len(lib.search(favorites_only=True)) == 1
    assert len(lib.search(date_from="2000-01-01", date_to="2999-01-01")) == 2
    assert lib.search(date_from="2999-01-01") == []
    assert lib.delete(rec.id) and lib.count() == 1


def test_load_user_image_rejects(tmp_path):
    bad = tmp_path / "x.exe"
    bad.write_bytes(b"MZ")
    with pytest.raises(ValueError):
        load_user_image(bad)


def test_classic_tools():
    img = Image.new("RGB", (40, 30), (120, 80, 60))
    assert T.upscale_classic(img, 2).size == (80, 60)
    with pytest.raises(ValueError):
        T.upscale_classic(img, 5)
    assert T.enhance(img).size == img.size
    assert T.restore(img).size == img.size


def test_outpaint_and_mask():
    img = Image.new("RGB", (60, 60), "red")
    canvas, mask = T.prepare_outpaint(img, 20, 20, 0, 5)
    assert canvas.width % 8 == 0 and canvas.height % 8 == 0
    assert mask.getpixel((0, 0)) == 255 and mask.getpixel((50, 30)) == 0
    layer = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
    layer.paste((255, 255, 255, 255), (10, 10, 20, 20))
    bg, m = T.mask_from_editor({"background": img, "layers": [layer]})
    assert m.getpixel((15, 15)) == 255 and m.getpixel((40, 40)) == 0
    with pytest.raises(ValueError):
        T.mask_from_editor({"background": img, "layers": []})


def test_fit_for_diffusion():
    out = T.fit_for_diffusion(Image.new("RGB", (2000, 1000)), 768)
    assert max(out.size) <= 768 and out.width % 8 == 0


def test_paths_follow_data_dir(tmp_path):
    st = SettingsStore(tmp_path)
    assert st.settings.models_path == tmp_path / "models"
    assert st.settings.output_path == tmp_path / "outputs"


def test_library_search_is_literal(tmp_path):
    lib = Library(Database(tmp_path / "t.db"), tmp_path / "out")
    lib.save(Image.new("RGB", (8, 8)), prompt="gato 100% feliz", model="SD 1.5")
    lib.save(Image.new("RGB", (8, 8)), prompt="perro_azul", model="SD 1.5")
    lib.save(Image.new("RGB", (8, 8)), prompt="otra cosa", model="SD 1.5")
    assert [r.prompt for r in lib.search("%")] == ["gato 100% feliz"]
    assert [r.prompt for r in lib.search("_")] == ["perro_azul"]
    assert len(lib.search("")) == 3
