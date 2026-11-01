# MARS.AI
**Transforma tu imaginación en imágenes.**

Estudio de generación de imágenes con IA para Windows 11. Es gratuito, funciona en local
y usa modelos de código abierto. Escribes una descripción y MARS.AI la convierte en imagen con
Stable Diffusion 1.5, SDXL o FLUX en tu propio equipo, o con la API de Hugging Face si quieres
(es opcional).

## Instalación en Windows 11

1. Instala **Python 3.11 o 3.12** desde <https://www.python.org/downloads/windows/>.
   Durante la instalación, marca *Add python.exe to PATH*.
2. Haz doble clic en **`install_windows.bat`**. Este paso:
   - analiza tu equipo (Python, RAM, GPU y disco libre),
   - te pide permiso antes de instalar nada,
   - instala PyTorch con CUDA si tienes una GPU NVIDIA, o la versión para CPU si no la tienes,
   - instala todo dentro de la carpeta `.venv`, sin tocar el resto del sistema,
   - **no descarga modelos de IA**.
3. Haz doble clic en **`run_windows.bat`**. MARS.AI se abrirá en el navegador, en `http://127.0.0.1:7860`.
   La app solo escucha en tu equipo y no se expone a Internet.
4. Ve a **Modelos IA**, elige *Stable Diffusion 1.5*, marca la casilla de autorización y pulsa
   **Descargar** (unos 2,6 GB). Otra opción: en **Configuración → APIs**, añade un token de Hugging Face.

Si solo quieres el diagnóstico del equipo, sin instalar nada: `python check_system.py`.

## Qué funciona y qué necesita

| Función | Estado | Requisito |
|---|---|---|
| Generar imágenes (txt2img) | ✅ | Un modelo local descargado **o** un token de Hugging Face |
| 20 estilos con ajustes y ejemplos | ✅ | — |
| Prompt, negativo, resolución (512/768/1024/personalizada), aspecto, lote, seed, steps, CFG | ✅ | — |
| Progreso en vivo, cancelar, tiempo de generación | ✅ | — |
| Galería: guardar, descargar, borrar, favoritos, buscar, filtrar por fecha, ver prompt y modelo | ✅ | — |
| Upscaler con IA (Real-ESRGAN x4plus, BSD-3) | ✅ | Descarga única de ~64 MB con tu autorización, verificada con SHA-256 |
| Restauración de caras con IA (GFPGAN v1.4, Apache 2.0, y detector YuNet, MIT) | ✅ | Descarga única de ~333 MB con tu autorización, verificada con SHA-256 |
| Upscaler, mejora de imagen y restauración (clásicos) | ✅ | Ninguno (Pillow) |
| Mejorar prompt | ✅ | Ninguno (diccionario local ES→EN y calificadores) |
| Image to Image, Variaciones, Inpainting, Outpainting | ✅ | Un modelo **local** instalado |
| Quitar fondo con IA (U²-Netp rápido o IS-Net de calidad, Apache 2.0) | ✅ | Descarga única de ~4,6 MB o ~179 MB con tu autorización, verificada con SHA-256 |
| Administrador de modelos: estado, compatibilidad, espacio, descarga autorizada, borrar, añadir `.safetensors` | ✅ | — |
| Modo de bajo consumo y liberar memoria | ✅ | — |

Ten en cuenta estas limitaciones:
- La restauración general de fotos es **clásica**. Para las caras usa *Herramientas → Caras IA* (GFPGAN)
  y para ampliar, *Herramientas → Upscaler IA* (Real-ESRGAN).
- GFPGAN reconstruye las caras: con una intensidad alta puede cambiar ligeramente los rasgos.
  Una intensidad de 0,5–0,7 conserva mejor la identidad.
- El idioma de la interfaz es solo el español y el tema es solo el oscuro.

## Modelos

| Modelo | Descarga | VRAM mínima | Licencia |
|---|---|---|---|
| Stable Diffusion 1.5 | ~2,6 GB | 4 GB (o CPU, lento) | CreativeML OpenRAIL-M |
| SDXL Turbo | ~7 GB | 8 GB | Stability AI (uso no comercial, revísala) |
| SDXL 1.0 | ~7 GB | 8 GB | OpenRAIL++-M |
| FLUX.1 [schnell] | ~34 GB | 16 GB | Apache 2.0 |
| API de Hugging Face | — | — | Según el modelo |

- Todos se descargan solo desde los repositorios oficiales de Hugging Face, y solo cuando tú lo autorizas.
- Puedes añadir tus propios modelos `.safetensors` (SD 1.5 o SDXL). Los archivos `.ckpt` se rechazan por
  seguridad, porque pueden ejecutar código.
- **Sobre la API de Hugging Face:** las cuentas gratuitas tienen un crédito mensual limitado y las
  condiciones pueden cambiar. Revisa <https://huggingface.co/docs/inference-providers/pricing>. Antes de
  guardar el token, MARS.AI te pide que aceptes el aviso de costes.

### Rendimiento orientativo
- **GPU NVIDIA de 6 GB o más:** SD 1.5 a 512×512 tarda unos segundos por imagen.
- **Solo CPU:** SD 1.5 a 512×512 con 20–25 pasos tarda varios minutos. Para acelerar, usa la API o baja los pasos.

## Seguridad y privacidad
- El token de la API se guarda en el **Administrador de credenciales de Windows** (con `keyring`).
  Nunca se escribe en `settings.json` y los registros lo ocultan.
- La telemetría de Gradio y de Hugging Face está desactivada.
- Las imágenes que importas se validan por formato y tamaño, y solo se borran archivos creados por MARS.AI.

## Dónde se guardan los datos
- Configuración, base de datos y registros: `%APPDATA%\MARS.AI\`
- Imágenes: `%APPDATA%\MARS.AI\outputs\AAAA-MM-DD\`. Puedes cambiar la carpeta en Configuración.
  Después de cambiarla, reinicia la app.
- Modelos: `%APPDATA%\MARS.AI\models\`. También se puede cambiar.

## Estructura del proyecto
```
MARS.AI/
  main.py                 punto de entrada
  check_system.py         diagnóstico del equipo
  install_windows.bat     instalador · run_windows.bat lanzador
  config/settings.py      ajustes (JSON) y claves seguras (keyring)
  core/                   diagnóstico, registros con ocultación de claves, contexto de la app
  generator/              estilos, motor (hilos, progreso, cancelación), potenciador de prompts
  models/                 catálogo, backends (Diffusers y API de HF), administrador
  tools/image_tools.py    upscaler, mejora, restauración, quitar fondo, utilidades de inpaint y outpaint
  tools/realesrgan.py     upscaler con IA (Real-ESRGAN)
  tools/face_restore.py   restauración de caras (GFPGAN + YuNet)
  tools/background_remover.py  quitafondos con IA (U²-Netp / IS-Net con OpenCV)
  tools/gfpgan_arch/      arquitectura de GFPGAN (Apache 2.0, con su licencia)
  gallery/library.py      biblioteca de imágenes
  database/db.py          SQLite
  interface/              interfaz Gradio y tema CSS
  tests/                  pruebas automáticas (pytest)
```

## Desarrollo
```bash
pip install -r requirements.txt pytest
python -m pytest -q tests
```
