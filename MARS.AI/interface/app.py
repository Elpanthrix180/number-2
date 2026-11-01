"""Interfaz gráfica de MARS.AI (Gradio, se abre en el navegador como app local)."""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

import gradio as gr
from PIL import Image

from config.settings import APP_NAME, SLOGAN
from core.app_context import AppContext
from core.system_info import format_report
from gallery.library import load_user_image
from generator.engine import ASPECTS, RESOLUTIONS, GenerationJob, build_request
from generator.prompt_enhancer import enhance_prompt
from generator.styles import STYLES, get_style, style_names
from models.backends import BackendUnavailable, GenRequest
from tools import image_tools as T
from tools import face_restore as FR
from tools import realesrgan as RE

log = logging.getLogger(__name__)
CSS_FILE = Path(__file__).with_name("theme.css")
PAGES = ["Inicio", "Crear imagen", "Explorar estilos", "Mis creaciones", "Favoritos",
         "Herramientas", "Modelos IA", "Configuración"]
ICONS = ["🏠", "✨", "🎨", "🖼️", "⭐", "🛠️", "🧠", "⚙️"]
FORCE_DARK_JS = """() => { document.body.classList.add('dark');
  const u = new URL(window.location); if (u.searchParams.get('__theme') !== 'dark') {
  u.searchParams.set('__theme','dark'); window.history.replaceState({}, '', u); } }"""


def progress_html(step: int, total: int, label: str) -> str:
    pct = int(100 * step / max(1, total))
    return (f"<div class='mars-status'>{label}</div>"
            f"<div style='height:8px;border-radius:6px;background:#1f1f33;overflow:hidden;margin-top:6px'>"
            f"<div style='width:{pct}%;height:100%;background:linear-gradient(90deg,#8b5cf6,#3b82f6);"
            f"transition:width .3s'></div></div>")


