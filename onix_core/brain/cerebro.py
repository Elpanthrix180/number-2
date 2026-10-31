"""Cerebro de ONIX: conecta Python con un modelo local de Ollama.

Solo usa la biblioteca estándar de Python (no hay que instalar nada extra).
"""
import json
import urllib.error
import urllib.request

from onix_core.personality.onix import mensaje_sistema


class ErrorCerebro(Exception):
    """Error explicado en español para el usuario."""


class Cerebro:
    def __init__(self, config):
        self.url = config["ollama_url"].rstrip("/")
        self.modelo = config["modelo"]
        self.tiempo_limite = config["tiempo_limite_segundos"]
        self.max_tokens = config["max_tokens_respuesta"]
        self.max_historial = config["max_mensajes_historial"]
        self.historial = []

    def _peticion(self, ruta, datos=None, tiempo=10):
        cuerpo = json.dumps(datos).encode("utf-8") if datos is not None else None
        req = urllib.request.Request(
            self.url + ruta, data=cuerpo,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=tiempo) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise ErrorCerebro(f"Ollama respondió con un error ({e.code}).") from e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            raise ErrorCerebro(
                "No puedo hablar con Ollama. ¿Está abierto? "
                "Búscalo en el menú Inicio y ábrelo."
            ) from e

    def ollama_disponible(self):
        try:
            self._peticion("/api/tags")
            return True
        except ErrorCerebro:
            return False

    def modelos_instalados(self):
        datos = self._peticion("/api/tags")
        return [m["name"] for m in datos.get("models", [])]

    def modelo_instalado(self):
        nombres = self.modelos_instalados()
        return any(n == self.modelo or n.split(":")[0] == self.modelo for n in nombres)

    def responder(self, texto):
        texto = (texto or "").strip()
        if not texto:
            raise ErrorCerebro("No has escrito nada.")
        self.historial.append({"role": "user", "content": texto})
        # Se recorta el historial para no llenar la memoria RAM.
        self.historial = self.historial[-self.max_historial:]
        datos = {
            "model": self.modelo,
            "messages": [mensaje_sistema()] + self.historial,
            "stream": False,
            "options": {"num_predict": self.max_tokens, "num_ctx": 2048},
        }
        try:
            r = self._peticion("/api/chat", datos, tiempo=self.tiempo_limite)
        except ErrorCerebro:
            self.historial.pop()
            raise
        respuesta = r.get("message", {}).get("content", "").strip()
        if not respuesta:
            self.historial.pop()
            raise ErrorCerebro("El modelo no devolvió ninguna respuesta.")
        self.historial.append({"role": "assistant", "content": respuesta})
        return respuesta

    def olvidar(self):
        self.historial = []
