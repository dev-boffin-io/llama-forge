"""
converter_logic.py — convert_hf_to_gguf / convert_lora_to_gguf arg builder.
"""

from __future__ import annotations
import os

SCRIPTS: list[str] = [
    "convert_hf_to_gguf.py",
    "convert_llama_ggml_to_gguf.py",
    "convert_lora_to_gguf.py",
]

OUTTYPE_VALUES: list[str] = ["f32", "f16", "bf16", "q8_0", "tq1_0", "tq2_0", "auto"]

DEFAULT_OUTTYPE: dict[str, str] = {
    "convert_hf_to_gguf.py":          "f16",
    "convert_llama_ggml_to_gguf.py":  "f16",
    "convert_lora_to_gguf.py":        "q8_0",
}

HF_BOOL_FLAGS: list[str] = [
    "--vocab-only",
    "--lm-head",
    "--bigendian",
    "--use-temp-file",
    "--no-lazy",
    "--no-tensor-first-split",
    "--dry-run",
]

HF_TEXT_FLAGS: list[str] = [
    "--model-name",
    "--awq-path",
    "--metadata",
    "--split-max-tensors",
    "--split-max-size",
]


def build_convert_args(
    llama_dir:    str,
    script:       str,
    input_path:   str,
    outtype:      str,
    output_path:  str = "",
    base_model:   str = "",
    hf_bools:     dict[str, bool] | None = None,
    hf_texts:     dict[str, str]  | None = None,
    extra_args:   str = "",
) -> list[str]:
    """
    Build the python3 <script> command as a list of strings.
    Raises ValueError for missing required args.
    """
    script_path = os.path.join(llama_dir, script)
    if not os.path.isfile(script_path):
        raise ValueError(f"Script not found: {script_path}")
    if not input_path.strip():
        raise ValueError("Input model / path is required.")

    cmd = ["python3", script_path, input_path]
    cmd += ["--outtype", outtype]

    if output_path.strip():
        cmd += ["--outfile", output_path.strip()]

    if script == "convert_lora_to_gguf.py":
        if not base_model.strip():
            raise ValueError("Base model GGUF is required for LoRA conversion.")
        cmd += ["--base", base_model.strip()]

    if script == "convert_hf_to_gguf.py":
        for flag, enabled in (hf_bools or {}).items():
            if enabled:
                cmd.append(flag)
        for flag, val in (hf_texts or {}).items():
            if val.strip():
                cmd += [flag, val.strip()]

    if extra_args.strip():
        import shlex
        cmd += shlex.split(extra_args.strip())

    return cmd
