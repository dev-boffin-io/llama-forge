"""
ram_detect.py — system RAM detection and quant type recommendation.
"""

from __future__ import annotations
import os


def get_total_ram_gb() -> float:
    """Return total system RAM in GB. Falls back to 0.0 on failure."""
    # Linux: /proc/meminfo
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return round(kb / (1024 * 1024), 1)
    except OSError:
        pass

    # macOS / BSD: sysctl
    try:
        import subprocess
        out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)
        return round(int(out.strip()) / (1024 ** 3), 1)
    except Exception:
        pass

    # Windows: wmic
    try:
        import subprocess
        out = subprocess.check_output(
            ["wmic", "ComputerSystem", "get", "TotalPhysicalMemory"],
            text=True
        )
        for line in out.splitlines():
            line = line.strip()
            if line.isdigit():
                return round(int(line) / (1024 ** 3), 1)
    except Exception:
        pass

    return 0.0


# (min_ram_gb, quant_type, description)
_RECOMMENDATIONS: list[tuple[float, str, str]] = [
    (64.0, "q8_0",   "64 GB+ → q8_0: near-lossless, maximum quality"),
    (32.0, "q6_K",   "32 GB+ → q6_K: excellent quality, small loss"),
    (24.0, "q5_K_M", "24 GB+ → q5_K_M: great quality/size balance"),
    (16.0, "q5_K_S", "16 GB+ → q5_K_S: good quality, moderate size"),
    (12.0, "q4_K_M", "12 GB+ → q4_K_M: recommended default"),
    ( 8.0, "q4_K_S", " 8 GB+ → q4_K_S: balanced for limited RAM"),
    ( 6.0, "q3_K_M", " 6 GB+ → q3_K_M: smaller, some quality loss"),
    ( 4.0, "q3_K_S", " 4 GB+ → q3_K_S: tight RAM, noticeable loss"),
    ( 0.0, "q2_K",   "< 4 GB  → q2_K: last resort, significant loss"),
]


def recommend_quant(ram_gb: float | None = None) -> tuple[str, str]:
    """
    Return (quant_type, description) for the given (or auto-detected) RAM.
    """
    if ram_gb is None:
        ram_gb = get_total_ram_gb()

    for min_gb, qtype, desc in _RECOMMENDATIONS:
        if ram_gb >= min_gb:
            return qtype, desc

    return "q2_K", "Unknown RAM → q2_K (safe fallback)"


def all_recommendations() -> list[tuple[str, str, str]]:
    """Return all (min_ram_label, quant, description) rows for display."""
    return [(f"{r[0]:.0f} GB", r[1], r[2]) for r in _RECOMMENDATIONS]
