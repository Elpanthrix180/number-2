"""Chat de ONIX en la ventana de comandos."""
from onix_core.brain.cerebro import Cerebro, ErrorCerebro
from onix_core.brain.seguridad import hay_ram_suficiente
from onix_core.config.ajustes import cargar


def main():
    config = cargar()
    print("=" * 50)
    print("  ONIX CORE 1.0 - Tu asistente personal local")
    print("=" * 50)
    ok, mensaje = hay_ram_suficiente(config["ram_libre_minima_gb"])
    print(mensaje)
    if not ok:
        return 1
    cerebro = Cerebro(config)
    if not cerebro.ollama_disponible():
        print("Ollama no está abierto. Ábrelo desde el menú Inicio y vuelve a probar.")
        return 1
    if not cerebro.modelo_instalado():
        print(f"Falta el modelo. Abre PowerShell y escribe:  ollama pull {cerebro.modelo}")
        return 1
    print("Escribe tu mensaje. Comandos: 'salir' para terminar, 'olvidar' para empezar de cero.\n")
    while True:
        try:
            texto = input("Tú: ")
        except (EOFError, KeyboardInterrupt):
            break
        orden = texto.strip().lower()
        if orden in ("salir", "adios", "adiós"):
            break
        if orden == "olvidar":
            cerebro.olvidar()
            print("ONIX: He olvidado la conversación.\n")
            continue
        if not orden:
            continue
        print("ONIX está pensando...")
        try:
            print("ONIX:", cerebro.responder(texto), "\n")
        except ErrorCerebro as e:
            print("Aviso:", e, "\n")
    print("ONIX: ¡Hasta pronto!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
