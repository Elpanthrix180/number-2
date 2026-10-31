"""Comprueba que hay RAM libre suficiente antes de cargar el modelo."""
import ctypes
import os


def ram_libre_gb():
    """Devuelve la RAM libre en GB, o None si no se puede medir."""
    try:
        if os.name == "nt":
            class MEM(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MEM()
            m.dwLength = ctypes.sizeof(MEM)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.ullAvailPhys / 1024 ** 3
        with open("/proc/meminfo") as f:
            for linea in f:
                if linea.startswith("MemAvailable"):
                    return int(linea.split()[1]) / 1024 ** 2
    except Exception:
        return None
    return None


def hay_ram_suficiente(minimo_gb, libre=None):
    libre = ram_libre_gb() if libre is None else libre
    if libre is None:
        return True, "No pude medir la RAM; continúo con cuidado."
    if libre < minimo_gb:
        return False, (f"Solo hay {libre:.1f} GB de RAM libre (se necesitan {minimo_gb} GB). "
                       "Cierra programas como el navegador e inténtalo de nuevo.")
    return True, f"RAM libre: {libre:.1f} GB. Correcto."
