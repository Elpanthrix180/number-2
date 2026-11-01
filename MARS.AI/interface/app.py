"""Interfaz gráfica de MARS.AI (Gradio, se abre en el navegador como app local)."""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

import gradio as gr

from config.settings import APP_NAME, SLOGAN
from core.app_context import AppContext
from core.i18n import LANGUAGES, N_, get_language, t
from core.system_info import format_report
from gallery.library import load_user_image
from generator.engine import ASPECTS, RESOLUTIONS, GenerationJob, build_request
from generator.prompt_enhancer import enhance_prompt
from generator.styles import STYLES, get_style, style_names
from models.backends import BackendUnavailable, GenRequest
from tools import image_tools as T
from tools import background_remover as BG
from tools import face_restore as FR
from tools import realesrgan as RE

log = logging.getLogger(__name__)
CSS_FILE = Path(__file__).with_name("theme.css")
# Claves internas de las páginas (se muestran traducidas con t()).
PAGES = [N_("Inicio"), N_("Crear imagen"), N_("Explorar estilos"), N_("Mis creaciones"), N_("Favoritos"),
         N_("Herramientas"), N_("Modelos IA"), N_("Configuración")]
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


def style_choices() -> list[tuple[str, str]]:
    return [(t(n), n) for n in style_names()]


