"""Diagnóstico del equipo: Python, RAM, GPU y disco.

Solo usa la biblioteca estándar (y psutil/torch si están instalados), para que
pueda ejecutarse antes de instalar nada.
"""
from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from core.i18n import t


@dataclass
class GPUInfo:
    name: str
    vram_gb: float
    backend: str  # "cuda", "directml", "mps" o "desconocido"


@dataclass
class SystemReport:
    os_name: str
    python_version: str
    python_ok: bool
    ram_total_gb: float
    ram_available_gb: float
    disk_free_gb: float
    cpu_count: int
    gpus: list[GPUInfo] = field(default_factory=list)
    torch_installed: bool = False
    torch_cuda: bool = False
    recommended_profile: str = "cpu-bajo-consumo"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _ram_gb() -> tuple[float, float]:
    try:
        import psutil  # type: ignore

        vm = psutil.virtual_memory()
        return vm.total / 1024**3, vm.available / 1024**3
    except ImportError:
        pass
    if os.name == "nt":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        st = MEMORYSTATUSEX()
        st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))  # type: ignore[attr-defined]
        return st.ullTotalPhys / 1024**3, st.ullAvailPhys / 1024**3
    try:
        info = {}
        with open("/proc/meminfo") as fh:
            for line in fh:
                k, v = line.split(":", 1)
                info[k] = int(v.split()[0]) / 1024**2
        return info.get("MemTotal", 0.0), info.get("MemAvailable", 0.0)
    except OSError:
        return 0.0, 0.0


def _nvidia_gpus() -> list[GPUInfo]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return []
    try:
        out = subprocess.run(
            [exe, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    gpus = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 2:
            try:
                gpus.append(GPUInfo(parts[0], round(float(parts[1]) / 1024, 1), "cuda"))
            except ValueError:
                pass
    return gpus


def _windows_gpus() -> list[GPUInfo]:
    """GPUs no NVIDIA en Windows (solo informativo: diffusers no las usa sin DirectML)."""
    if os.name != "nt":
        return []
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name }"],
            capture_output=True, text=True, timeout=15,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [GPUInfo(n.strip(), 0.0, "desconocido") for n in out.splitlines()
            if n.strip() and "nvidia" not in n.lower()]


def collect(path_for_disk: str = ".") -> SystemReport:
    total, avail = _ram_gb()
    disk_free = shutil.disk_usage(os.path.abspath(path_for_disk)).free / 1024**3
    gpus = _nvidia_gpus() + _windows_gpus()
    rep = SystemReport(
        os_name=f"{platform.system()} {platform.release()} ({platform.version()})",
        python_version=platform.python_version(),
        python_ok=(3, 10) <= sys.version_info[:2] <= (3, 13),
        ram_total_gb=round(total, 1),
        ram_available_gb=round(avail, 1),
        disk_free_gb=round(disk_free, 1),
        cpu_count=os.cpu_count() or 1,
        gpus=gpus,
    )
    try:
        import torch  # type: ignore

        rep.torch_installed = True
        rep.torch_cuda = bool(torch.cuda.is_available())
    except Exception:
        pass

    vram = max((g.vram_gb for g in gpus if g.backend == "cuda"), default=0.0)
    if vram >= 12:
        rep.recommended_profile = "gpu-alta"
    elif vram >= 6:
        rep.recommended_profile = "gpu-media"
    elif vram >= 4:
        rep.recommended_profile = "gpu-baja"
    else:
        rep.recommended_profile = "cpu-bajo-consumo"

    if not rep.python_ok:
        rep.notes.append(t("Python {v}: se recomienda Python 3.10–3.13 (PyTorch puede no tener versión para otras).",
                           v=rep.python_version))
    if rep.ram_total_gb and rep.ram_total_gb < 8:
        rep.notes.append(t("Menos de 8 GB de RAM: usa SD 1.5 a 512×512 en modo bajo consumo, o una API externa."))
    if vram == 0:
        rep.notes.append(t("Sin GPU NVIDIA: la generación local funcionará en CPU (lenta: minutos por imagen)."))
    if rep.disk_free_gb < 10:
        rep.notes.append(t("Menos de 10 GB libres: no habrá espacio para la mayoría de modelos locales."))
    return rep


def format_report(rep: SystemReport) -> str:
    rows = [
        (t("Sistema operativo"), rep.os_name),
        ("Python", f"{rep.python_version} {'(OK)' if rep.python_ok else t('(no recomendado)')}"),
        (t("CPU (núcleos)"), rep.cpu_count),
        (t("RAM total"), t("{total} GB (disponible {avail} GB)", total=rep.ram_total_gb, avail=rep.ram_available_gb)),
        (t("Disco libre"), f"{rep.disk_free_gb} GB"),
    ]
    if rep.gpus:
        for g in rep.gpus:
            vram = f"{g.vram_gb} GB VRAM" if g.vram_gb else t("VRAM desconocida")
            rows.append(("GPU", f"{g.name} — {vram} [{g.backend}]"))
    else:
        rows.append(("GPU", t("no se detectó GPU NVIDIA")))
    rows.append(("PyTorch", (t("instalado") if rep.torch_installed else t("no instalado"))
                 + (t(" (CUDA activo)") if rep.torch_cuda else "")))
    rows.append((t("Perfil recomendado"), rep.recommended_profile))
    width = max(len(k) for k, _ in rows)
    lines = [f"{k.ljust(width)} : {v}" for k, v in rows]
    for n in rep.notes:
        lines.append(f"  • {n}")
    return "\n".join(lines)
