"""
gguf_info.py — lightweight GGUF metadata reader.

Uses the gguf Python package that ships with llama.cpp (gguf-py/).
Falls back to raw struct parsing if the package is not importable.
"""

from __future__ import annotations
import os
import sys
import struct
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GGUFInfo:
    path: str
    model_name: str        = "unknown"
    architecture: str      = "unknown"
    quant_type: str        = "unknown"
    context_length: int    = 0
    embedding_length: int  = 0
    n_layers: int          = 0
    n_heads: int           = 0
    file_size_mb: float    = 0.0
    extra: dict[str, Any]  = field(default_factory=dict)
    error: str             = ""


# Keys we care about (GGUF standard names)
_KEYS = {
    "general.name":                  "model_name",
    "general.architecture":          "architecture",
    "general.file_type":             "quant_type",
    "llama.context_length":          "context_length",
    "llama.embedding_length":        "embedding_length",
    "llama.block_count":             "n_layers",
    "llama.attention.head_count":    "n_heads",
    # common arch variants
    "phi2.context_length":           "context_length",
    "phi2.embedding_length":         "embedding_length",
    "phi2.block_count":              "n_layers",
    "mistral.context_length":        "context_length",
    "mistral.embedding_length":      "embedding_length",
    "mistral.block_count":           "n_layers",
    "gemma.context_length":          "context_length",
    "gemma.block_count":             "n_layers",
}

_QUANT_NAMES = {
    0: "F32", 1: "F16", 2: "Q4_0", 3: "Q4_1",
    6: "Q5_0", 7: "Q5_1", 8: "Q8_0", 9: "Q8_1",
    10: "Q2_K", 11: "Q3_K_S", 12: "Q3_K_M", 13: "Q3_K_L",
    14: "Q4_K_S", 15: "Q4_K_M", 16: "Q5_K_S", 17: "Q5_K_M",
    18: "Q6_K", 19: "Q8_K", 20: "IQ2_XXS", 21: "IQ2_XS",
    24: "IQ3_XXS", 26: "IQ4_NL", 29: "IQ3_S", 30: "IQ3_M",
    31: "IQ2_S", 32: "IQ2_M", 36: "IQ4_XS", 37: "IQ1_S",
    38: "IQ4_NL", 39: "BF16",
}


def read_gguf_info(path: str, llama_root: str = "") -> GGUFInfo:
    """Return GGUFInfo for the given .gguf file."""
    info = GGUFInfo(path=path)
    try:
        info.file_size_mb = os.path.getsize(path) / (1024 * 1024)
    except OSError:
        pass

    # Try gguf-py package first
    if _try_gguf_py(path, info, llama_root):
        return info

    # Fallback: raw binary parse
    _parse_raw(path, info)
    return info


def _try_gguf_py(path: str, info: GGUFInfo, llama_root: str) -> bool:
    """Attempt to read via the gguf Python package. Returns True on success."""
    # Inject llama_root/gguf-py into sys.path if needed
    candidates = []
    if llama_root:
        candidates.append(os.path.join(llama_root, "gguf-py"))
    for c in candidates:
        if c and os.path.isdir(c) and c not in sys.path:
            sys.path.insert(0, c)

    try:
        import gguf  # type: ignore
        reader = gguf.GGUFReader(path, "r")

        for field_obj in reader.fields.values():
            key = field_obj.name
            mapped = _KEYS.get(key)
            # Read first part value
            try:
                val = field_obj.parts[field_obj.data[0]][0]
                if isinstance(val, bytes):
                    val = val.decode("utf-8", errors="replace")
            except Exception:
                continue

            if mapped:
                setattr(info, mapped, val)
            else:
                info.extra[key] = val

        # Resolve quant type number → name
        if isinstance(info.quant_type, int):
            info.quant_type = _QUANT_NAMES.get(info.quant_type, str(info.quant_type))

        return True
    except Exception:
        return False


# ── Minimal raw GGUF parser (fallback) ──────────────────────────────────────
# GGUF v1/v2/v3 spec: magic(4) version(4) n_tensors(8) n_kv(8) then KV pairs

_GGUF_MAGIC = b"GGUF"

_VALUE_TYPES = {
    0: ("B",  1),   # uint8
    1: ("b",  1),   # int8
    2: ("H",  2),   # uint16
    3: ("h",  2),   # int16
    4: ("I",  4),   # uint32
    5: ("i",  4),   # int32
    6: ("f",  4),   # float32
    7: ("?",  1),   # bool
    # 8 = string (special)
    # 9 = array  (special)
    10: ("Q", 8),   # uint64
    11: ("q", 8),   # int64
    12: ("d", 8),   # float64
}


def _parse_raw(path: str, info: GGUFInfo) -> None:
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
            if magic != _GGUF_MAGIC:
                info.error = "Not a GGUF file"
                return

            version = struct.unpack("<I", f.read(4))[0]
            if version not in (1, 2, 3):
                info.error = f"Unsupported GGUF version {version}"
                return

            n_tensors = struct.unpack("<Q", f.read(8))[0]
            n_kv      = struct.unpack("<Q", f.read(8))[0]

            kv: dict[str, Any] = {}
            for _ in range(n_kv):
                key = _read_string(f)
                vtype = struct.unpack("<I", f.read(4))[0]
                val = _read_value(f, vtype)
                if key and val is not None:
                    kv[key] = val

            for src_key, attr in _KEYS.items():
                if src_key in kv:
                    setattr(info, attr, kv[src_key])

            if isinstance(info.quant_type, int):
                info.quant_type = _QUANT_NAMES.get(info.quant_type, str(info.quant_type))

    except Exception as e:
        info.error = str(e)


def _read_string(f) -> str:
    try:
        length = struct.unpack("<Q", f.read(8))[0]
        return f.read(length).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _read_value(f, vtype: int):
    if vtype in _VALUE_TYPES:
        fmt, size = _VALUE_TYPES[vtype]
        raw = f.read(size)
        if len(raw) < size:
            return None
        return struct.unpack(f"<{fmt}", raw)[0]
    elif vtype == 8:   # string
        return _read_string(f)
    elif vtype == 9:   # array — skip
        elem_type = struct.unpack("<I", f.read(4))[0]
        count     = struct.unpack("<Q", f.read(8))[0]
        for _ in range(count):
            _read_value(f, elem_type)
        return None
    else:
        return None
