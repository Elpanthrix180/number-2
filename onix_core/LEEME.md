# ONIX CORE 1.0 — Fase 1: el cerebro

ONIX es tu asistente personal. Funciona **en tu ordenador**, gratis y sin internet
(solo necesitas internet una vez, para descargar los programas y el modelo).

## Qué hay en cada carpeta

| Carpeta | Para qué sirve | Estado |
|---|---|---|
| `brain` | La inteligencia: habla con el modelo de Ollama | ✅ Funciona |
| `personality` | Cómo es y cómo habla ONIX | ✅ Funciona |
| `interface` | La ventana donde escribes | ✅ Funciona (consola) |
| `config` | Ajustes (`config.json`) | ✅ Funciona |
| `tests` | Pruebas automáticas | ✅ Funciona |
| `memory` | Memoria permanente | ⏳ Fase futura |
| `voice` | Voz | ⏳ Fase futura |
| `tools` | Herramientas | ⏳ Fase futura |

## Instalación (una sola vez)

1. **Python**: descarga Python 3.12 desde https://www.python.org/downloads/ .
   Al instalar, marca la casilla **"Add python.exe to PATH"**.
2. **Ollama**: descárgalo desde https://ollama.com/download/windows e instálalo.
3. **El modelo**: abre PowerShell y escribe:

   ```
   ollama pull qwen2.5:1.5b
   ```

   Si tu ordenador va lento, usa el modelo pequeño: `ollama pull qwen2.5:0.5b`
   y cambia `"modelo"` en `config/config.json` a `"qwen2.5:0.5b"`.

No hace falta instalar nada más: ONIX solo usa lo que trae Python.

## Uso

- **Probar que todo está bien**: doble clic en `probar_onix.bat`. Debe terminar con `OK`.
- **Conversar**: cierra el navegador y otros programas pesados, y haz doble clic en `iniciar_onix.bat`.
  - Escribe `olvidar` para empezar una conversación nueva.
  - Escribe `salir` para terminar.

## Protecciones para tu ordenador de 4 GB

- Antes de empezar, ONIX mide la RAM libre. Si hay menos de 1,8 GB, **no arranca** y te avisa.
- Las respuestas son cortas (máximo 300 fragmentos de texto) y solo recuerda los últimos 10 mensajes.
- Si el modelo tarda más de 2 minutos, se cancela la respuesta.
- ONIX no borra ni modifica tus archivos.

## Problemas frecuentes

| Mensaje | Solución |
|---|---|
| "No puedo hablar con Ollama" | Abre Ollama desde el menú Inicio. |
| "Falta el modelo" | Ejecuta `ollama pull qwen2.5:1.5b` en PowerShell. |
| "Solo hay X GB de RAM libre" | Cierra programas o usa el modelo `qwen2.5:0.5b`. |
| "python no se reconoce" | Reinstala Python marcando "Add to PATH". |

## Qué se ha probado (y qué no)

- ✅ 8 pruebas automáticas superadas con un Ollama **simulado**: conexión, personalidad,
  conversación, límite de historial, errores claros y protección de RAM.
- ❌ **Todavía no se ha probado con un modelo real en tu ordenador.** Ese es el siguiente paso.
