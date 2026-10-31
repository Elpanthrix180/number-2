import os

import pytest

from core.app_context import AppContext
from core.system_info import GPUInfo, SystemReport
from models.catalog import CATALOG


def fake_system(vram=0.0, ram=16.0):
    gpus = [GPUInfo("GPU", vram, "cuda")] if vram else []
    return SystemReport("Windows 11", "3.11", True, ram, ram, 100, 8, gpus)


@pytest.fixture
def ctx(tmp_path):
    return AppContext(tmp_path, system=fake_system())


def test_catalog_has_required_families():
    fams = {m.family for m in CATALOG}
    assert {"sd15", "sdxl", "flux", "api"} <= fams
    assert all(m.license and m.repo_id for m in CATALOG)


def test_status_not_installed(ctx):
    st = {s.spec.id: s for s in ctx.models.statuses()}
    assert not st["sd15"].installed and not st["sd15"].available
    assert not st["hf-api"].available or ctx.secrets.get("huggingface")


def test_compatibility(tmp_path):
    low = AppContext(tmp_path / "a", system=fake_system(0, 8)).models
    assert low.compatibility(low.spec("sd15")).startswith("Justo")
    assert low.compatibility(low.spec("flux-schnell")) == "No recomendado"
    hi = AppContext(tmp_path / "b", system=fake_system(24, 64)).models
    assert hi.compatibility(hi.spec("flux-schnell")) == "OK"


def test_download_requires_authorization(ctx):
    msg = ctx.models.download("sd15", authorized=False)
    assert "autorización" in msg
    assert not any(ctx.models.models_dir.iterdir())


def test_unavailable_backend_raises(ctx):
    from models.backends import BackendUnavailable
    with pytest.raises(BackendUnavailable):
        ctx.models.backend("sd15")


def test_add_custom_rejects_ckpt(ctx, tmp_path):
    f = tmp_path / "m.ckpt"
    f.write_bytes(b"x")
    assert "❌" in ctx.models.add_custom(str(f), "x", "sd15")
    g = tmp_path / "m.safetensors"
    g.write_bytes(b"x")
    assert "✅" in ctx.models.add_custom(str(g), "Mío", "sdxl")
    assert ctx.models.status(ctx.models.spec("custom-m")).spec.family == "sdxl"


def test_ui_builds(ctx):
    from interface.app import build_ui
    demo = build_ui(ctx)
    assert demo is not None


TINY = "/tmp/claude-0/tiny-sd"


@pytest.mark.skipif(not os.path.isdir(TINY), reason="modelo diminuto de prueba no disponible")
def test_real_diffusers_pipeline(tmp_path):
    import threading
    from models.backends import DiffusersBackend, GenRequest
    from models.catalog import ModelSpec
    spec = ModelSpec(id="tiny", name="Tiny", family="sd15", connection="local", repo_id=TINY,
                     license="test", license_url="", fp16_variant=False)
    be = DiffusersBackend(spec, str(tmp_path), low_power=True)
    imgs = be.generate(GenRequest("panda", width=64, height=64, steps=3, seed=1), lambda a, b: None,
                       threading.Event())
    assert imgs[0].size == (64, 64)
    be.unload()
