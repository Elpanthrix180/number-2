"""Ejecuta el diagnóstico del equipo sin necesidad de instalar dependencias.

Uso:  python check_system.py
"""
from core.system_info import collect, format_report

if __name__ == "__main__":
    print("=== MARS.AI — Diagnóstico del sistema ===")
    print(format_report(collect()))
