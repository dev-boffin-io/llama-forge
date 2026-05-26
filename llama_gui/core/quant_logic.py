"""
quant_logic.py — llama-quantize argument builder and quant type list.

Updated for latest llama.cpp (2025) — includes SIMD-optimised q4_0 variants,
all IQ types, TQ types, and BF16.
"""

from __future__ import annotations

QUANT_TYPES: list[str] = [
    # K-quants (recommended for most use cases)
    "q2_K", "q2_K_S",
    "q3_K_S", "q3_K_M", "q3_K_L",
    "q4_0", "q4_1",
    "q4_K_S", "q4_K_M",
    "q5_0", "q5_1",
    "q5_K_S", "q5_K_M",
    "q6_K",
    "q8_0",
    # Float types
    "f16", "bf16", "f32",
    # IQ / importance-matrix quants
    "iq1_s", "iq1_m",
    "iq2_xxs", "iq2_xs", "iq2_s", "iq2_m",
    "iq3_xxs", "iq3_xs", "iq3_s", "iq3_m",
    "iq4_xs", "iq4_nl",
    # TQ 2-bit tiny
    "tq1_0", "tq2_0",
    # SIMD-optimised q4_0 variants (ARM NEON / AVX-512 / AVX-VNNI)
    "q4_0_4_4", "q4_0_4_8", "q4_0_8_8",
    # Copy (no quantization — useful for lossless round-trip)
    "copy",
]

TENSOR_TYPES: list[str] = ["default", "f32", "f16", "bf16", "q8_0"]

# KV cache types (--cache-type-k / --cache-type-v in llama-server/llama-cli)
KV_CACHE_TYPES: list[str] = ["f16", "f32", "bf16", "q8_0", "q4_0", "q4_1", "iq4_nl", "q5_0", "q5_1"]

DEFAULT_QUANT = "q4_K_M"


def build_quantize_args(
    exe:             str,
    src_gguf:        str,
    qtype:           str,
    out_tensor_type: str = "default",
    tok_emb_type:    str = "default",
    nthread:         str = "",
    imatrix:         str = "",
    include_weights: str = "",
    exclude_weights: str = "",
    override_kv:     str = "",
    allow_requantize: bool = False,
    leave_output:    bool = False,
    pure:            bool = False,
    keep_split:      bool = False,
) -> list[str]:
    """
    Build the llama-quantize command as a list of strings (no shell quoting).
    Output file is auto-derived from src_gguf.
    """
    args = [exe]

    if allow_requantize:
        args.append("--allow-requantize")
    if leave_output:
        args.append("--leave-output-tensor")
    if pure:
        args.append("--pure")
    if keep_split:
        args.append("--keep-split")
    if nthread.strip():
        args += ["--nthread", nthread.strip()]
    if imatrix.strip():
        args += ["--imatrix", imatrix.strip()]
    if include_weights.strip():
        args += ["--include-weights", include_weights.strip()]
    if exclude_weights.strip():
        args += ["--exclude-weights", exclude_weights.strip()]
    if out_tensor_type != "default":
        args += ["--output-tensor-type", out_tensor_type]
    if tok_emb_type != "default":
        args += ["--token-embedding-type", tok_emb_type]
    if override_kv.strip():
        args += ["--override-kv", override_kv.strip()]

    out_gguf = src_gguf.replace(".gguf", f"-{qtype}.gguf")
    args += [src_gguf, out_gguf, qtype]
    return args
