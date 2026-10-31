"""Pruebas automáticas del cerebro con un Ollama simulado (no necesita internet)."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from onix_core.brain.cerebro import Cerebro, ErrorCerebro
from onix_core.brain.seguridad import hay_ram_suficiente
from onix_core.config.ajustes import cargar
from onix_core.personality.onix import mensaje_sistema


class OllamaFalso(BaseHTTPRequestHandler):
    ultima_peticion = None

    def log_message(self, *a):
        pass

    def _enviar(self, datos, codigo=200):
        cuerpo = json.dumps(datos).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        self._enviar({"models": [{"name": "qwen2.5:1.5b"}]})

    def do_POST(self):
        datos = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        OllamaFalso.ultima_peticion = datos
        n = sum(1 for m in datos["messages"] if m["role"] == "user")
        self._enviar({"message": {"role": "assistant", "content": f"Hola, soy ONIX (mensaje {n})."}})


class PruebasCerebro(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.servidor = HTTPServer(("127.0.0.1", 0), OllamaFalso)
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()

    def config(self, puerto=None):
        c = cargar()
        c["ollama_url"] = f"http://127.0.0.1:{puerto or self.servidor.server_port}"
        return c

    def test_configuracion_valida(self):
        c = cargar()
        self.assertIn(c["modelo"], ("qwen2.5:1.5b", "qwen2.5:0.5b"))
        self.assertLessEqual(c["max_tokens_respuesta"], 512)

    def test_personalidad_en_espanol(self):
        m = mensaje_sistema()
        self.assertEqual(m["role"], "system")
        self.assertIn("ONIX", m["content"])
        self.assertIn("español", m["content"])

    def test_detecta_ollama_y_modelo(self):
        c = Cerebro(self.config())
        self.assertTrue(c.ollama_disponible())
        self.assertTrue(c.modelo_instalado())

    def test_conversacion_con_memoria_de_sesion(self):
        c = Cerebro(self.config())
        self.assertEqual(c.responder("Hola"), "Hola, soy ONIX (mensaje 1).")
        self.assertEqual(c.responder("¿Qué tal?"), "Hola, soy ONIX (mensaje 2).")
        enviados = OllamaFalso.ultima_peticion["messages"]
        self.assertEqual(enviados[0]["role"], "system")
        self.assertEqual(len(c.historial), 4)

    def test_historial_limitado(self):
        c = Cerebro(self.config())
        for i in range(20):
            c.responder(f"mensaje {i}")
        self.assertLessEqual(len(c.historial), c.max_historial + 1)

    def test_mensaje_vacio(self):
        with self.assertRaises(ErrorCerebro):
            Cerebro(self.config()).responder("   ")

    def test_ollama_apagado_da_error_claro(self):
        c = Cerebro(self.config(puerto=1))
        self.assertFalse(c.ollama_disponible())
        with self.assertRaises(ErrorCerebro) as e:
            c.responder("Hola")
        self.assertIn("Ollama", str(e.exception))
        self.assertEqual(c.historial, [])

    def test_proteccion_ram(self):
        self.assertFalse(hay_ram_suficiente(1.8, libre=1.0)[0])
        self.assertTrue(hay_ram_suficiente(1.8, libre=2.5)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
