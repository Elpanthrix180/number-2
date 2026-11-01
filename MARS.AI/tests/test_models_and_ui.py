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


ESR = "/tmp/claude-0/esrm"


def test_realesrgan_requires_authorization(tmp_path):
    from tools.realesrgan import RealESRGAN
    u = RealESRGAN(tmp_path)
    assert not u.installed()
    assert "autorización" in u.download(False)
    assert not (tmp_path / "realesrgan").exists()
    with pytest.raises(RuntimeError):
        from PIL import Image
        u.upscale(Image.new("RGB", (8, 8)))


@pytest.mark.skipif(not os.path.isdir(ESR), reason="pesos de Real-ESRGAN no disponibles")
def test_realesrgan_real_weights():
    import threading
    from PIL import Image
    from tools.realesrgan import RealESRGAN
    u = RealESRGAN(ESR)
    img = Image.new("RGBA", (40, 30), (200, 50, 50, 128))
    assert u.upscale(img, 4, tile=16).size == (160, 120)
    assert u.upscale(img, 2).mode == "RGBA"
    ev = threading.Event(); ev.set()
    with pytest.raises(InterruptedError):
        u.upscale(img, 4, cancel=ev)


GFP = "/tmp/claude-0/gfpm"


def test_face_restore_requires_authorization(tmp_path):
    from PIL import Image
    from tools.face_restore import FaceRestorer
    fr = FaceRestorer(tmp_path)
    assert not fr.installed()
    assert "autorización" in fr.download(False)
    assert not (tmp_path / "gfpgan").exists()
    with pytest.raises(RuntimeError):
        fr.restore(Image.new("RGB", (64, 64)))


@pytest.mark.skipif(not os.path.isdir(GFP), reason="pesos de GFPGAN no disponibles")
def test_face_restore_real_weights():
    import threading
    import numpy as np
    from PIL import Image
    from tools.face_restore import FaceRestorer, sha256_file, GFPGAN_FILE
    fr = FaceRestorer(GFP)
    assert sha256_file(fr.path(GFPGAN_FILE)) == GFPGAN_FILE.sha256
    face = Image.open("/tmp/claude-0/face_in.png") if os.path.exists("/tmp/claude-0/face_in.png") else None
    if face is not None:
        out, n = fr.restore(face, 0.6)
        assert n == 1 and out.size == face.size
        diff = np.abs(np.asarray(out, np.float32) - np.asarray(face, np.float32))
        assert diff[60:200, 190:310].mean() > 3   # la cara cambia
        assert diff[440:, :80].mean() < 0.5        # el fondo lejano no
    blank, n = fr.restore(Image.new("RGBA", (96, 96), (90, 90, 90, 200)))
    assert n == 0 and blank.mode == "RGBA"
    ev = threading.Event(); ev.set()
    if face is not None:
        with pytest.raises(InterruptedError):
            fr.restore(face, cancel=ev)


BGM = "/tmp/claude-0/bgm"


def test_bg_remover_requires_authorization(tmp_path):
    from PIL import Image
    from tools.background_remover import BackgroundRemover, _parse_color
    br = BackgroundRemover(tmp_path)
    assert "autorización" in br.download("rapido", False)
    assert "desconocido" in br.download("nope", True)
    assert not (tmp_path / "background").exists()
    with pytest.raises(RuntimeError):
        br.remove(Image.new("RGB", (32, 32)), "rapido")
    assert _parse_color("#0f0") == (0, 255, 0, 255)
    assert _parse_color("rgb(1, 2, 3)") == (1, 2, 3, 255)
    assert _parse_color("basura") == (255, 255, 255, 255)


@pytest.mark.skipif(not os.path.isdir(BGM), reason="modelos de quitafondos no disponibles")
@pytest.mark.parametrize("model_id", ["rapido", "calidad"])
def test_bg_remover_real_models(model_id):
    import numpy as np
    from PIL import Image, ImageDraw
    from tools.background_remover import BackgroundRemover
    img = Image.new("RGB", (300, 200), (235, 235, 235))
    ImageDraw.Draw(img).ellipse((100, 50, 200, 150), fill=(200, 30, 30))
    br = BackgroundRemover(BGM)
    out = br.remove(img, model_id)
    a = np.asarray(out.getchannel("A"))
    assert out.mode == "RGBA" and out.size == img.size
    assert a[100, 150] > 200 and a[10, 10] < 50       # objeto opaco, esquina transparente
    assert br.remove(img, model_id, "color", "#0000ff").getpixel((5, 5)) == (0, 0, 255)
    assert br.remove(img, model_id, "mascara").mode == "RGB"
    hard = np.asarray(br.remove(img, model_id, threshold=128).getchannel("A"))
    assert set(np.unique(hard)) <= {0, 255}


def test_theme_js_and_setting(tmp_path):
    from interface.app import THEMES, theme_js
    assert set(THEMES) == {"oscuro", "claro", "sistema"}
    assert "marsApplyTheme('claro')" in theme_js("claro")
    assert "marsApplyTheme('oscuro')" in theme_js("<script>malo")   # valores no válidos -> oscuro
    ctx = AppContext(tmp_path, system=fake_system())
    assert ctx.settings.theme == "oscuro"
