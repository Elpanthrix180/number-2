"""Traducciones al inglés de MARS.AI. Clave: texto original en español."""

EN: dict[str, str] = {
    # ------------------------------------------------------------ general
    "Transforma tu imaginación en imágenes.": "Turn your imagination into images.",
    "(no configurada)": "(not set)",
    "Memoria liberada (difusión, Real-ESRGAN, GFPGAN y quitafondos).":
        "Memory freed (diffusion, Real-ESRGAN, GFPGAN and background remover).",
    "No hay ninguna generación en curso.": "No generation is running.",
    "Cancelando… (se detendrá al terminar el paso actual)": "Cancelling… (it will stop after the current step)",
    "Memoria liberada.": "Memory freed.",
    "Cancelado": "Cancelled",
    "Imágenes : {path}": "Images : {path}",
    "Modelos  : {path}": "Models : {path}",
    "Abre http://127.0.0.1:{port} si el navegador no se abre solo. Ctrl+C para salir.":
        "Open http://127.0.0.1:{port} if the browser does not open by itself. Press Ctrl+C to quit.",

    # ------------------------------------------------------- diagnóstico
    "Python {v}: se recomienda Python 3.10–3.13 (PyTorch puede no tener versión para otras).":
        "Python {v}: Python 3.10–3.13 is recommended (PyTorch may not support other versions).",
    "Menos de 8 GB de RAM: usa SD 1.5 a 512×512 en modo bajo consumo, o una API externa.":
        "Less than 8 GB of RAM: use SD 1.5 at 512×512 in low-power mode, or an external API.",
    "Sin GPU NVIDIA: la generación local funcionará en CPU (lenta: minutos por imagen).":
        "No NVIDIA GPU: local generation will run on the CPU (slow: minutes per image).",
    "Menos de 10 GB libres: no habrá espacio para la mayoría de modelos locales.":
        "Less than 10 GB free: there will not be enough space for most local models.",
    "Sistema operativo": "Operating system",
    "CPU (núcleos)": "CPU (cores)",
    "RAM total": "Total RAM",
    "{total} GB (disponible {avail} GB)": "{total} GB ({avail} GB available)",
    "Disco libre": "Free disk space",
    "Perfil recomendado": "Recommended profile",
    "VRAM desconocida": "unknown VRAM",
    "no se detectó GPU NVIDIA": "no NVIDIA GPU detected",
    "instalado": "installed",
    "no instalado": "not installed",
    " (CUDA activo)": " (CUDA active)",
    "(no recomendado)": "(not recommended)",

    # ----------------------------------------------------------- estilos
    "Ninguno": "None",
    "Fotorealismo": "Photorealism",
    "Anime": "Anime",
    "Manga": "Manga",
    "Dibujos animados": "Cartoons",
    "Animación 3D": "3D animation",
    "Fantasía": "Fantasy",
    "Ciencia ficción": "Science fiction",
    "Terror": "Horror",
    "Arte digital": "Digital art",
    "Pintura artística": "Fine-art painting",
    "Acuarela": "Watercolour",
    "Caricaturas": "Caricatures",
    "Retratos": "Portraits",
    "Superhéroes": "Superheroes",
    "Criaturas y monstruos": "Creatures and monsters",
    "Paisajes": "Landscapes",
    "Arquitectura": "Architecture",
    "Diseño de productos": "Product design",
    "Logotipos": "Logos",
    "Ilustraciones infantiles": "Children's illustrations",
    # ejemplos de prompts
    "Retrato de una anciana pescadora en un puerto al amanecer":
        "Portrait of an elderly fisherwoman in a harbour at dawn",
    "Taza de café humeante sobre una mesa de madera, luz de ventana":
        "Steaming cup of coffee on a wooden table, window light",
    "Chica samurái bajo cerezos en flor, viento": "Samurai girl under blossoming cherry trees, wind",
    "Chico con chaqueta de cuero en una azotea de Tokio de noche":
        "Young man in a leather jacket on a Tokyo rooftop at night",
    "Detective en un callejón lluvioso, viñeta dramática": "Detective in a rainy alley, dramatic panel",
    "Duelo de espadachines en un tejado": "Swordsmen duelling on a rooftop",
    "Un perro con gafas de sol surfeando": "A dog wearing sunglasses, surfing",
    "Un dragón simpático vendiendo helados": "A friendly dragon selling ice cream",
    "Un robot pequeño regando plantas en Marte": "A small robot watering plants on Mars",
    "Una familia de zorros cenando en su madriguera": "A family of foxes having dinner in their den",
    "Castillo flotante entre nubes doradas": "Floating castle among golden clouds",
    "Elfa arquera en un bosque luminoso": "Elf archer in a glowing forest",
    "Ciudad cyberpunk con coches voladores bajo la lluvia": "Cyberpunk city with flying cars in the rain",
    "Astronauta frente a un planeta con anillos": "Astronaut facing a ringed planet",
    "Casa abandonada en el bosque con una luz en la ventana":
        "Abandoned house in the woods with a light in the window",
    "Pasillo de hospital antiguo con niebla": "Old hospital corridor full of fog",
    "Ballena cósmica nadando entre galaxias": "Cosmic whale swimming among galaxies",
    "Tigre hecho de cristales de colores": "Tiger made of coloured crystals",
    "Campo de girasoles al atardecer": "Sunflower field at sunset",
    "Retrato de un caballero renacentista": "Portrait of a Renaissance gentleman",
    "Pueblo costero mediterráneo": "Mediterranean seaside village",
    "Ramo de flores silvestres en un jarrón": "Bunch of wildflowers in a vase",
    "Chef con un bigote enorme y gorro gigante": "Chef with a huge moustache and a giant hat",
    "Científico despeinado con gafas enormes": "Scruffy scientist with enormous glasses",
    "Mujer con pecas y pelo rizado, luz suave": "Woman with freckles and curly hair, soft light",
    "Hombre mayor con barba blanca, luz de Rembrandt": "Older man with a white beard, Rembrandt lighting",
    "Superheroína volando sobre una metrópolis": "Superheroine flying over a metropolis",
    "Héroe con armadura de energía azul": "Hero in blue energy armour",
    "Gólem de musgo en un pantano": "Moss golem in a swamp",
    "Criatura marina bioluminiscente gigante": "Giant bioluminescent sea creature",
    "Fiordo noruego con aurora boreal": "Norwegian fjord with the northern lights",
    "Desierto con dunas rojas al atardecer": "Desert with red dunes at sunset",
    "Casa minimalista de hormigón sobre un acantilado": "Minimalist concrete house on a cliff",
    "Biblioteca futurista llena de plantas": "Futuristic library full of plants",
    "Zapatillas deportivas futuristas flotando": "Futuristic sneakers floating in the air",
    "Botella de perfume de cristal sobre mármol": "Glass perfume bottle on marble",
    "Logo de una cafetería con un búho": "Logo for a coffee shop featuring an owl",
    "Logo minimalista de una startup espacial": "Minimalist logo for a space startup",
    "Un conejo leyendo un libro bajo una seta": "A rabbit reading a book under a mushroom",
    "Niña y su gato explorando la luna": "A girl and her cat exploring the moon",

    # ------------------------------------------------------ navegación
    "Inicio": "Home",
    "Crear imagen": "Create image",
    "Explorar estilos": "Explore styles",
    "Mis creaciones": "My creations",
    "Favoritos": "Favourites",
    "Herramientas": "Tools",
    "Modelos IA": "AI models",
    "Configuración": "Settings",
    "🧹 Liberar memoria": "🧹 Free memory",

    # ------------------------------------------------------- generador
    "Escribe una descripción (prompt) para generar.": "Write a description (prompt) to generate.",
    "Generación": "Generation",
    "Preparando {name} ({w}×{h})… la primera vez puede tardar en cargar el modelo.":
        "Preparing {name} ({w}×{h})… the first time, loading the model can take a while.",
    "⏳ {label}: paso {step}/{total} · {secs} s": "⏳ {label}: step {step}/{total} · {secs} s",
    "⛔ Cancelado tras {secs} s": "⛔ Cancelled after {secs} s",
    "✅ {label}: terminado en {secs} s · seed {seed}": "✅ {label}: finished in {secs} s · seed {seed}",
    "### Creaciones recientes": "### Recent creations",
    "## ✨ Crear imagen": "## ✨ Create image",
    "Configuración de generación": "Generation settings",
    "🚀 GENERAR IMAGEN": "🚀 GENERATE IMAGE",
    "⛔ CANCELAR": "⛔ CANCEL",
    "🪄 Mejorar prompt": "🪄 Enhance prompt",
    "Listo.": "Ready.",
    "Vista previa": "Preview",
    "Recientes": "Recent",
    "Descripción (prompt)": "Description (prompt)",
    "Un panda guerrero con armadura futurista en una ciudad japonesa de noche, iluminación cinematográfica…":
        "A warrior panda in futuristic armour in a Japanese city at night, cinematic lighting…",
    "Descripción negativa (lo que NO quieres)": "Negative prompt (what you do NOT want)",
    "borroso, deformado, texto…": "blurry, deformed, text…",
    "Estilo": "Style",
    "Modelo": "Model",
    "Resolución": "Resolution",
    "Personalizada…": "Custom…",
    "Resolución personalizada": "Custom resolution",
    "Relación de aspecto": "Aspect ratio",
    "Número de imágenes": "Number of images",
    "Seed (-1 = aleatorio)": "Seed (-1 = random)",
    "Mejorar prompt automáticamente (traduce al inglés y añade calidad)":
        "Enhance prompt automatically (translates Spanish to English and adds quality terms)",
    "Mejorar prompt automáticamente (añade calidad)": "Enhance prompt automatically (adds quality terms)",

    # ---------------------------------------------------------- estilos
    "## 🎨 Explorar estilos\nElige una categoría, revisa sus ajustes y usa un ejemplo.":
        "## 🎨 Explore styles\nPick a category, review its settings and try an example.",
    "Prompts de ejemplo": "Example prompts",
    "➡️ Usar en «Crear imagen»": "➡️ Use in “Create image”",
    "**Palabras clave añadidas:** `{pos}`\n\n**Negativo:** `{neg}`\n\n**Ajustes:** {steps} steps · CFG {cfg} · "
    "aspecto {aspect}":
        "**Added keywords:** `{pos}`\n\n**Negative:** `{neg}`\n\n**Settings:** {steps} steps · CFG {cfg} · "
        "aspect {aspect}",

    # ---------------------------------------------------------- galería
    "Buscar (prompt, modelo o estilo)": "Search (prompt, model or style)",
    "Desde (AAAA-MM-DD)": "From (YYYY-MM-DD)",
    "Hasta (AAAA-MM-DD)": "To (YYYY-MM-DD)",
    "🔍 Buscar": "🔍 Search",
    "Biblioteca": "Library",
    "Selecciona una imagen para ver sus datos.": "Select an image to see its details.",
    "⭐ Favorito / quitar": "⭐ Add / remove favourite",
    "⬇️ Descargar": "⬇️ Download",
    "🗑️ Eliminar": "🗑️ Delete",
    "Confirmo que quiero eliminarla": "I confirm I want to delete it",
    "{n} imagen(es).": "{n} image(s).",
    "**#{id}** · {date} · {fav}\n\n**Prompt:** {prompt}\n\n**Negativo:** {neg}\n\n**Modelo:** {model} · "
    "**Estilo:** {style} · **Tipo:** {kind}\n\n**Tamaño:** {w}×{h} · **Steps:** {steps} · **CFG:** {cfg} · "
    "**Seed:** {seed} · **Tiempo:** {secs} s\n\n`{path}`":
        "**#{id}** · {date} · {fav}\n\n**Prompt:** {prompt}\n\n**Negative:** {neg}\n\n**Model:** {model} · "
        "**Style:** {style} · **Type:** {kind}\n\n**Size:** {w}×{h} · **Steps:** {steps} · **CFG:** {cfg} · "
        "**Seed:** {seed} · **Time:** {secs} s\n\n`{path}`",
    "⭐ Favorito": "⭐ Favourite",
    "Selecciona una imagen.": "Select an image.",
    "⚠️ Marca la casilla de confirmación para eliminar.": "⚠️ Tick the confirmation box to delete.",
    "🗑️ Eliminada. {msg}": "🗑️ Deleted. {msg}",
    "La imagen es demasiado grande.": "The image is too large.",
    "Formato no admitido. Usa PNG, JPG, WEBP o BMP.": "Unsupported format. Use PNG, JPG, WEBP or BMP.",

    # ----------------------------------------------------- herramientas
    "## 🛠️ Herramientas\nLas herramientas **clásicas** funcionan siempre. Las de **IA** necesitan un modelo "
    "local instalado (ver «Modelos IA»).":
        "## 🛠️ Tools\n**Classic** tools always work. **AI** tools need a local model installed "
        "(see “AI models”).",
    "Quitafondos IA": "AI background remover",
    "Herramienta clásica": "Classic tool",
    "❌ Sube una imagen primero.": "❌ Upload an image first.",
    "✅ Listo en {secs} s · {w}×{h} · guardado como #{id}": "✅ Done in {secs} s · {w}×{h} · saved as #{id}",
    "Esta herramienta necesita un modelo local instalado (no la API).":
        "This tool needs a local model installed (not the API).",
    "{name} no admite {mode}.": "{name} does not support {mode}.",
    "Sube una imagen de referencia.": "Upload a reference image.",
    "Imagen": "Image",
    "Factor": "Factor",
    "Resultado": "Result",
    "Estado: {s}": "Status: {s}",
    "⬇️ Descargar modelo": "⬇️ Download model",
    "⛔ Cancelar": "⛔ Cancel",
    "⛔ Cancelando…": "⛔ Cancelling…",
    "❌ Descarga primero el modelo (arriba).": "❌ Download the model first (above).",
    # upscaler clásico
    "Upscaler clásico": "Classic upscaler",
    "Ampliación **clásica** (Lanczos + enfoque). No añade detalle inventado.":
        "**Classic** upscaling (Lanczos + sharpening). It does not invent new detail.",
    "Ampliar": "Upscale",
    "El factor debe ser 2, 3 o 4.": "The factor must be 2, 3 or 4.",
    "El resultado superaría {px}px de lado.": "The result would exceed {px}px per side.",
    # upscaler IA
    "Upscaler IA": "AI upscaler",
    "**Real-ESRGAN x4plus** — reconstruye detalle al ampliar. Licencia {lic}. Descarga única de ~{mb} MB desde "
    "el repositorio oficial en GitHub, verificada con SHA-256. En CPU puede tardar de segundos a varios minutos "
    "según el tamaño; con GPU es casi inmediato.":
        "**Real-ESRGAN x4plus** — rebuilds detail while upscaling. Licence {lic}. One-time download of ~{mb} MB "
        "from the official GitHub repository, verified with SHA-256. On a CPU it takes from seconds to several "
        "minutes depending on size; on a GPU it is almost instant.",
    "Autorizo descargar Real-ESRGAN (~{mb} MB)": "I authorise downloading Real-ESRGAN (~{mb} MB)",
    "Ampliar con IA": "Upscale with AI",
    "Ampliando": "Upscaling",
    "✅ {w}×{h} en {secs} s · guardado #{id}": "✅ {w}×{h} in {secs} s · saved #{id}",
    "🔴 Falta PyTorch (ejecuta install_windows.bat)": "🔴 PyTorch is missing (run install_windows.bat)",
    "Real-ESRGAN ya está instalado.": "Real-ESRGAN is already installed.",
    "✅ Real-ESRGAN instalado y verificado.": "✅ Real-ESRGAN installed and verified.",
    "Real-ESRGAN no está instalado. Descárgalo en Herramientas → Upscaler IA.":
        "Real-ESRGAN is not installed. Download it in Tools → AI upscaler.",
    "La escala debe ser 2, 3 o 4.": "The scale must be 2, 3 or 4.",
    "Imagen demasiado grande para ampliar (máx. 4096 px de lado).":
        "Image too large to upscale (max. 4096 px per side).",
    # mejora
    "Mejorar imagen": "Enhance image",
    "Mejorar": "Enhance",
    "Nitidez": "Sharpness",
    "Contraste": "Contrast",
    "Color": "Colour",
    # restauración
    "Restauración": "Restoration",
    "Restauración **clásica**: reduce ruido y rayas finas, corrige contraste y dominantes de color.":
        "**Classic** restoration: reduces noise and fine scratches, fixes contrast and colour casts.",
    "Foto antigua": "Old photo",
    "Reducción de ruido": "Noise reduction",
    "Restaurar": "Restore",
    # caras
    "Caras IA": "AI faces",
    "**GFPGAN v1.4** — restaura caras borrosas, antiguas o de baja calidad. Licencias: {lic}. Descarga única de "
    "~{mb} MB desde los repositorios oficiales en GitHub, verificada con SHA-256. Solo mejora las caras; "
    "combínalo con «Restauración» para el resto de la foto.":
        "**GFPGAN v1.4** — restores blurry, old or low-quality faces. Licences: {lic}. One-time download of "
        "~{mb} MB from the official GitHub repositories, verified with SHA-256. It only improves faces; combine "
        "it with “Restoration” for the rest of the photo.",
    "Autorizo descargar GFPGAN (~{mb} MB)": "I authorise downloading GFPGAN (~{mb} MB)",
    "Foto con caras": "Photo with faces",
    "Intensidad (más baja = más fiel al original)": "Strength (lower = closer to the original)",
    "Ampliar foto (×2 usa Real-ESRGAN si está instalado)": "Upscale photo (×2 uses Real-ESRGAN if installed)",
    "Restaurar caras": "Restore faces",
    "Restaurando caras": "Restoring faces",
    "⚠️ No se detectó ninguna cara ({secs} s).": "⚠️ No faces were detected ({secs} s).",
    "✅ {n} cara(s) restaurada(s) en {secs} s · {w}×{h} · guardado #{id}":
        "✅ {n} face(s) restored in {secs} s · {w}×{h} · saved #{id}",
    "✅ GFPGAN y el detector de caras están instalados y verificados.":
        "✅ GFPGAN and the face detector are installed and verified.",
    "La restauración de caras ya está instalada.": "Face restoration is already installed.",
    "La restauración de caras no está instalada. Descárgala en Herramientas → Caras IA.":
        "Face restoration is not installed. Download it in Tools → AI faces.",
    "La ampliación debe ser 1 o 2.": "The upscale factor must be 1 or 2.",
    "La intensidad debe estar entre 0 y 1.": "The strength must be between 0 and 1.",
    "❌ {name} no coincide con la huella oficial (SHA-256). Se ha descartado.":
        "❌ {name} does not match the official fingerprint (SHA-256). It has been discarded.",
    "❌ Error al descargar {name}: {err}": "❌ Error downloading {name}: {err}",
    # quitar fondo
    "Quitar fondo": "Remove background",
    "**Quitafondos con IA integrado** (se ejecuta con OpenCV, sin instalar nada más). Elige el modelo: *Rápido* "
    "(U²-Netp, ~4,6 MB) o *Calidad* (IS-Net, ~179 MB), ambos con licencia Apache 2.0. Se descargan una vez desde "
    "GitHub con tu autorización y se verifican con SHA-256.":
        "**Built-in AI background remover** (runs on OpenCV, nothing else to install). Choose a model: *Fast* "
        "(U²-Netp, ~4.6 MB) or *Quality* (IS-Net, ~179 MB), both under the Apache 2.0 licence. They are "
        "downloaded once from GitHub with your permission and verified with SHA-256.",
    "Rápido (U²-Netp, ~4,6 MB)": "Fast (U²-Netp, ~4.6 MB)",
    "Calidad (IS-Net, ~179 MB)": "Quality (IS-Net, ~179 MB)",
    "Autorizo descargar el modelo elegido": "I authorise downloading the chosen model",
    "Fondo": "Background",
    "Transparente (PNG)": "Transparent (PNG)",
    "Color sólido": "Solid colour",
    "Solo máscara": "Mask only",
    "Color de fondo": "Background colour",
    "Suavizar borde (px)": "Soften edge (px)",
    "Recorte duro (0 = bordes suaves)": "Hard cut-out (0 = soft edges)",
    "❌ {name} no está instalado: descárgalo arriba.": "❌ {name} is not installed: download it above.",
    "🔴 Falta opencv-python-headless (ejecuta install_windows.bat)":
        "🔴 opencv-python-headless is missing (run install_windows.bat)",
    "❌ Modelo desconocido.": "❌ Unknown model.",
    "✅ {name} instalado y verificado.": "✅ {name} installed and verified.",
    "{name} no está instalado. Descárgalo arriba.": "{name} is not installed. Download it above.",
    "Imagen demasiado grande (máx. {px}px de lado).": "Image too large (max. {px}px per side).",
    # mejorar prompt
    "Mejorar prompt": "Enhance prompt",
    "Tu descripción": "Your description",
    "Traducir términos frecuentes al inglés": "Translate common Spanish terms into English",
    "Prompt mejorado": "Enhanced prompt",
    # herramientas de difusión
    "Modelo local": "Local model",
    "Imagen de referencia": "Reference image",
    "Negativo": "Negative",
    "Fuerza (más = más cambios)": "Strength (higher = more changes)",
    "Generar": "Generate",
    "Variaciones": "Variations",
    "Descripción de la imagen (ayuda a mantenerla)": "Description of the image (helps preserve it)",
    "Intensidad de variación": "Variation strength",
    "Crear 3 variaciones": "Create 3 variations",
    "Sube la imagen y **pinta con el pincel** la zona que quieres cambiar.":
        "Upload the image and **paint with the brush** over the area you want to change.",
    "Imagen + máscara": "Image + mask",
    "¿Qué debe aparecer en la zona pintada?": "What should appear in the painted area?",
    "Fuerza": "Strength",
    "Aplicar": "Apply",
    "Izquierda": "Left",
    "Derecha": "Right",
    "Arriba": "Top",
    "Abajo": "Bottom",
    "Descripción de la escena completa": "Description of the whole scene",
    "Los márgenes no pueden ser negativos.": "Margins cannot be negative.",
    "Indica al menos un margen para ampliar.": "Set at least one margin to extend.",
    "Sube una imagen y pinta la zona a modificar.": "Upload an image and paint the area to change.",
    "No has pintado ninguna zona. Usa el pincel sobre lo que quieras cambiar.":
        "You have not painted any area. Use the brush on what you want to change.",

    # ----------------------------------------------------------- modelos
    "## 🧠 Modelos IA\nNada se descarga sin tu autorización explícita. Los modelos se guardan en la carpeta de "
    "modelos configurada.":
        "## 🧠 AI models\nNothing is downloaded without your explicit permission. Models are stored in the "
        "configured models folder.",
    "Estado": "Status",
    "Conexión": "Connection",
    "Compatibilidad": "Compatibility",
    "Descarga": "Download",
    "VRAM mín.": "Min. VRAM",
    "RAM mín.": "Min. RAM",
    "Licencia": "Licence",
    "🔄 Actualizar": "🔄 Refresh",
    "Autorizo descargar este modelo (he revisado tamaño y licencia)":
        "I authorise downloading this model (I have checked its size and licence)",
    "⬇️ Descargar / instalar": "⬇️ Download / install",
    "✅ Usar por defecto": "✅ Set as default",
    "🗑️ Eliminar del disco": "🗑️ Delete from disk",
    "Añadir modelo local (.safetensors)": "Add local model (.safetensors)",
    "Ruta del archivo": "File path",
    "Nombre": "Name",
    "Añadir": "Add",
    "### {name}\n**Estado:** {state} · **Compatibilidad con tu equipo:** {compat}\n\n**Repositorio:** `{repo}` · "
    "**Licencia:** {lic}\n\n**Espacio necesario:** {gb} GB · **VRAM mínima:** {vram} GB · **RAM mínima:** "
    "{ram} GB\n\n{notes}":
        "### {name}\n**Status:** {state} · **Compatibility with your computer:** {compat}\n\n**Repository:** "
        "`{repo}` · **Licence:** {lic}\n\n**Space needed:** {gb} GB · **Minimum VRAM:** {vram} GB · "
        "**Minimum RAM:** {ram} GB\n\n{notes}",
    "Descargando… (puede tardar mucho, no cierres la ventana)":
        "Downloading… (this can take a long time; do not close the window)",
    "Modelo por defecto: **{name}**": "Default model: **{name}**",
    "⚠️ Marca la casilla para confirmar.": "⚠️ Tick the box to confirm.",
    "El más ligero. Recomendado para equipos modestos y para CPU.":
        "The lightest one. Recommended for modest computers and for CPU.",
    "Stability AI Community / no comercial (revisar)": "Stability AI Community / non-commercial (check it)",
    "Muy rápido (1–4 pasos). Uso comercial sujeto a la licencia de Stability AI.":
        "Very fast (1–4 steps). Commercial use is subject to the Stability AI licence.",
    "Alta calidad a 1024×1024. Necesita GPU con 8 GB+ de VRAM.":
        "High quality at 1024×1024. Needs a GPU with 8 GB+ of VRAM.",
    "Calidad excelente pero muy pesado. Solo para GPUs de 16 GB+ (o 12 GB con descarga a CPU, lento).":
        "Excellent quality but very heavy. Only for 16 GB+ GPUs (or 12 GB with CPU offload, slow).",
    "API de Hugging Face (Inference Providers)": "Hugging Face API (Inference Providers)",
    "Según el modelo elegido": "Depends on the chosen model",
    "Genera en la nube. Requiere token gratuito de Hugging Face. Las cuentas gratuitas tienen un crédito mensual "
    "pequeño; al agotarlo las peticiones fallan o pueden tener coste. Consulta las condiciones actuales antes de "
    "usarla.":
        "Generates in the cloud. Requires a free Hugging Face token. Free accounts get a small monthly credit; "
        "once it runs out, requests fail or may cost money. Check the current terms before using it.",
    "Según el autor del archivo": "Set by the file's author",
    "Modelo local añadido por el usuario (archivo único).": "Local model added by the user (single file).",
    "No recomendado": "Not recommended",
    "Justo": "Borderline",
    "Justo (CPU, lento)": "Borderline (CPU, slow)",
    "🟢 Conectado (token configurado)": "🟢 Connected (token set)",
    "🟡 Requiere token de Hugging Face": "🟡 Requires a Hugging Face token",
    "🔴 Falta PyTorch/Diffusers": "🔴 PyTorch/Diffusers missing",
    "🟢 Instalado": "🟢 Installed",
    " (cargado en memoria)": " (loaded in memory)",
    "⚪ No instalado": "⚪ Not installed",
    "⚪ No instalado (descarga de ~{mb} MB)": "⚪ Not installed (~{mb} MB download)",
    "Descargando (~{gb} GB)…": "Downloading (~{gb} GB)…",
    "Este modelo no se descarga (es una API o un archivo local).":
        "This model is not downloaded (it is an API or a local file).",
    "⚠️ Debes marcar la casilla de autorización antes de descargar.":
        "⚠️ You must tick the authorisation box before downloading.",
    "⚠️ Marca la casilla de autorización antes de descargar.":
        "⚠️ Tick the authorisation box before downloading.",
    "{name} ya está instalado.": "{name} is already installed.",
    "❌ Espacio insuficiente: se necesitan ~{need} GB y hay {free} GB libres.":
        "❌ Not enough space: ~{need} GB needed and {free} GB free.",
    "❌ Falta huggingface_hub. Ejecuta install_windows.bat.": "❌ huggingface_hub is missing. Run install_windows.bat.",
    "✅ {name} instalado correctamente.": "✅ {name} installed successfully.",
    "❌ Error al descargar: {err}{hint}": "❌ Download error: {err}{hint}",
    "❌ Error al descargar: {err}": "❌ Download error: {err}",
    "❌ El archivo descargado no coincide con la huella oficial (SHA-256). Se ha descartado.":
        "❌ The downloaded file does not match the official fingerprint (SHA-256). It has been discarded.",
    "Solo se pueden eliminar modelos descargados.": "Only downloaded models can be deleted.",
    "🗑️ {name} eliminado.": "🗑️ {name} deleted.",
    "No estaba instalado.": "It was not installed.",
    "❌ Indica la ruta a un archivo .safetensors existente (no se aceptan .ckpt por seguridad).":
        "❌ Enter the path to an existing .safetensors file (.ckpt files are rejected for safety).",
    "✅ Modelo añadido: {name}": "✅ Model added: {name}",
    "{name}: {state}. Revísalo en «Modelos IA».": "{name}: {state}. Check it in “AI models”.",
    "Falta el token de Hugging Face. Añádelo en Configuración → APIs.":
        "The Hugging Face token is missing. Add it in Settings → APIs.",
    "Falta huggingface_hub. Ejecuta install_windows.bat.": "huggingface_hub is missing. Run install_windows.bat.",
    "La API de Hugging Face respondió con error: {err}": "The Hugging Face API returned an error: {err}",

    # ----------------------------------------------------- configuración
    "## ⚙️ Configuración": "## ⚙️ Settings",
    "General": "General",
    "Idioma": "Language",
    "El cambio se aplica al reiniciar MARS.AI.": "The change takes effect when you restart MARS.AI.",
    "Tema": "Theme",
    "Oscuro": "Dark",
    "Claro": "Light",
    "Sistema (como Windows)": "System (follow Windows)",
    "Se aplica al instante al guardar.": "Applied instantly when you save.",
    "Carpeta de imágenes": "Images folder",
    "Carpeta de modelos": "Models folder",
    "Estilo por defecto": "Default style",
    "Steps por defecto": "Default steps",
    "CFG por defecto": "Default CFG",
    "Resolución por defecto": "Default resolution",
    "Aspecto por defecto": "Default aspect ratio",
    "Memoria": "Memory",
    "Modo bajo consumo (descarga partes del modelo a la CPU; menos VRAM, algo más lento)":
        "Low-power mode (offloads parts of the model to the CPU; less VRAM, a bit slower)",
    "Liberar el modelo de memoria tras cada generación (mínima RAM, más lento)":
        "Unload the model from memory after each generation (minimum RAM, slower)",
    "Máximo de imágenes por lote": "Maximum images per batch",
    "APIs y conexiones": "APIs and connections",
    "**API de Hugging Face (opcional).** Crea un token gratuito en huggingface.co → Settings → Access Tokens. "
    "Las cuentas gratuitas incluyen un crédito mensual limitado; **las condiciones pueden cambiar y el uso extra "
    "puede tener coste**. Revisa https://huggingface.co/docs/inference-providers/pricing. MARS.AI nunca contrata "
    "nada por ti.\n\nEl token se guarda en el **Administrador de credenciales de Windows** (keyring) y nunca se "
    "escribe en registros ni en archivos de configuración.":
        "**Hugging Face API (optional).** Create a free token at huggingface.co → Settings → Access Tokens. "
        "Free accounts include a limited monthly credit; **the terms may change and extra usage may cost "
        "money**. See https://huggingface.co/docs/inference-providers/pricing. MARS.AI never signs up for "
        "anything on your behalf.\n\nThe token is stored in the **Windows Credential Manager** (keyring) and is "
        "never written to logs or settings files.",
    "Token actual: `{tok}` · Almacén seguro: {ok}": "Current token: `{tok}` · Secure storage: {ok}",
    "Nuevo token de Hugging Face (vacío = no cambiar)": "New Hugging Face token (empty = keep current)",
    "Borrar el token guardado": "Delete the saved token",
    "Modelo para la API": "Model for the API",
    "Ej.: black-forest-labs/FLUX.1-schnell, stabilityai/stable-diffusion-xl-base-1.0":
        "E.g.: black-forest-labs/FLUX.1-schnell, stabilityai/stable-diffusion-xl-base-1.0",
    "Entiendo que la API externa puede tener límites o costes":
        "I understand the external API may have limits or costs",
    "Sistema": "System",
    "Diagnóstico del equipo": "Computer diagnostics",
    "💾 Guardar configuración": "💾 Save settings",
    "imágenes": "images",
    "modelos": "models",
    "❌ Carpeta de {label} no válida: {err}": "❌ Invalid {label} folder: {err}",
    "✅ Configuración guardada.": "✅ Settings saved.",
    "🌐 Reinicia MARS.AI para aplicar el idioma.": "🌐 Restart MARS.AI to apply the language.",
    "Token borrado.": "Token deleted.",
    "⚠️ Token NO guardado: acepta primero el aviso de costes.":
        "⚠️ Token NOT saved: accept the cost warning first.",
    "Token guardado de forma segura.": "Token saved securely.",
    "❌ No se pudo guardar el token (almacén seguro no disponible).":
        "❌ The token could not be saved (secure storage unavailable).",
}