def build_ui(ctx: AppContext) -> gr.Blocks:
    s = ctx.settings
    translate_default = get_language() == "es"

    # =========================================================== helpers
    def model_choices():
        return ctx.models.available_choices()

    def run_job(backend, req: GenRequest, label: str):
        """Generador común: ejecuta un trabajo y emite (html_progreso, imágenes|None, job)."""
        job = GenerationJob(backend, req).start()
        ctx.current_job = job
        while not job.done:
            yield progress_html(job.step, job.total,
                                t("⏳ {label}: paso {step}/{total} · {secs} s", label=label, step=job.step,
                                  total=job.total, secs=f"{job.elapsed:.1f}")), None, job
            time.sleep(0.4)
        res = job.result
        if ctx.settings.unload_after_generation:
            ctx.models.unload()
        if res.cancelled:
            yield progress_html(0, 1, t("⛔ Cancelado tras {secs} s", secs=f"{res.seconds:.1f}")), None, job
        elif res.error:
            yield progress_html(0, 1, f"❌ {res.error}"), None, job
        else:
            yield progress_html(1, 1, t("✅ {label}: terminado en {secs} s · seed {seed}", label=label,
                                        secs=f"{res.seconds:.1f}", seed=res.seed)), res.images, job

    def generate(prompt, negative, model_id, style, res, aspect, n, seed, steps, cfg, auto_enhance):
        try:
            spec = ctx.models.spec(model_id)
            p = enhance_prompt(prompt, translate=translate_default) if auto_enhance else prompt
            req = build_request(p, negative, style, int(res), aspect, int(n), int(seed), int(steps), float(cfg),
                                max_side=spec.max_resolution, max_batch=ctx.settings.max_batch)
            backend = ctx.models.backend(model_id)
        except (ValueError, BackendUnavailable, KeyError) as exc:
            yield progress_html(0, 1, f"❌ {exc}"), gr.update(), gr.update()
            return
        yield progress_html(0, req.steps, t("Preparando {name} ({w}×{h})… la primera vez puede tardar en "
                                            "cargar el modelo.", name=t(spec.name), w=req.width, h=req.height)), \
            gr.update(), gr.update()
        for html, images, job in run_job(backend, req, t("Generación")):
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
                raise BackendUnavailable(t("Esta herramienta necesita un modelo local instalado (no la API)."))
            backend = ctx.models.backend(model_id)
            mode = "img2img" if kind in ("img2img", "variations") else "inpaint"
            if not backend.supports(mode):
                raise BackendUnavailable(t("{name} no admite {mode}.", name=t(spec.name), mode=mode))
            mask = None
            if kind == "inpaint":
                image, mask = T.mask_from_editor(image)
            elif image is None:
                raise ValueError(t("Sube una imagen de referencia."))
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
            return None, t("❌ Sube una imagen primero.")
        try:
            t0 = time.perf_counter()
            out = fn(load_user_image(image), *args)
            model = N_("Quitafondos IA") if kind == "nobg" else N_("Herramienta clásica")
            rec = ctx.library.save(out, prompt=f"[{kind}]", model=model, kind=kind,
                                   seconds=round(time.perf_counter() - t0, 2))
            return out, t("✅ Listo en {secs} s · {w}×{h} · guardado como #{id}", secs=rec.seconds,
                          w=out.width, h=out.height, id=rec.id)
        except Exception as exc:  # noqa: BLE001
            return None, f"❌ {exc}"

    def threaded_tool(work_fn, label: str, cancel_attr: str):
        """Ejecuta work_fn(progress, cancel) en un hilo y emite el progreso. Devuelve el resultado al final."""
        state = {"step": 0, "total": 1, "res": None, "err": None}
        cancel = threading.Event()
        setattr(ctx, cancel_attr, cancel)
        t0 = time.perf_counter()

        def work():
            try:
                state["res"] = work_fn(lambda a, b: state.update(step=a, total=b), cancel)
            except Exception as exc:  # noqa: BLE001
                state["err"] = str(exc)
        th = threading.Thread(target=work, daemon=True)
        th.start()
        while th.is_alive():
            yield progress_html(state["step"], state["total"],
                                f"⏳ {label}: {state['step']}/{state['total']} · "
                                f"{time.perf_counter() - t0:.1f} s"), None, None
            time.sleep(0.5)
        yield None, state, round(time.perf_counter() - t0, 1)

    # ============================================================== UI
    theme = gr.themes.Base(primary_hue="violet", secondary_hue="blue", neutral_hue="slate",
                           font=[gr.themes.GoogleFont("Inter"), "Segoe UI", "sans-serif"])
    with gr.Blocks(title=f"{APP_NAME} — {t(SLOGAN)}") as demo:
        demo.mars_theme, demo.mars_css, demo.mars_js = theme, CSS_FILE.read_text(encoding="utf-8"), FORCE_DARK_JS
        gr.HTML(f"<div id='mars-header'><h1>{APP_NAME}</h1><p>{t(SLOGAN)}</p></div>")
        with gr.Row():
            with gr.Column(scale=0, min_width=200, elem_id="mars-sidebar"):
                nav_buttons = [gr.Button(f"{i}  {t(p)}", size="sm") for i, p in zip(ICONS, PAGES)]
                gr.HTML("<hr style='border-color:#262640'>")
                mem_btn = gr.Button(t("🧹 Liberar memoria"), size="sm")
                mem_msg = gr.Markdown(elem_classes="mars-muted")
            with gr.Column(scale=5):
                pages = {}

                # ---------------------------------------------- Inicio / Crear
                def generator_panel(full: bool):
                    with gr.Group(elem_classes="mars-card"):
                        prompt = gr.Textbox(label=t("Descripción (prompt)"), lines=4, elem_id="mars-prompt",
                                            placeholder=t("Un panda guerrero con armadura futurista en una ciudad "
                                                          "japonesa de noche, iluminación cinematográfica…"))
                        negative = gr.Textbox(label=t("Descripción negativa (lo que NO quieres)"), lines=2,
                                              visible=full, placeholder=t("borroso, deformado, texto…"))
                    with gr.Row():
                        style = gr.Dropdown(style_choices(), value=s.default_style, label=t("Estilo"))
                        model = gr.Dropdown(model_choices(), value=s.default_model, label=t("Modelo"))
                    with gr.Accordion(t("Configuración de generación"), open=full):
                        with gr.Row():
                            res = gr.Dropdown([(f"{r} × {r}", r) for r in RESOLUTIONS] + [(t("Personalizada…"), 0)],
                                              value=s.default_resolution, label=t("Resolución"))
                            custom_res = gr.Slider(256, 1536, value=640, step=64, label=t("Resolución personalizada"),
                                                   visible=False)
                            aspect = gr.Dropdown(list(ASPECTS), value=s.default_aspect, label=t("Relación de aspecto"))
                            n = gr.Slider(1, 4, value=1, step=1, label=t("Número de imágenes"))
                        with gr.Row():
                            seed = gr.Number(value=-1, precision=0, label=t("Seed (-1 = aleatorio)"))
                            steps = gr.Slider(1, 80, value=s.default_steps, step=1, label="Steps")
                            cfg = gr.Slider(0, 20, value=s.default_cfg, step=0.5, label="CFG Scale")
                        auto_enh = gr.Checkbox(False, label=t("Mejorar prompt automáticamente (traduce al inglés y "
                                                              "añade calidad)") if translate_default else
                                               t("Mejorar prompt automáticamente (añade calidad)"))
                    with gr.Row():
                        gen_btn = gr.Button(t("🚀 GENERAR IMAGEN"), elem_id="mars-generate", scale=3)
                        cancel_btn = gr.Button(t("⛔ CANCELAR"), elem_id="mars-cancel", scale=1)
                        enh_btn = gr.Button(t("🪄 Mejorar prompt"), scale=1)
                    status = gr.HTML(progress_html(0, 1, t("Listo.")))
                    preview = gr.Gallery(label=t("Vista previa"), columns=2, height=520 if full else 380,
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
                    enh_btn.click(lambda p: enhance_prompt(p, translate=translate_default), prompt, prompt)
                    return dict(prompt=prompt, negative=negative, style=style, model=model, res=res,
                                custom_res=custom_res, aspect=aspect, n=n, seed=seed, steps=steps, cfg=cfg,
                                auto=auto_enh, gen=gen_btn, cancel=cancel_btn, status=status, preview=preview)

                with gr.Column(visible=True) as pages["Inicio"]:
                    home = generator_panel(full=False)
                    gr.Markdown(t("### Creaciones recientes"))
                    recent = gr.Gallery(value=recent_gallery(), columns=4, height=320, format="png",
                                        label=t("Recientes"), object_fit="cover")

                with gr.Column(visible=False) as pages["Crear imagen"]:
                    gr.Markdown(t("## ✨ Crear imagen"))
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
                    gr.Markdown(t("## 🎨 Explorar estilos\nElige una categoría, revisa sus ajustes y usa un ejemplo."))
                    cards = "".join(
                        f"<div class='mars-style-card'><b>{st.icon} {t(st.name)}</b><br>"
                        f"<span class='mars-muted'>Steps {st.steps} · CFG {st.cfg} · {st.aspect}</span><br>"
                        f"<small>{t(st.examples[0])}</small></div>" for st in STYLES)
                    gr.HTML(f"<div style='display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));"
                            f"gap:10px'>{cards}</div>")
                    with gr.Row():
                        ex_style = gr.Dropdown([(t(st.name), st.name) for st in STYLES], value=STYLES[0].name,
                                               label=t("Estilo"))
                        ex_prompt = gr.Radio([t(e) for e in STYLES[0].examples], label=t("Prompts de ejemplo"),
                                             value=t(STYLES[0].examples[0]))
                    ex_info = gr.Markdown()
                    use_btn = gr.Button(t("➡️ Usar en «Crear imagen»"), variant="primary")

                    def style_info(name):
                        st = get_style(name)
                        info = t("**Palabras clave añadidas:** `{pos}`\n\n**Negativo:** `{neg}`\n\n**Ajustes:** "
                                 "{steps} steps · CFG {cfg} · aspecto {aspect}", pos=st.positive,
                                 neg=st.negative or "—", steps=st.steps, cfg=st.cfg, aspect=st.aspect)
                        ex = [t(e) for e in st.examples]
                        return gr.update(choices=ex, value=ex[0]), info
                    ex_style.change(style_info, ex_style, [ex_prompt, ex_info])
                    demo.load(style_info, ex_style, [ex_prompt, ex_info])

                # ---------------------------------------------- Galería
                def gallery_page(title: str, favorites: bool):
                    gr.Markdown(f"## {title}")
                    with gr.Row():
                        q = gr.Textbox(label=t("Buscar (prompt, modelo o estilo)"), scale=3)
                        d_from = gr.Textbox(label=t("Desde (AAAA-MM-DD)"), scale=1)
                        d_to = gr.Textbox(label=t("Hasta (AAAA-MM-DD)"), scale=1)
                        search_btn = gr.Button(t("🔍 Buscar"), scale=1)
                    gal = gr.Gallery(columns=4, height=480, format="png", label=t("Biblioteca"),
                                     object_fit="cover", allow_preview=True)
                    ids = gr.State([])
                    sel_id = gr.State(None)
                    details = gr.Markdown(t("Selecciona una imagen para ver sus datos."))
                    with gr.Row():
                        fav_btn = gr.Button(t("⭐ Favorito / quitar"))
                        dl_btn = gr.DownloadButton(t("⬇️ Descargar"), value=None)
                        del_btn = gr.Button(t("🗑️ Eliminar"), variant="stop")
                        del_ok = gr.Checkbox(False, label=t("Confirmo que quiero eliminarla"))

                    def refresh(text, dfrom, dto):
                        recs = ctx.library.search(text or "", favorites, dfrom or "", dto or "")
                        return [(r.file_path, r.caption()) for r in recs], [r.id for r in recs], \
                            t("{n} imagen(es).", n=len(recs))

                    def select(ids_list, evt: gr.SelectData):
                        if evt.index is None or evt.index >= len(ids_list):
                            return None, "—", gr.update(value=None)
                        r = ctx.library.get(ids_list[evt.index])
                        md = t("**#{id}** · {date} · {fav}\n\n**Prompt:** {prompt}\n\n**Negativo:** {neg}\n\n"
                               "**Modelo:** {model} · **Estilo:** {style} · **Tipo:** {kind}\n\n"
                               "**Tamaño:** {w}×{h} · **Steps:** {steps} · **CFG:** {cfg} · **Seed:** {seed} · "
                               "**Tiempo:** {secs} s\n\n`{path}`",
                               id=r.id, date=r.created_at, fav=t("⭐ Favorito") if r.favorite else "",
                               prompt=r.prompt, neg=r.negative or "—", model=t(r.model),
                               style=t(r.style) if r.style else "—", kind=r.kind, w=r.width, h=r.height,
                               steps=r.steps, cfg=r.cfg, seed=r.seed, secs=r.seconds, path=r.file_path)
                        return r.id, md, gr.update(value=r.file_path)

                    def fav(i, text, dfrom, dto):
                        if i is not None:
                            ctx.library.toggle_favorite(i)
                        return refresh(text, dfrom, dto)

                    def delete(i, ok, text, dfrom, dto):
                        if i is None:
                            g, l, _ = refresh(text, dfrom, dto)
                            return g, l, t("Selecciona una imagen."), None, False
                        if not ok:
                            g, l, _ = refresh(text, dfrom, dto)
                            return g, l, t("⚠️ Marca la casilla de confirmación para eliminar."), i, False
                        ctx.library.delete(i)
                        g, l, msg = refresh(text, dfrom, dto)
                        return g, l, t("🗑️ Eliminada. {msg}", msg=msg), None, False

                    flt = [q, d_from, d_to]
                    search_btn.click(refresh, flt, [gal, ids, details])
                    q.submit(refresh, flt, [gal, ids, details])
                    gal.select(select, ids, [sel_id, details, dl_btn])
                    fav_btn.click(fav, [sel_id] + flt, [gal, ids, details])
                    del_btn.click(delete, [sel_id, del_ok] + flt, [gal, ids, details, sel_id, del_ok])
                    return refresh, flt, [gal, ids, details]

                with gr.Column(visible=False) as pages["Mis creaciones"]:
                    lib_refresh = gallery_page("🖼️ " + t("Mis creaciones"), favorites=False)
                with gr.Column(visible=False) as pages["Favoritos"]:
                    fav_refresh = gallery_page("⭐ " + t("Favoritos"), favorites=True)

                # ---------------------------------------------- Herramientas
                with gr.Column(visible=False) as pages["Herramientas"]:
                    gr.Markdown(t("## 🛠️ Herramientas\nLas herramientas **clásicas** funcionan siempre. Las de "
                                  "**IA** necesitan un modelo local instalado (ver «Modelos IA»)."))
                    local_choices = [c for c in model_choices() if c[1] != "hf-api"]
                    with gr.Tabs():
                        with gr.Tab(t("Upscaler clásico")):
                            gr.Markdown(t("Ampliación **clásica** (Lanczos + enfoque). No añade detalle inventado."))
                            up_in = gr.Image(type="pil", label=t("Imagen"))
                            up_f = gr.Radio([2, 3, 4], value=2, label=t("Factor"))
                            up_btn = gr.Button(t("Ampliar"), variant="primary")
                            up_out, up_msg = gr.Image(label=t("Resultado"), format="png"), gr.Markdown()
                            up_btn.click(lambda im, f: classic_tool(T.upscale_classic, im, int(f), kind="upscale"),
                                         [up_in, up_f], [up_out, up_msg])

                        with gr.Tab(t("Upscaler IA")):
                            gr.Markdown(t("**Real-ESRGAN x4plus** — reconstruye detalle al ampliar. Licencia {lic}. "
                                          "Descarga única de ~{mb} MB desde el repositorio oficial en GitHub, "
                                          "verificada con SHA-256. En CPU puede tardar de segundos a varios minutos "
                                          "según el tamaño; con GPU es casi inmediato.",
                                          lic=RE.LICENSE, mb=RE.MODEL_MB))
                            ai_stat = gr.Markdown(lambda: t("Estado: {s}", s=ctx.upscaler.status()))
                            with gr.Row():
                                ai_auth = gr.Checkbox(False, label=t("Autorizo descargar Real-ESRGAN (~{mb} MB)",
                                                                     mb=RE.MODEL_MB))
                                ai_dl = gr.Button(t("⬇️ Descargar modelo"))
                            ai_in = gr.Image(type="pil", label=t("Imagen"))
                            ai_f = gr.Radio([2, 3, 4], value=4, label=t("Factor"))
                            with gr.Row():
                                ai_btn = gr.Button(t("Ampliar con IA"), variant="primary")
                                ai_cancel = gr.Button(t("⛔ Cancelar"))
                            ai_prog = gr.HTML()
                            ai_out = gr.Image(label=t("Resultado"), format="png")

                            def ai_upscale(im, f):
                                if im is None:
                                    yield progress_html(0, 1, t("❌ Sube una imagen primero.")), None
                                    return
                                if not ctx.upscaler.installed():
                                    yield progress_html(0, 1, t("❌ Descarga primero el modelo (arriba).")), None
                                    return
                                img = load_user_image(im)
                                for html, state, secs in threaded_tool(
                                        lambda prog, cancel: ctx.upscaler.upscale(img, int(f), progress=prog,
                                                                                  cancel=cancel),
                                        t("Ampliando"), "upscale_cancel"):
                                    if html is not None:
                                        yield html, None
                                if state["err"]:
                                    yield progress_html(0, 1, f"❌ {state['err']}"), None
                                    return
                                out = state["res"]
                                rec = ctx.library.save(out, prompt="[upscale IA x%s]" % f, model="Real-ESRGAN x4plus",
                                                       kind="upscale_ai", seconds=secs)
                                yield progress_html(1, 1, t("✅ {w}×{h} en {secs} s · guardado #{id}", w=out.width,
                                                            h=out.height, secs=secs, id=rec.id)), out

                            ai_dl.click(lambda ok: ctx.upscaler.download(ok), ai_auth, ai_stat) \
                                .then(lambda: False, None, ai_auth)
                            ai_btn.click(ai_upscale, [ai_in, ai_f], [ai_prog, ai_out])
                            ai_cancel.click(lambda: (ctx.upscale_cancel.set(),
                                                     progress_html(0, 1, t("⛔ Cancelando…")))[1], None, ai_prog)

                        with gr.Tab(t("Mejorar imagen")):
                            en_in = gr.Image(type="pil", label=t("Imagen"))
                            with gr.Row():
                                en_sh = gr.Slider(0.5, 3, 1.5, step=0.1, label=t("Nitidez"))
                                en_co = gr.Slider(0.5, 2, 1.1, step=0.05, label=t("Contraste"))
                                en_cl = gr.Slider(0, 2, 1.1, step=0.05, label=t("Color"))
                            en_btn = gr.Button(t("Mejorar"), variant="primary")
                            en_out, en_msg = gr.Image(label=t("Resultado"), format="png"), gr.Markdown()
                            en_btn.click(lambda im, a, b, c: classic_tool(T.enhance, im, a, b, c, kind="enhance"),
                                         [en_in, en_sh, en_co, en_cl], [en_out, en_msg])

                        with gr.Tab(t("Restauración")):
                            gr.Markdown(t("Restauración **clásica**: reduce ruido y rayas finas, corrige contraste "
                                          "y dominantes de color."))
                            rs_in = gr.Image(type="pil", label=t("Foto antigua"))
                            rs_dn = gr.Slider(0, 7, 3, step=1, label=t("Reducción de ruido"))
                            rs_btn = gr.Button(t("Restaurar"), variant="primary")
                            rs_out, rs_msg = gr.Image(label=t("Resultado"), format="png"), gr.Markdown()
                            rs_btn.click(lambda im, d: classic_tool(T.restore, im, int(d), kind="restore"),
                                         [rs_in, rs_dn], [rs_out, rs_msg])

                        with gr.Tab(t("Caras IA")):
                            gr.Markdown(t("**GFPGAN v1.4** — restaura caras borrosas, antiguas o de baja calidad. "
                                          "Licencias: {lic}. Descarga única de ~{mb} MB desde los repositorios "
                                          "oficiales en GitHub, verificada con SHA-256. Solo mejora las caras; "
                                          "combínalo con «Restauración» para el resto de la foto.",
                                          lic=FR.LICENSE, mb=FR.TOTAL_MB))
                            fc_stat = gr.Markdown(lambda: t("Estado: {s}", s=ctx.faces.status()))
                            with gr.Row():
                                fc_auth = gr.Checkbox(False, label=t("Autorizo descargar GFPGAN (~{mb} MB)",
                                                                     mb=FR.TOTAL_MB))
                                fc_dl = gr.Button(t("⬇️ Descargar modelo"))
                            fc_in = gr.Image(type="pil", label=t("Foto con caras"))
                            with gr.Row():
                                fc_w = gr.Slider(0, 1, 0.6, step=0.05,
                                                 label=t("Intensidad (más baja = más fiel al original)"))
                                fc_up = gr.Radio([("×1", 1), ("×2", 2)], value=1,
                                                 label=t("Ampliar foto (×2 usa Real-ESRGAN si está instalado)"))
                            with gr.Row():
                                fc_btn = gr.Button(t("Restaurar caras"), variant="primary")
                                fc_cancel = gr.Button(t("⛔ Cancelar"))
                            fc_prog = gr.HTML()
                            fc_out = gr.Image(label=t("Resultado"), format="png")

                            def face_restore(im, wgt, up):
                                if im is None:
                                    yield progress_html(0, 1, t("❌ Sube una imagen primero.")), None
                                    return
                                if not ctx.faces.installed():
                                    yield progress_html(0, 1, t("❌ Descarga primero el modelo (arriba).")), None
                                    return
                                img = load_user_image(im)
                                for html, state, secs in threaded_tool(
                                        lambda prog, cancel: ctx.faces.restore(img, float(wgt), int(up),
                                                                               upscaler=ctx.upscaler, progress=prog,
                                                                               cancel=cancel),
                                        t("Restaurando caras"), "faces_cancel"):
                                    if html is not None:
                                        yield html, None
                                if state["err"]:
                                    yield progress_html(0, 1, f"❌ {state['err']}"), None
                                    return
                                out, n = state["res"]
                                if n == 0:
                                    yield progress_html(0, 1, t("⚠️ No se detectó ninguna cara ({secs} s).",
                                                                secs=secs)), None
                                    return
                                rec = ctx.library.save(out, prompt=f"[faces AI, {wgt}]",
                                                       model="GFPGAN v1.4", kind="faces_ai", seconds=secs)
                                yield progress_html(1, 1, t("✅ {n} cara(s) restaurada(s) en {secs} s · {w}×{h} · "
                                                            "guardado #{id}", n=n, secs=secs, w=out.width,
                                                            h=out.height, id=rec.id)), out

                            fc_dl.click(lambda ok: ctx.faces.download(ok), fc_auth, fc_stat) \
                                .then(lambda: False, None, fc_auth)
                            fc_btn.click(face_restore, [fc_in, fc_w, fc_up], [fc_prog, fc_out])
                            fc_cancel.click(lambda: (ctx.faces_cancel.set(),
                                                     progress_html(0, 1, t("⛔ Cancelando…")))[1], None, fc_prog)

                        with gr.Tab(t("Quitar fondo")):
                            gr.Markdown(t("**Quitafondos con IA integrado** (se ejecuta con OpenCV, sin instalar nada "
                                          "más). Elige el modelo: *Rápido* (U²-Netp, ~4,6 MB) o *Calidad* "
                                          "(IS-Net, ~179 MB), ambos con licencia Apache 2.0. Se descargan una vez "
                                          "desde GitHub con tu autorización y se verifican con SHA-256."))
                            bg_stat = gr.Markdown(lambda: t("Estado: {s}", s=ctx.bgremover.status()))
                            with gr.Row():
                                bg_model = gr.Radio([(t(m.label), m.id) for m in BG.MODELS.values()],
                                                    value="calidad", label=t("Modelo"))
                                bg_auth = gr.Checkbox(False, label=t("Autorizo descargar el modelo elegido"))
                                bg_dl = gr.Button(t("⬇️ Descargar modelo"))
                            bg_in = gr.Image(type="pil", label=t("Imagen"))
                            with gr.Row():
                                bg_mode = gr.Radio([(t("Transparente (PNG)"), "transparente"),
                                                    (t("Color sólido"), "color"), (t("Solo máscara"), "mascara")],
                                                   value="transparente", label=t("Fondo"))
                                bg_color = gr.ColorPicker("#ffffff", label=t("Color de fondo"))
                            with gr.Row():
                                bg_feather = gr.Slider(0, 10, 0, step=1, label=t("Suavizar borde (px)"))
                                bg_thr = gr.Slider(0, 254, 0, step=1, label=t("Recorte duro (0 = bordes suaves)"))
                            bg_btn = gr.Button(t("Quitar fondo"), variant="primary")
                            bg_out, bg_msg = gr.Image(label=t("Resultado"), format="png"), gr.Markdown()

                            def bg_remove(im, model_id, mode, color, feather, thr):
                                if not ctx.bgremover.installed(model_id):
                                    return None, t("❌ {name} no está instalado: descárgalo arriba.",
                                                   name=t(BG.MODELS[model_id].label))
                                return classic_tool(lambda img: ctx.bgremover.remove(img, model_id, mode, color,
                                                                                     int(feather), int(thr)),
                                                    im, kind="nobg")

                            bg_dl.click(lambda m, ok: ctx.bgremover.download(m, ok), [bg_model, bg_auth], bg_stat) \
                                .then(lambda: False, None, bg_auth)
                            bg_btn.click(bg_remove, [bg_in, bg_model, bg_mode, bg_color, bg_feather, bg_thr],
                                         [bg_out, bg_msg])

                        with gr.Tab(t("Mejorar prompt")):
                            pe_in = gr.Textbox(label=t("Tu descripción"), lines=3)
                            pe_tr = gr.Checkbox(translate_default, label=t("Traducir términos frecuentes al inglés"))
                            pe_btn = gr.Button(t("Mejorar"), variant="primary")
                            pe_out = gr.Textbox(label=t("Prompt mejorado"), lines=3)
                            pe_btn.click(enhance_prompt, [pe_in, pe_tr], pe_out)

                        def ai_common():
                            with gr.Row():
                                mdl = gr.Dropdown(local_choices, value=local_choices[0][1] if local_choices else None,
                                                  label=t("Modelo local"))
                                stp = gr.Slider(1, 60, 25, step=1, label="Steps")
                                cf = gr.Slider(0, 15, 7, step=0.5, label="CFG")
                                sd = gr.Number(-1, precision=0, label="Seed")
                            return mdl, stp, cf, sd

                        with gr.Tab("Image to Image"):
                            i2_in = gr.Image(type="pil", label=t("Imagen de referencia"))
                            i2_p = gr.Textbox(label="Prompt")
                            i2_n = gr.Textbox(label=t("Negativo"))
                            i2_s = gr.Slider(0.1, 1.0, 0.6, step=0.05, label=t("Fuerza (más = más cambios)"))
                            i2_m, i2_st, i2_c, i2_sd = ai_common()
                            i2_btn = gr.Button(t("Generar"), variant="primary")
                            i2_stat, i2_out = gr.HTML(), gr.Gallery(columns=3, format="png")
                            i2_btn.click(lambda *a: (yield from ai_tool("img2img", *a)),
                                         [i2_in, i2_p, i2_n, i2_m, i2_s, i2_st, i2_c, i2_sd], [i2_stat, i2_out])

                        with gr.Tab(t("Variaciones")):
                            va_in = gr.Image(type="pil", label=t("Imagen"))
                            va_p = gr.Textbox(label=t("Descripción de la imagen (ayuda a mantenerla)"))
                            va_s = gr.Slider(0.2, 0.9, 0.5, step=0.05, label=t("Intensidad de variación"))
                            va_m, va_st, va_c, va_sd = ai_common()
                            va_btn = gr.Button(t("Crear 3 variaciones"), variant="primary")
                            va_stat, va_out = gr.HTML(), gr.Gallery(columns=3, format="png")
                            va_btn.click(lambda im, p, *a: (yield from ai_tool("variations", im, p, "", *a)),
                                         [va_in, va_p, va_m, va_s, va_st, va_c, va_sd], [va_stat, va_out])

                        with gr.Tab("Inpainting"):
                            gr.Markdown(t("Sube la imagen y **pinta con el pincel** la zona que quieres cambiar."))
                            ip_in = gr.ImageEditor(type="pil", label=t("Imagen + máscara"),
                                                   brush=gr.Brush(colors=["#ffffff"], color_mode="fixed"))
                            ip_p = gr.Textbox(label=t("¿Qué debe aparecer en la zona pintada?"))
                            ip_n = gr.Textbox(label=t("Negativo"))
                            ip_s = gr.Slider(0.3, 1.0, 0.85, step=0.05, label=t("Fuerza"))
                            ip_m, ip_st, ip_c, ip_sd = ai_common()
                            ip_btn = gr.Button(t("Aplicar"), variant="primary")
                            ip_stat, ip_out = gr.HTML(), gr.Gallery(columns=2, format="png")
                            ip_btn.click(lambda *a: (yield from ai_tool("inpaint", *a)),
                                         [ip_in, ip_p, ip_n, ip_m, ip_s, ip_st, ip_c, ip_sd], [ip_stat, ip_out])

                        with gr.Tab("Outpainting"):
                            op_in = gr.Image(type="pil", label=t("Imagen"))
                            with gr.Row():
                                op_l = gr.Slider(0, 512, 128, step=8, label=t("Izquierda"))
                                op_r = gr.Slider(0, 512, 128, step=8, label=t("Derecha"))
                                op_t = gr.Slider(0, 512, 0, step=8, label=t("Arriba"))
                                op_b = gr.Slider(0, 512, 0, step=8, label=t("Abajo"))
                            op_p = gr.Textbox(label=t("Descripción de la escena completa"))
                            op_m, op_st, op_c, op_sd = ai_common()
                            op_btn = gr.Button(t("Ampliar"), variant="primary")
                            op_stat, op_out = gr.HTML(), gr.Gallery(columns=2, format="png")

                            def _op(im, p, m, st, c, sd, l, r, tp, b):
                                yield from ai_tool("outpaint", im, p, "", m, 1.0, st, c, sd,
                                                   extra=(int(l), int(r), int(tp), int(b)))
                            op_btn.click(_op, [op_in, op_p, op_m, op_st, op_c, op_sd, op_l, op_r, op_t, op_b],
                                         [op_stat, op_out])

                # ---------------------------------------------- Modelos
                with gr.Column(visible=False) as pages["Modelos IA"]:
                    gr.Markdown(t("## 🧠 Modelos IA\nNada se descarga sin tu autorización explícita. "
                                  "Los modelos se guardan en la carpeta de modelos configurada."))
                    mtable = gr.Dataframe(headers=[t("Modelo"), t("Estado"), t("Conexión"), t("Compatibilidad"),
                                                   t("Descarga"), t("VRAM mín."), t("RAM mín."), t("Licencia")],
                                          interactive=False, wrap=True)
                    with gr.Row():
                        msel = gr.Dropdown([(t(sp.name), sp.id) for sp in ctx.models.all_specs()],
                                           value=s.default_model, label=t("Modelo"))
                        mrefresh = gr.Button(t("🔄 Actualizar"))
                    minfo = gr.Markdown()
                    mauth = gr.Checkbox(False, label=t("Autorizo descargar este modelo (he revisado tamaño y licencia)"))
                    with gr.Row():
                        mdl_btn = gr.Button(t("⬇️ Descargar / instalar"), variant="primary")
                        mdef_btn = gr.Button(t("✅ Usar por defecto"))
                        mdel_btn = gr.Button(t("🗑️ Eliminar del disco"), variant="stop")
                    mmsg = gr.Markdown()
                    with gr.Accordion(t("Añadir modelo local (.safetensors)"), open=False):
                        cpath = gr.Textbox(label=t("Ruta del archivo"),
                                           placeholder=r"C:\Modelos\mi_modelo.safetensors")
                        cname = gr.Textbox(label=t("Nombre"))
                        cbase = gr.Radio([("SD 1.5", "sd15"), ("SDXL", "sdxl")], value="sd15",
                                         label=t("Arquitectura"))
                        cadd = gr.Button(t("Añadir"))

                    def table():
                        rows = []
                        for st in ctx.models.statuses():
                            sp = st.spec
                            rows.append([t(sp.name), st.state, sp.connection, t(st.compatibility),
                                         f"{sp.download_gb} GB" if sp.download_gb else "—",
                                         f"{sp.min_vram_gb} GB" if sp.min_vram_gb else "—",
                                         f"{sp.min_ram_gb} GB", t(sp.license)])
                        return rows

                    def info(mid):
                        try:
                            sp = ctx.models.spec(mid)
                        except KeyError:
                            return ""
                        st = ctx.models.status(sp)
                        lic = f"[{t(sp.license)}]({sp.license_url})" if sp.license_url else t(sp.license)
                        return t("### {name}\n**Estado:** {state} · **Compatibilidad con tu equipo:** {compat}\n\n"
                                 "**Repositorio:** `{repo}` · **Licencia:** {lic}\n\n**Espacio necesario:** {gb} GB · "
                                 "**VRAM mínima:** {vram} GB · **RAM mínima:** {ram} GB\n\n{notes}",
                                 name=t(sp.name), state=st.state, compat=t(st.compatibility), repo=sp.repo_id,
                                 lic=lic, gb=sp.download_gb or "—", vram=sp.min_vram_gb or "—",
                                 ram=sp.min_ram_gb, notes=t(sp.notes))

                    def all_model_updates():
                        ch = model_choices()
                        return [gr.update(choices=ch), gr.update(choices=ch)]

                    def do_download(mid, ok, progress=gr.Progress()):
                        progress(0, desc=t("Descargando… (puede tardar mucho, no cierres la ventana)"))
                        msg = ctx.models.download(mid, ok)
                        return [msg, table(), info(mid), False] + all_model_updates()

                    def do_default(mid):
                        ctx.store.update(default_model=mid)
                        return [t("Modelo por defecto: **{name}**", name=t(ctx.models.spec(mid).name)), table(),
                                info(mid), False] + [gr.update(choices=model_choices(), value=mid)] * 2

                    def do_delete(mid, ok):
                        if not ok:
                            return [t("⚠️ Marca la casilla para confirmar."), table(), info(mid), False] + \
                                all_model_updates()
                        return [ctx.models.delete(mid), table(), info(mid), False] + all_model_updates()

                    def do_add(path, name, base):
                        msg = ctx.models.add_custom(path, name, base)
                        return [msg, table(),
                                gr.update(choices=[(t(sp.name), sp.id) for sp in ctx.models.all_specs()])] \
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
                    gr.Markdown(t("## ⚙️ Configuración"))
                    with gr.Tab(t("General")):
                        c_lang = gr.Dropdown([(v, k) for k, v in LANGUAGES.items()], value=get_language(),
                                             label=t("Idioma"),
                                             info=t("El cambio se aplica al reiniciar MARS.AI."))
                        gr.Dropdown([(t("Oscuro (MARS)"), "oscuro")], value="oscuro", label=t("Tema"))
                        c_out = gr.Textbox(str(s.output_path), label=t("Carpeta de imágenes"))
                        c_mod = gr.Textbox(str(s.models_path), label=t("Carpeta de modelos"))
                    with gr.Tab(t("Generación")):
                        c_style = gr.Dropdown(style_choices(), value=s.default_style, label=t("Estilo por defecto"))
                        c_steps = gr.Slider(1, 80, s.default_steps, step=1, label=t("Steps por defecto"))
                        c_cfg = gr.Slider(0, 20, s.default_cfg, step=0.5, label=t("CFG por defecto"))
                        c_res = gr.Dropdown(RESOLUTIONS, value=s.default_resolution,
                                            label=t("Resolución por defecto"))
                        c_asp = gr.Dropdown(list(ASPECTS), value=s.default_aspect, label=t("Aspecto por defecto"))
                    with gr.Tab(t("Memoria")):
                        c_low = gr.Checkbox(s.low_power_mode, label=t("Modo bajo consumo (descarga partes del "
                                                                      "modelo a la CPU; menos VRAM, algo más lento)"))
                        c_unl = gr.Checkbox(s.unload_after_generation, label=t("Liberar el modelo de memoria tras "
                                                                               "cada generación (mínima RAM, más lento)"))
                        c_batch = gr.Slider(1, 8, s.max_batch, step=1, label=t("Máximo de imágenes por lote"))
                    with gr.Tab(t("APIs y conexiones")):
                        gr.Markdown(t(
                            "**API de Hugging Face (opcional).** Crea un token gratuito en "
                            "huggingface.co → Settings → Access Tokens. Las cuentas gratuitas incluyen un "
                            "crédito mensual limitado; **las condiciones pueden cambiar y el uso extra puede "
                            "tener coste**. Revisa https://huggingface.co/docs/inference-providers/pricing. "
                            "MARS.AI nunca contrata nada por ti.\n\n"
                            "El token se guarda en el **Administrador de credenciales de Windows** (keyring) y "
                            "nunca se escribe en registros ni en archivos de configuración."))

                        def token_line():
                            return t("Token actual: `{tok}` · Almacén seguro: {ok}",
                                     tok=ctx.secrets.mask(ctx.secrets.get("huggingface")),
                                     ok="✅" if ctx.secrets.secure_backend_available else "❌")
                        tok_state = gr.Markdown(token_line)
                        c_tok = gr.Textbox(type="password", label=t("Nuevo token de Hugging Face (vacío = no cambiar)"))
                        c_tok_del = gr.Checkbox(False, label=t("Borrar el token guardado"))
                        c_hfm = gr.Textbox(s.hf_api_model, label=t("Modelo para la API"),
                                           info=t("Ej.: black-forest-labs/FLUX.1-schnell, "
                                                  "stabilityai/stable-diffusion-xl-base-1.0"))
                        c_cost = gr.Checkbox(s.accepted_api_cost_warning,
                                             label=t("Entiendo que la API externa puede tener límites o costes"))
                    with gr.Tab(t("Sistema")):
                        gr.Code(format_report(ctx.system), language=None, label=t("Diagnóstico del equipo"))
                    c_save = gr.Button(t("💾 Guardar configuración"), variant="primary")
                    c_msg = gr.Markdown()

                    def save_cfg(lang, out, mod, style, steps, cfg, res, asp, low, unl, batch, tok, tok_del, hfm,
                                 cost):
                        for label, pth in ((t("imágenes"), out), (t("modelos"), mod)):
                            try:
                                Path(pth).mkdir(parents=True, exist_ok=True)
                            except OSError as exc:
                                return t("❌ Carpeta de {label} no válida: {err}", label=label, err=exc), gr.update()
                        lang_changed = lang != ctx.settings.language
                        ctx.store.update(language=lang, output_dir=out, models_dir=mod, default_style=style,
                                         default_steps=int(steps), default_cfg=float(cfg), default_resolution=int(res),
                                         default_aspect=asp, low_power_mode=bool(low),
                                         unload_after_generation=bool(unl), max_batch=int(batch),
                                         hf_api_model=hfm.strip() or "black-forest-labs/FLUX.1-schnell",
                                         accepted_api_cost_warning=bool(cost))
                        ctx.library.set_output_dir(Path(out))
                        msg = t("✅ Configuración guardada.")
                        if lang_changed:
                            msg += " " + t("🌐 Reinicia MARS.AI para aplicar el idioma.")
                        if tok_del:
                            ctx.secrets.delete("huggingface")
                            msg += " " + t("Token borrado.")
                        elif tok:
                            if not cost:
                                msg += " " + t("⚠️ Token NO guardado: acepta primero el aviso de costes.")
                            elif ctx.secrets.set("huggingface", tok.strip()):
                                msg += " " + t("Token guardado de forma segura.")
                            else:
                                msg += " " + t("❌ No se pudo guardar el token (almacén seguro no disponible).")
                        ctx.models.unload()  # aplica cambios de memoria / API
                        return msg, token_line()
                    c_save.click(save_cfg, [c_lang, c_out, c_mod, c_style, c_steps, c_cfg, c_res, c_asp, c_low,
                                            c_unl, c_batch, c_tok, c_tok_del, c_hfm, c_cost], [c_msg, tok_state]) \
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