def build_ui(ctx: AppContext) -> gr.Blocks:
    s = ctx.settings

    # =========================================================== helpers
    def model_choices():
        return ctx.models.available_choices()

    def run_job(backend, req: GenRequest, label: str):
        """Generador común: ejecuta un trabajo y emite (html_progreso, imágenes|None, job)."""
        job = GenerationJob(backend, req).start()
        ctx.current_job = job
        while not job.done:
            yield progress_html(job.step, job.total,
                                f"⏳ {label}: paso {job.step}/{job.total} · {job.elapsed:.1f} s"), None, job
            time.sleep(0.4)
        res = job.result
        if ctx.settings.unload_after_generation:
            ctx.models.unload()
        if res.cancelled:
            yield progress_html(0, 1, f"⛔ Cancelado tras {res.seconds:.1f} s"), None, job
        elif res.error:
            yield progress_html(0, 1, f"❌ {res.error}"), None, job
        else:
            yield progress_html(1, 1, f"✅ {label}: terminado en {res.seconds:.1f} s · seed {res.seed}"), \
                res.images, job

    def generate(prompt, negative, model_id, style, res, aspect, n, seed, steps, cfg, auto_enhance):
        try:
            spec = ctx.models.spec(model_id)
            p = enhance_prompt(prompt) if auto_enhance else prompt
            req = build_request(p, negative, style, int(res), aspect, int(n), int(seed), int(steps), float(cfg),
                                max_side=spec.max_resolution, max_batch=ctx.settings.max_batch)
            backend = ctx.models.backend(model_id)
        except (ValueError, BackendUnavailable, KeyError) as exc:
            yield progress_html(0, 1, f"❌ {exc}"), gr.update(), gr.update()
            return
        yield progress_html(0, req.steps, f"Preparando {spec.name} ({req.width}×{req.height})… "
                            "la primera vez puede tardar en cargar el modelo."), gr.update(), gr.update()
        for html, images, job in run_job(backend, req, "Generación"):
            if images is None:
                yield html, gr.update(), gr.update()
            else:
                paths = []
                for img in images:
                    rec = ctx.library.save(img, prompt=req.prompt, negative=req.negative, model=spec.name,
                                           style=style, steps=req.steps, cfg=req.cfg, seed=job.result.seed,
                                           kind="txt2img", seconds=round(job.result.seconds, 1))
                    paths.append((rec.file_path, rec.caption()))
                yield html, paths, recent_gallery()

    def recent_gallery():
        return [(r.file_path, r.caption()) for r in ctx.library.search(limit=12)]

    def ai_tool(kind: str, image, prompt, negative, model_id, strength, steps, cfg, seed, extra=None):
        """img2img / variations / inpaint / outpaint con el modelo de difusión elegido."""
        try:
            spec = ctx.models.spec(model_id)
            if spec.connection == "hf-api":
                raise BackendUnavailable("Esta herramienta necesita un modelo local instalado (no la API).")
            backend = ctx.models.backend(model_id)
            mode = "img2img" if kind in ("img2img", "variations") else "inpaint"
            if not backend.supports(mode):
                raise BackendUnavailable(f"{spec.name} no admite {mode}.")
            mask = None
            if kind == "inpaint":
                image, mask = T.mask_from_editor(image)
            elif image is None:
                raise ValueError("Sube una imagen de referencia.")
            if kind == "outpaint":
                image, mask = T.prepare_outpaint(load_user_image(image), *extra)
            image = load_user_image(image)
            max_side = spec.max_resolution
            if kind in ("inpaint", "outpaint"):
                fitted = T.fit_for_diffusion(image, max_side)
                mask = mask.resize(fitted.size)
                image = fitted
            else:
                image = T.fit_for_diffusion(image, max_side)
            req = GenRequest(prompt=prompt or "high quality", negative=negative or "", width=image.width,
                             height=image.height, steps=int(steps), cfg=float(cfg), seed=int(seed),
                             num_images=3 if kind == "variations" else 1, mode=mode, init_image=image,
                             mask_image=mask, strength=1.0 if kind == "outpaint" else float(strength))
        except (ValueError, BackendUnavailable, KeyError) as exc:
            yield progress_html(0, 1, f"❌ {exc}"), gr.update()
            return
        for html, images, job in run_job(backend, req, kind):
            if images is None:
                yield html, gr.update()
            else:
                out = []
                for img in images:
                    rec = ctx.library.save(img, prompt=req.prompt, negative=req.negative, model=spec.name,
                                           steps=req.steps, cfg=req.cfg, seed=job.result.seed, kind=kind,
                                           seconds=round(job.result.seconds, 1))
                    out.append((rec.file_path, rec.caption()))
                yield html, out

    def classic_tool(fn, image, *args, kind="tool"):
        if image is None:
            return None, "❌ Sube una imagen primero."
        try:
            t0 = time.perf_counter()
            out = fn(load_user_image(image), *args)
            rec = ctx.library.save(out, prompt=f"[{kind}]", model="Herramienta clásica", kind=kind,
                                   seconds=round(time.perf_counter() - t0, 2))
            return out, f"✅ Listo en {rec.seconds} s · {out.width}×{out.height} · guardado como #{rec.id}"
        except Exception as exc:  # noqa: BLE001
            return None, f"❌ {exc}"

    # ============================================================== UI
    theme = gr.themes.Base(primary_hue="violet", secondary_hue="blue", neutral_hue="slate",
                           font=[gr.themes.GoogleFont("Inter"), "Segoe UI", "sans-serif"])
    with gr.Blocks(title=f"{APP_NAME} — {SLOGAN}") as demo:
        demo.mars_theme, demo.mars_css, demo.mars_js = theme, CSS_FILE.read_text(encoding="utf-8"), FORCE_DARK_JS
        gr.HTML(f"<div id='mars-header'><h1>{APP_NAME}</h1><p>{SLOGAN}</p></div>")
        with gr.Row():
            with gr.Column(scale=0, min_width=200, elem_id="mars-sidebar"):
                nav_buttons = [gr.Button(f"{i}  {p}", size="sm") for i, p in zip(ICONS, PAGES)]
                gr.HTML("<hr style='border-color:#262640'>")
                mem_btn = gr.Button("🧹 Liberar memoria", size="sm")
                mem_msg = gr.Markdown(elem_classes="mars-muted")
            with gr.Column(scale=5):
                pages = {}

                # ---------------------------------------------- Inicio / Crear
                def generator_panel(full: bool):
                    with gr.Group(elem_classes="mars-card"):
                        prompt = gr.Textbox(label="Descripción (prompt)", lines=4, elem_id="mars-prompt",
                                            placeholder="Un panda guerrero con armadura futurista en una ciudad "
                                                        "japonesa de noche, iluminación cinematográfica…")
                        negative = gr.Textbox(label="Descripción negativa (lo que NO quieres)", lines=2,
                                              visible=full, placeholder="borroso, deformado, texto…")
                    with gr.Row():
                        style = gr.Dropdown(style_names(), value=s.default_style, label="Estilo")
                        model = gr.Dropdown(model_choices(), value=s.default_model, label="Modelo")
                    with gr.Accordion("Configuración de generación", open=full):
                        with gr.Row():
                            res = gr.Dropdown([(f"{r} × {r}", r) for r in RESOLUTIONS] + [("Personalizada…", 0)],
                                              value=s.default_resolution, label="Resolución")
                            custom_res = gr.Slider(256, 1536, value=640, step=64, label="Resolución personalizada",
                                                   visible=False)
                            aspect = gr.Dropdown(list(ASPECTS), value=s.default_aspect, label="Relación de aspecto")
                            n = gr.Slider(1, 4, value=1, step=1, label="Número de imágenes")
                        with gr.Row():
                            seed = gr.Number(value=-1, precision=0, label="Seed (-1 = aleatorio)")
                            steps = gr.Slider(1, 80, value=s.default_steps, step=1, label="Steps")
                            cfg = gr.Slider(0, 20, value=s.default_cfg, step=0.5, label="CFG Scale")
                        auto_enh = gr.Checkbox(False, label="Mejorar prompt automáticamente (traduce al inglés y "
                                                            "añade calidad)")
                    with gr.Row():
                        gen_btn = gr.Button("🚀 GENERAR IMAGEN", elem_id="mars-generate", scale=3)
                        cancel_btn = gr.Button("⛔ CANCELAR", elem_id="mars-cancel", scale=1)
                        enh_btn = gr.Button("🪄 Mejorar prompt", scale=1)
                    status = gr.HTML(progress_html(0, 1, "Listo."))
                    preview = gr.Gallery(label="Vista previa", columns=2, height=520 if full else 380,
                                         format="png", object_fit="contain")

                    res.change(lambda r: gr.update(visible=(r == 0)), res, custom_res)
                    style.change(lambda st: (gr.update(value=get_style(st).steps),
                                             gr.update(value=get_style(st).cfg),
                                             gr.update(value=get_style(st).aspect)) if st != "Ninguno"
                                 else (gr.update(), gr.update(), gr.update()), style, [steps, cfg, aspect])

                    def on_model(mid):
                        try:
                            sp = ctx.models.spec(mid)
                        except KeyError:
                            return gr.update(), gr.update(), gr.update()
                        return (gr.update(value=sp.default_steps), gr.update(value=sp.default_cfg),
                                gr.update(value=sp.default_resolution if sp.default_resolution in RESOLUTIONS
                                          else 512))
                    model.change(on_model, model, [steps, cfg, res])
                    enh_btn.click(enhance_prompt, prompt, prompt)
                    return dict(prompt=prompt, negative=negative, style=style, model=model, res=res,
                                custom_res=custom_res, aspect=aspect, n=n, seed=seed, steps=steps, cfg=cfg,
                                auto=auto_enh, gen=gen_btn, cancel=cancel_btn, status=status, preview=preview)

                with gr.Column(visible=True) as pages["Inicio"]:
                    home = generator_panel(full=False)
                    gr.Markdown("### Creaciones recientes")
                    recent = gr.Gallery(value=recent_gallery(), columns=4, height=320, format="png",
                                        label="Recientes", object_fit="cover")

                with gr.Column(visible=False) as pages["Crear imagen"]:
                    gr.Markdown("## ✨ Crear imagen")
                    create = generator_panel(full=True)

                for panel in (home, create):
                    def _res(r, c):
                        return int(c) if int(r) == 0 else int(r)
                    inputs = [panel[k] for k in ("prompt", "negative", "model", "style")]

                    def _gen(prompt, negative, model_id, style, r, c, aspect, n, seed, steps, cfg, auto):
                        yield from generate(prompt, negative, model_id, style, _res(r, c), aspect, n, seed,
                                            steps, cfg, auto)
                    panel["gen"].click(_gen, inputs + [panel[k] for k in ("res", "custom_res", "aspect", "n",
                                                                           "seed", "steps", "cfg", "auto")],
                                       [panel["status"], panel["preview"], recent])
                    panel["cancel"].click(lambda: progress_html(0, 1, ctx.cancel_current()), None, panel["status"])

                # ---------------------------------------------- Estilos
                with gr.Column(visible=False) as pages["Explorar estilos"]:
                    gr.Markdown("## 🎨 Explorar estilos\nElige una categoría, revisa sus ajustes y usa un ejemplo.")
                    cards = "".join(
                        f"<div class='mars-style-card'><b>{st.icon} {st.name}</b><br>"
                        f"<span class='mars-muted'>Steps {st.steps} · CFG {st.cfg} · {st.aspect}</span><br>"
                        f"<small>{st.examples[0]}</small></div>" for st in STYLES)
                    gr.HTML(f"<div style='display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));"
                            f"gap:10px'>{cards}</div>")
                    with gr.Row():
                        ex_style = gr.Dropdown([st.name for st in STYLES], value=STYLES[0].name, label="Estilo")
                        ex_prompt = gr.Radio(list(STYLES[0].examples), label="Prompts de ejemplo",
                                             value=STYLES[0].examples[0])
                    ex_info = gr.Markdown()
                    use_btn = gr.Button("➡️ Usar en «Crear imagen»", variant="primary")

                    def style_info(name):
                        st = get_style(name)
                        info = (f"**Palabras clave añadidas:** `{st.positive}`\n\n**Negativo:** `{st.negative or '—'}`"
                                f"\n\n**Ajustes:** {st.steps} steps · CFG {st.cfg} · aspecto {st.aspect}")
                        return gr.update(choices=list(st.examples), value=st.examples[0]), info
                    ex_style.change(style_info, ex_style, [ex_prompt, ex_info])
                    demo.load(style_info, ex_style, [ex_prompt, ex_info])

                # ---------------------------------------------- Galería
                def gallery_page(title: str, favorites: bool):
                    gr.Markdown(f"## {title}")
                    with gr.Row():
                        q = gr.Textbox(label="Buscar (prompt, modelo o estilo)", scale=3)
                        d_from = gr.Textbox(label="Desde (AAAA-MM-DD)", scale=1)
                        d_to = gr.Textbox(label="Hasta (AAAA-MM-DD)", scale=1)
                        search_btn = gr.Button("🔍 Buscar", scale=1)
                    gal = gr.Gallery(columns=4, height=480, format="png", label="Biblioteca",
                                     object_fit="cover", allow_preview=True)
                    ids = gr.State([])
                    sel_id = gr.State(None)
                    details = gr.Markdown("Selecciona una imagen para ver sus datos.")
                    with gr.Row():
                        fav_btn = gr.Button("⭐ Favorito / quitar")
                        dl_btn = gr.DownloadButton("⬇️ Descargar", value=None)
                        del_btn = gr.Button("🗑️ Eliminar", variant="stop")
                        del_ok = gr.Checkbox(False, label="Confirmo que quiero eliminarla")

                    def refresh(text, dfrom, dto):
                        recs = ctx.library.search(text or "", favorites, dfrom or "", dto or "")
                        return [(r.file_path, r.caption()) for r in recs], [r.id for r in recs], \
                            f"{len(recs)} imagen(es)."

                    def select(ids_list, evt: gr.SelectData):
                        if evt.index is None or evt.index >= len(ids_list):
                            return None, "—", gr.update(value=None)
                        r = ctx.library.get(ids_list[evt.index])
                        md = (f"**#{r.id}** · {r.created_at} · {'⭐ Favorito' if r.favorite else ''}\n\n"
                              f"**Prompt:** {r.prompt}\n\n**Negativo:** {r.negative or '—'}\n\n"
                              f"**Modelo:** {r.model} · **Estilo:** {r.style or '—'} · **Tipo:** {r.kind}\n\n"
                              f"**Tamaño:** {r.width}×{r.height} · **Steps:** {r.steps} · **CFG:** {r.cfg} · "
                              f"**Seed:** {r.seed} · **Tiempo:** {r.seconds} s\n\n`{r.file_path}`")
                        return r.id, md, gr.update(value=r.file_path)

                    def fav(i, text, dfrom, dto):
                        if i is not None:
                            ctx.library.toggle_favorite(i)
                        return refresh(text, dfrom, dto)

                    def delete(i, ok, text, dfrom, dto):
                        if i is None:
                            g, l, _ = refresh(text, dfrom, dto)
                            return g, l, "Selecciona una imagen.", None, False
                        if not ok:
                            g, l, _ = refresh(text, dfrom, dto)
                            return g, l, "⚠️ Marca la casilla de confirmación para eliminar.", i, False
                        ctx.library.delete(i)
                        g, l, msg = refresh(text, dfrom, dto)
                        return g, l, f"🗑️ Eliminada. {msg}", None, False

                    flt = [q, d_from, d_to]
                    search_btn.click(refresh, flt, [gal, ids, details])
                    q.submit(refresh, flt, [gal, ids, details])
                    gal.select(select, ids, [sel_id, details, dl_btn])
                    fav_btn.click(fav, [sel_id] + flt, [gal, ids, details])
                    del_btn.click(delete, [sel_id, del_ok] + flt, [gal, ids, details, sel_id, del_ok])
                    return refresh, flt, [gal, ids, details]

                with gr.Column(visible=False) as pages["Mis creaciones"]:
                    lib_refresh = gallery_page("🖼️ Mis creaciones", favorites=False)
                with gr.Column(visible=False) as pages["Favoritos"]:
                    fav_refresh = gallery_page("⭐ Favoritos", favorites=True)

                # ---------------------------------------------- Herramientas
                with gr.Column(visible=False) as pages["Herramientas"]:
                    gr.Markdown("## 🛠️ Herramientas\nLas herramientas **clásicas** funcionan siempre. Las de "
                                "**IA** necesitan un modelo local instalado (ver «Modelos IA»).")
                    local_choices = [c for c in model_choices() if c[1] != "hf-api"]
                    with gr.Tabs():
                        with gr.Tab("Upscaler clásico"):
                            gr.Markdown("Ampliación **clásica** (Lanczos + enfoque). No añade detalle inventado.")
                            up_in = gr.Image(type="pil", label="Imagen")
                            up_f = gr.Radio([2, 3, 4], value=2, label="Factor")
                            up_btn = gr.Button("Ampliar", variant="primary")
                            up_out, up_msg = gr.Image(label="Resultado", format="png"), gr.Markdown()
                            up_btn.click(lambda im, f: classic_tool(T.upscale_classic, im, int(f), kind="upscale"),
                                         [up_in, up_f], [up_out, up_msg])
                        with gr.Tab("Upscaler IA"):
                            gr.Markdown(f"**Real-ESRGAN x4plus** — reconstruye detalle al ampliar. "
                                        f"Licencia {RE.LICENSE}. Descarga única de ~{RE.MODEL_MB} MB desde el "
                                        "repositorio oficial en GitHub, verificada con SHA-256. "
                                        "En CPU puede tardar de segundos a varios minutos según el tamaño; con GPU es casi inmediato.")
                            ai_stat = gr.Markdown(lambda: f"Estado: {ctx.upscaler.status()}")
                            with gr.Row():
                                ai_auth = gr.Checkbox(False, label=f"Autorizo descargar Real-ESRGAN (~{RE.MODEL_MB} MB)")
                                ai_dl = gr.Button("⬇️ Descargar modelo")
                            ai_in = gr.Image(type="pil", label="Imagen")
                            ai_f = gr.Radio([2, 3, 4], value=4, label="Factor")
                            with gr.Row():
                                ai_btn = gr.Button("Ampliar con IA", variant="primary")
                                ai_cancel = gr.Button("⛔ Cancelar")
                            ai_prog = gr.HTML()
                            ai_out = gr.Image(label="Resultado", format="png")

                            def ai_upscale(im, f):
                                if im is None:
                                    yield progress_html(0, 1, "❌ Sube una imagen primero."), None
                                    return
                                if not ctx.upscaler.installed():
                                    yield progress_html(0, 1, "❌ Descarga primero el modelo (arriba)."), None
                                    return
                                state = {"step": 0, "total": 1, "res": None, "err": None}
                                ctx.upscale_cancel = threading.Event()
                                t0 = time.perf_counter()

                                def work():
                                    try:
                                        state["res"] = ctx.upscaler.upscale(
                                            load_user_image(im), int(f),
                                            progress=lambda a, b: state.update(step=a, total=b),
                                            cancel=ctx.upscale_cancel)
                                    except Exception as exc:  # noqa: BLE001
                                        state["err"] = str(exc)
                                th = threading.Thread(target=work, daemon=True)
                                th.start()
                                while th.is_alive():
                                    yield progress_html(state["step"], state["total"],
                                                        f"⏳ Ampliando: bloque {state['step']}/{state['total']} · "
                                                        f"{time.perf_counter() - t0:.1f} s"), None
                                    time.sleep(0.5)
                                if state["err"]:
                                    yield progress_html(0, 1, f"❌ {state['err']}"), None
                                    return
                                out = state["res"]
                                secs = round(time.perf_counter() - t0, 1)
                                rec = ctx.library.save(out, prompt="[upscale IA x%s]" % f, model="Real-ESRGAN x4plus",
                                                       kind="upscale_ai", seconds=secs)
                                yield progress_html(1, 1, f"✅ {out.width}×{out.height} en {secs} s · guardado #{rec.id}"), out

                            ai_dl.click(lambda ok: ctx.upscaler.download(ok), ai_auth, ai_stat) \
                                .then(lambda: False, None, ai_auth)
                            ai_btn.click(ai_upscale, [ai_in, ai_f], [ai_prog, ai_out])
                            ai_cancel.click(lambda: (ctx.upscale_cancel.set(), progress_html(0, 1, "⛔ Cancelando…"))[1],
                                            None, ai_prog)
                        with gr.Tab("Enhancer"):
                            en_in = gr.Image(type="pil", label="Imagen")
                            with gr.Row():
                                en_sh = gr.Slider(0.5, 3, 1.5, step=0.1, label="Nitidez")
                                en_co = gr.Slider(0.5, 2, 1.1, step=0.05, label="Contraste")
                                en_cl = gr.Slider(0, 2, 1.1, step=0.05, label="Color")
                            en_btn = gr.Button("Mejorar", variant="primary")
                            en_out, en_msg = gr.Image(label="Resultado", format="png"), gr.Markdown()
                            en_btn.click(lambda im, a, b, c: classic_tool(T.enhance, im, a, b, c, kind="enhance"),
                                         [en_in, en_sh, en_co, en_cl], [en_out, en_msg])
                        with gr.Tab("Restauración"):
                            gr.Markdown("Restauración **clásica**: reduce ruido y rayas finas, corrige contraste "
                                        "y dominantes de color.")
                            rs_in = gr.Image(type="pil", label="Foto antigua")
                            rs_dn = gr.Slider(0, 7, 3, step=1, label="Reducción de ruido")
                            rs_btn = gr.Button("Restaurar", variant="primary")
                            rs_out, rs_msg = gr.Image(label="Resultado", format="png"), gr.Markdown()
                            rs_btn.click(lambda im, d: classic_tool(T.restore, im, int(d), kind="restore"),
                                         [rs_in, rs_dn], [rs_out, rs_msg])
                        with gr.Tab("Caras IA"):
                            gr.Markdown(f"**GFPGAN v1.4** — restaura caras borrosas, antiguas o de baja calidad. "
                                        f"Licencias: {FR.LICENSE}. Descarga única de ~{FR.TOTAL_MB} MB desde los "
                                        "repositorios oficiales en GitHub, verificada con SHA-256. "
                                        "Solo mejora las caras; combínalo con «Restauración» para el resto de la foto.")
                            fc_stat = gr.Markdown(lambda: f"Estado: {ctx.faces.status()}")
                            with gr.Row():
                                fc_auth = gr.Checkbox(False, label=f"Autorizo descargar GFPGAN (~{FR.TOTAL_MB} MB)")
                                fc_dl = gr.Button("⬇️ Descargar modelo")
                            fc_in = gr.Image(type="pil", label="Foto con caras")
                            with gr.Row():
                                fc_w = gr.Slider(0, 1, 0.6, step=0.05, label="Intensidad (más baja = más fiel al original)")
                                fc_up = gr.Radio([("×1", 1), ("×2", 2)], value=1,
                                                 label="Ampliar foto (×2 usa Real-ESRGAN si está instalado)")
                            with gr.Row():
                                fc_btn = gr.Button("Restaurar caras", variant="primary")
                                fc_cancel = gr.Button("⛔ Cancelar")
                            fc_prog = gr.HTML()
                            fc_out = gr.Image(label="Resultado", format="png")

                            def face_restore(im, wgt, up):
                                if im is None:
                                    yield progress_html(0, 1, "❌ Sube una imagen primero."), None
                                    return
                                if not ctx.faces.installed():
                                    yield progress_html(0, 1, "❌ Descarga primero el modelo (arriba)."), None
                                    return
                                state = {"step": 0, "total": 1, "res": None, "err": None}
                                ctx.faces_cancel = threading.Event()
                                t0 = time.perf_counter()

                                def work():
                                    try:
                                        state["res"] = ctx.faces.restore(
                                            load_user_image(im), float(wgt), int(up), upscaler=ctx.upscaler,
                                            progress=lambda a, b: state.update(step=a, total=b),
                                            cancel=ctx.faces_cancel)
                                    except Exception as exc:  # noqa: BLE001
                                        state["err"] = str(exc)
                                th = threading.Thread(target=work, daemon=True)
                                th.start()
                                while th.is_alive():
                                    yield progress_html(state["step"], state["total"],
                                                        f"⏳ Restaurando caras: {state['step']}/{state['total']} · "
                                                        f"{time.perf_counter() - t0:.1f} s"), None
                                    time.sleep(0.5)
                                if state["err"]:
                                    yield progress_html(0, 1, f"❌ {state['err']}"), None
                                    return
                                out, n = state["res"]
                                secs = round(time.perf_counter() - t0, 1)
                                if n == 0:
                                    yield progress_html(0, 1, f"⚠️ No se detectó ninguna cara ({secs} s)."), None
                                    return
                                rec = ctx.library.save(out, prompt=f"[caras IA, intensidad {wgt}]",
                                                       model="GFPGAN v1.4", kind="faces_ai", seconds=secs)
                                yield progress_html(1, 1, f"✅ {n} cara(s) restaurada(s) en {secs} s · "
                                                          f"{out.width}×{out.height} · guardado #{rec.id}"), out

                            fc_dl.click(lambda ok: ctx.faces.download(ok), fc_auth, fc_stat) \
                                .then(lambda: False, None, fc_auth)
                            fc_btn.click(face_restore, [fc_in, fc_w, fc_up], [fc_prog, fc_out])
                            fc_cancel.click(lambda: (ctx.faces_cancel.set(), progress_html(0, 1, "⛔ Cancelando…"))[1],
                                            None, fc_prog)
                        with gr.Tab("Quitar fondo"):
                            gr.Markdown("Estado: " + ("🟢 disponible (rembg)" if T.rembg_available() else
                                                      "🔴 no instalado — ejecuta `install_optional_tools.bat`"))
                            bg_in = gr.Image(type="pil", label="Imagen")
                            bg_btn = gr.Button("Quitar fondo", variant="primary")
                            bg_out, bg_msg = gr.Image(label="Resultado (PNG transparente)", format="png"), \
                                gr.Markdown()
                            bg_btn.click(lambda im: classic_tool(T.remove_background, im, kind="nobg"),
                                         bg_in, [bg_out, bg_msg])
                        with gr.Tab("Mejorar prompt"):
                            pe_in = gr.Textbox(label="Tu descripción", lines=3)
                            pe_tr = gr.Checkbox(True, label="Traducir términos frecuentes al inglés")
                            pe_btn = gr.Button("Mejorar", variant="primary")
                            pe_out = gr.Textbox(label="Prompt mejorado", lines=3)
                            pe_btn.click(enhance_prompt, [pe_in, pe_tr], pe_out)

                        def ai_common():
                            with gr.Row():
                                mdl = gr.Dropdown(local_choices, value=local_choices[0][1] if local_choices else None,
                                                  label="Modelo local")
                                stp = gr.Slider(1, 60, 25, step=1, label="Steps")
                                cf = gr.Slider(0, 15, 7, step=0.5, label="CFG")
                                sd = gr.Number(-1, precision=0, label="Seed")
                            return mdl, stp, cf, sd

                        with gr.Tab("Image to Image"):
                            i2_in = gr.Image(type="pil", label="Imagen de referencia")
                            i2_p = gr.Textbox(label="Prompt"); i2_n = gr.Textbox(label="Negativo")
                            i2_s = gr.Slider(0.1, 1.0, 0.6, step=0.05, label="Fuerza (más = más cambios)")
                            i2_m, i2_st, i2_c, i2_sd = ai_common()
                            i2_btn = gr.Button("Generar", variant="primary")
                            i2_stat, i2_out = gr.HTML(), gr.Gallery(columns=3, format="png")
                            i2_btn.click(lambda *a: (yield from ai_tool("img2img", *a)),
                                         [i2_in, i2_p, i2_n, i2_m, i2_s, i2_st, i2_c, i2_sd], [i2_stat, i2_out])
                        with gr.Tab("Variaciones"):
                            va_in = gr.Image(type="pil", label="Imagen")
                            va_p = gr.Textbox(label="Descripción de la imagen (ayuda a mantenerla)")
                            va_s = gr.Slider(0.2, 0.9, 0.5, step=0.05, label="Intensidad de variación")
                            va_m, va_st, va_c, va_sd = ai_common()
                            va_btn = gr.Button("Crear 3 variaciones", variant="primary")
                            va_stat, va_out = gr.HTML(), gr.Gallery(columns=3, format="png")
                            va_btn.click(lambda im, p, *a: (yield from ai_tool("variations", im, p, "", *a)),
                                         [va_in, va_p, va_m, va_s, va_st, va_c, va_sd], [va_stat, va_out])
                        with gr.Tab("Inpainting"):
                            gr.Markdown("Sube la imagen y **pinta con el pincel** la zona que quieres cambiar.")
                            ip_in = gr.ImageEditor(type="pil", label="Imagen + máscara",
                                                   brush=gr.Brush(colors=["#ffffff"], color_mode="fixed"))
                            ip_p = gr.Textbox(label="¿Qué debe aparecer en la zona pintada?")
                            ip_n = gr.Textbox(label="Negativo")
                            ip_s = gr.Slider(0.3, 1.0, 0.85, step=0.05, label="Fuerza")
                            ip_m, ip_st, ip_c, ip_sd = ai_common()
                            ip_btn = gr.Button("Aplicar", variant="primary")
                            ip_stat, ip_out = gr.HTML(), gr.Gallery(columns=2, format="png")
                            ip_btn.click(lambda *a: (yield from ai_tool("inpaint", *a)),
                                         [ip_in, ip_p, ip_n, ip_m, ip_s, ip_st, ip_c, ip_sd], [ip_stat, ip_out])
                        with gr.Tab("Outpainting"):
                            op_in = gr.Image(type="pil", label="Imagen")
                            with gr.Row():
                                op_l = gr.Slider(0, 512, 128, step=8, label="Izquierda")
                                op_r = gr.Slider(0, 512, 128, step=8, label="Derecha")
                                op_t = gr.Slider(0, 512, 0, step=8, label="Arriba")
                                op_b = gr.Slider(0, 512, 0, step=8, label="Abajo")
                            op_p = gr.Textbox(label="Descripción de la escena completa")
                            op_m, op_st, op_c, op_sd = ai_common()
                            op_btn = gr.Button("Ampliar", variant="primary")
                            op_stat, op_out = gr.HTML(), gr.Gallery(columns=2, format="png")

                            def _op(im, p, m, st, c, sd, l, r, t, b):
                                yield from ai_tool("outpaint", im, p, "", m, 1.0, st, c, sd,
                                                   extra=(int(l), int(r), int(t), int(b)))
                            op_btn.click(_op, [op_in, op_p, op_m, op_st, op_c, op_sd, op_l, op_r, op_t, op_b],
                                         [op_stat, op_out])

                # ---------------------------------------------- Modelos
                with gr.Column(visible=False) as pages["Modelos IA"]:
                    gr.Markdown("## 🧠 Modelos IA\nNada se descarga sin tu autorización explícita. "
                                "Los modelos se guardan en la carpeta de modelos configurada.")
                    mtable = gr.Dataframe(headers=["Modelo", "Estado", "Conexión", "Compatibilidad",
                                                   "Descarga", "VRAM mín.", "RAM mín.", "Licencia"],
                                          interactive=False, wrap=True)
                    with gr.Row():
                        msel = gr.Dropdown([(sp.name, sp.id) for sp in ctx.models.all_specs()],
                                           value=s.default_model, label="Modelo")
                        mrefresh = gr.Button("🔄 Actualizar")
                    minfo = gr.Markdown()
                    mauth = gr.Checkbox(False, label="Autorizo descargar este modelo (he revisado tamaño y licencia)")
                    with gr.Row():
                        mdl_btn = gr.Button("⬇️ Descargar / instalar", variant="primary")
                        mdef_btn = gr.Button("✅ Usar por defecto")
                        mdel_btn = gr.Button("🗑️ Eliminar del disco", variant="stop")
                    mmsg = gr.Markdown()
                    with gr.Accordion("Añadir modelo local (.safetensors)", open=False):
                        cpath = gr.Textbox(label="Ruta del archivo", placeholder=r"C:\Modelos\mi_modelo.safetensors")
                        cname = gr.Textbox(label="Nombre")
                        cbase = gr.Radio([("SD 1.5", "sd15"), ("SDXL", "sdxl")], value="sd15", label="Arquitectura")
                        cadd = gr.Button("Añadir")

                    def table():
                        rows = []
                        for st in ctx.models.statuses():
                            sp = st.spec
                            rows.append([sp.name, st.state, sp.connection,
                                         st.compatibility, f"{sp.download_gb} GB" if sp.download_gb else "—",
                                         f"{sp.min_vram_gb} GB" if sp.min_vram_gb else "—",
                                         f"{sp.min_ram_gb} GB", sp.license])
                        return rows

                    def info(mid):
                        try:
                            sp = ctx.models.spec(mid)
                        except KeyError:
                            return ""
                        st = ctx.models.status(sp)
                        lic = f"[{sp.license}]({sp.license_url})" if sp.license_url else sp.license
                        return (f"### {sp.name}\n**Estado:** {st.state} · **Compatibilidad con tu equipo:** "
                                f"{st.compatibility}\n\n**Repositorio:** `{sp.repo_id}` · **Licencia:** {lic}\n\n"
                                f"**Espacio necesario:** {sp.download_gb or '—'} GB · **VRAM mínima:** "
                                f"{sp.min_vram_gb or '—'} GB · **RAM mínima:** {sp.min_ram_gb} GB\n\n{sp.notes}")

                    def all_model_updates():
                        ch = model_choices()
                        return [gr.update(choices=ch), gr.update(choices=ch)]

                    def do_download(mid, ok, progress=gr.Progress()):
                        progress(0, desc="Descargando… (puede tardar mucho, no cierres la ventana)")
                        msg = ctx.models.download(mid, ok)
                        return [msg, table(), info(mid), False] + all_model_updates()

                    def do_default(mid):
                        ctx.store.update(default_model=mid)
                        return [f"Modelo por defecto: **{ctx.models.spec(mid).name}**", table(), info(mid), False] \
                            + [gr.update(choices=model_choices(), value=mid)] * 2

                    def do_delete(mid, ok):
                        if not ok:
                            return ["⚠️ Marca la casilla para confirmar.", table(), info(mid), False] + \
                                all_model_updates()
                        return [ctx.models.delete(mid), table(), info(mid), False] + all_model_updates()

                    def do_add(path, name, base):
                        msg = ctx.models.add_custom(path, name, base)
                        return [msg, table(), gr.update(choices=[(sp.name, sp.id) for sp in ctx.models.all_specs()])] \
                            + all_model_updates()

                    gen_models = [home["model"], create["model"]]
                    mout = [mmsg, mtable, minfo, mauth] + gen_models
                    msel.change(info, msel, minfo)
                    mrefresh.click(lambda m: (table(), info(m)), msel, [mtable, minfo])
                    mdl_btn.click(do_download, [msel, mauth], mout)
                    mdef_btn.click(do_default, msel, mout)
                    mdel_btn.click(do_delete, [msel, mauth], mout)
                    cadd.click(do_add, [cpath, cname, cbase], [mmsg, mtable, msel] + gen_models)

                # ---------------------------------------------- Configuración
                with gr.Column(visible=False) as pages["Configuración"]:
                    gr.Markdown("## ⚙️ Configuración")
                    with gr.Tab("General"):
                        c_lang = gr.Dropdown([("Español", "es")], value="es", label="Idioma",
                                             info="Por ahora solo está disponible el español.")
                        c_theme = gr.Dropdown([("Oscuro (MARS)", "oscuro")], value="oscuro", label="Tema")
                        c_out = gr.Textbox(str(s.output_path), label="Carpeta de imágenes")
                        c_mod = gr.Textbox(str(s.models_path), label="Carpeta de modelos")
                    with gr.Tab("Generación"):
                        c_style = gr.Dropdown(style_names(), value=s.default_style, label="Estilo por defecto")
                        c_steps = gr.Slider(1, 80, s.default_steps, step=1, label="Steps por defecto")
                        c_cfg = gr.Slider(0, 20, s.default_cfg, step=0.5, label="CFG por defecto")
                        c_res = gr.Dropdown(RESOLUTIONS, value=s.default_resolution, label="Resolución por defecto")
                        c_asp = gr.Dropdown(list(ASPECTS), value=s.default_aspect, label="Aspecto por defecto")
                    with gr.Tab("Memoria"):
                        c_low = gr.Checkbox(s.low_power_mode, label="Modo bajo consumo (descarga partes del "
                                            "modelo a la CPU; menos VRAM, algo más lento)")
                        c_unl = gr.Checkbox(s.unload_after_generation, label="Liberar el modelo de memoria tras "
                                            "cada generación (mínima RAM, más lento)")
                        c_batch = gr.Slider(1, 8, s.max_batch, step=1, label="Máximo de imágenes por lote")
                    with gr.Tab("APIs y conexiones"):
                        gr.Markdown(
                            "**API de Hugging Face (opcional).** Crea un token gratuito en "
                            "huggingface.co → Settings → Access Tokens. Las cuentas gratuitas incluyen un "
                            "crédito mensual limitado; **las condiciones pueden cambiar y el uso extra puede "
                            "tener coste**. Revisa https://huggingface.co/docs/inference-providers/pricing. "
                            "MARS.AI nunca contrata nada por ti.\n\n"
                            "El token se guarda en el **Administrador de credenciales de Windows** (keyring) y "
                            "nunca se escribe en registros ni en archivos de configuración.")
                        tok_state = gr.Markdown(lambda: f"Token actual: `{ctx.secrets.mask(ctx.secrets.get('huggingface'))}`"
                                                f" · Almacén seguro: {'✅' if ctx.secrets.secure_backend_available else '❌'}")
                        c_tok = gr.Textbox(type="password", label="Nuevo token de Hugging Face (vacío = no cambiar)")
                        c_tok_del = gr.Checkbox(False, label="Borrar el token guardado")
                        c_hfm = gr.Textbox(s.hf_api_model, label="Modelo para la API",
                                           info="Ej.: black-forest-labs/FLUX.1-schnell, "
                                                "stabilityai/stable-diffusion-xl-base-1.0")
                        c_cost = gr.Checkbox(s.accepted_api_cost_warning,
                                             label="Entiendo que la API externa puede tener límites o costes")
                    with gr.Tab("Sistema"):
                        sysmd = gr.Code(format_report(ctx.system), language=None, label="Diagnóstico del equipo")
                    c_save = gr.Button("💾 Guardar configuración", variant="primary")
                    c_msg = gr.Markdown()

                    def save_cfg(out, mod, style, steps, cfg, res, asp, low, unl, batch, tok, tok_del, hfm, cost):
                        for label, pth in (("imágenes", out), ("modelos", mod)):
                            try:
                                Path(pth).mkdir(parents=True, exist_ok=True)
                            except OSError as exc:
                                return f"❌ Carpeta de {label} no válida: {exc}", gr.update()
                        ctx.store.update(output_dir=out, models_dir=mod, default_style=style,
                                         default_steps=int(steps), default_cfg=float(cfg), default_resolution=int(res),
                                         default_aspect=asp, low_power_mode=bool(low),
                                         unload_after_generation=bool(unl), max_batch=int(batch),
                                         hf_api_model=hfm.strip() or "black-forest-labs/FLUX.1-schnell",
                                         accepted_api_cost_warning=bool(cost))
                        ctx.library.set_output_dir(Path(out))
                        msg = "✅ Configuración guardada."
                        if tok_del:
                            ctx.secrets.delete("huggingface")
                            msg += " Token borrado."
                        elif tok:
                            if not cost:
                                msg += " ⚠️ Token NO guardado: acepta primero el aviso de costes."
                            elif ctx.secrets.set("huggingface", tok.strip()):
                                msg += " Token guardado de forma segura."
                            else:
                                msg += " ❌ No se pudo guardar el token (almacén seguro no disponible)."
                        ctx.models.unload()  # aplica cambios de memoria / API
                        return msg, f"Token actual: `{ctx.secrets.mask(ctx.secrets.get('huggingface'))}`"
                    c_save.click(save_cfg, [c_out, c_mod, c_style, c_steps, c_cfg, c_res, c_asp, c_low, c_unl,
                                            c_batch, c_tok, c_tok_del, c_hfm, c_cost], [c_msg, tok_state]) \
                        .then(lambda: "", None, c_tok)

        # ================================================== navegación
        page_cols = [pages[p] for p in PAGES]

        def show(name):
            return [gr.update(visible=(p == name)) for p in PAGES]

        for btn, name in zip(nav_buttons, PAGES):
            ev = btn.click(lambda n=name: show(n), None, page_cols)
            if name == "Mis creaciones":
                ev.then(lib_refresh[0], lib_refresh[1], lib_refresh[2])
            elif name == "Favoritos":
                ev.then(fav_refresh[0], fav_refresh[1], fav_refresh[2])
            elif name == "Modelos IA":
                ev.then(lambda m: (table(), info(m)), msel, [mtable, minfo])
            elif name == "Inicio":
                ev.then(recent_gallery, None, recent)

        use_btn.click(lambda st, ex: [*show("Crear imagen"), ex, st], [ex_style, ex_prompt],
                      page_cols + [create["prompt"], create["style"]])
        mem_btn.click(ctx.free_memory, None, mem_msg)
        demo.load(lambda m: (table(), info(m)), msel, [mtable, minfo])
    return demo


def launch(ctx: AppContext, port: int = 7860, inbrowser: bool = True, share: bool = False):
    demo = build_ui(ctx)
    demo.queue(default_concurrency_limit=1)  # una generación cada vez: protege la RAM
    demo.launch(server_name="127.0.0.1", server_port=port, inbrowser=inbrowser, share=share,
                allowed_paths=[str(ctx.settings.output_path)], theme=demo.mars_theme,
                css=demo.mars_css, js=demo.mars_js, show_error=True)
