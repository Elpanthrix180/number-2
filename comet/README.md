# COMET

Estudio creativo con IA de temática espacial (cometas y estrellas), inspirado en Higgsfield: generación de imágenes, video (con presets de movimiento de cámara) y edición de imágenes con IA.

Uso: abre `index.html` en el navegador, pega tu clave API de [fal.ai](https://fal.ai) (se guarda solo en tu navegador), escribe un prompt y pulsa **Generar**.

Pestañas: **Imagen** (FLUX, Recraft), **Video** (Kling, MiniMax, Seedance), **Editar** (FLUX img2img / Kontext), **Avatar** (foto + voz → video hablando, OmniHuman) y **Lipsync** (video + voz → labios sincronizados, Sync / Kling). En Avatar y Lipsync puedes subir un audio o escribir el texto en el prompt y se genera la voz con MiniMax TTS.


Las imágenes, videos y audios que subes se envían primero al almacenamiento de fal.ai (CDN) y al modelo solo se le pasa la URL, así que funcionan archivos grandes.


El historial de creaciones se guarda en tu navegador (localStorage): sobrevive a recargas, pero se guardan los enlaces de fal.ai, no los archivos. Descarga lo que quieras conservar para siempre.


Botón ☀/☾ en la cabecera para cambiar entre tema claro y oscuro; la elección se recuerda en el navegador (por defecto sigue el tema del sistema).


Encima de la galería puedes filtrar el historial por tipo (Imagen, Video, Editar, Avatar, Lipsync) y buscar por texto del prompt.


El botón **✦ Mejorar** junto al prompt reescribe tu idea con más detalle usando un LLM de fal.ai (any-llm), adaptado a la pestaña en la que estás.
