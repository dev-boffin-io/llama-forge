# llama-forge

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Upstream](https://img.shields.io/badge/upstream-llama.cpp-green.svg)](https://github.com/ggml-org/llama.cpp)
[![Platform](https://img.shields.io/badge/platform-Linux-informational.svg)]()
[![GUI](https://img.shields.io/badge/GUI-Tkinter%2FPython-blue.svg)]()

> **llama-forge** is a personal fork of [llama.cpp](https://github.com/ggml-org/llama.cpp) by [dev-boffin-io](https://github.com/dev-boffin-io), extended with a native Linux desktop GUI for local LLM management — chat, quantization, and model conversion, all from one application.

---

## Table of Contents

- [What's different from upstream](#whats-different-from-upstream)
- [GUI overview](#llama-forge-gui-llama_gui)
  - [Features](#features)
  - [Chat tab](#chat-tab)
  - [Quantize tab](#quantize-tab)
  - [Convert Tools](#convert-tools)
  - [Project-root detection](#project-root-detection)
  - [Structure](#structure)
  - [Running in development](#running-directly-development)
- [Build](#build)
  - [Full build](#full-build)
  - [GUI-only build](#gui-only-rebuild)
  - [Build output](#build-output)
- [Quick start](#quick-start)
- [Upstream sync](#upstream-sync)
- [Supported platforms](#supported-platforms)
- [Dependencies](#dependencies)
- [Acknowledgements](#acknowledgements)
- [License](#license)

---

## What's different from upstream

llama-forge keeps the full llama.cpp engine in sync with upstream and adds a native Linux desktop GUI on top. Nothing from the core is removed or modified.

| Feature | llama.cpp (upstream) | llama-forge |
|---|---|---|
| Core inference engine | ✅ | ✅ (synced) |
| CLI tools (`llama-cli`, `llama-server`, etc.) | ✅ | ✅ |
| Python conversion scripts | ✅ | ✅ |
| Desktop GUI application | ❌ | ✅ `llama_gui/` |
| CMake-integrated GUI build | ❌ | ✅ |
| PyInstaller onefile binary | ❌ | ✅ |
| Desktop entry auto-install | ❌ | ✅ |
| RAM-based quant recommendation | ❌ | ✅ |
| GGUF metadata viewer | ❌ | ✅ |

---

## llama-forge GUI (`llama_gui/`)

A native Linux desktop application built with Python and Tkinter. It wraps the llama.cpp CLI tools and Python conversion scripts behind a graphical interface — no terminal knowledge required for day-to-day use.

The GUI is built and installed as part of the standard CMake build. No extra steps, no separate pip install, no venv management needed by the user.

### Features

#### Chat tab

An interactive chat interface that launches `llama-cli` in a new terminal window with full argument control:

- **Core arguments** — context size, thread count, chat template, batch size, GPU layers, prediction limit
- **Boolean flags** — `--interactive-first`, `--conversation`, `--flash-attn`, `--mlock`, `--no-mmap`, `--verbose`, `--special`, and more — each as a checkbox, unchecked means the flag is not passed
- **Optional sampling arguments** — temperature, top-k, top-p, min-p, repeat penalty, seed, rope scaling, system prompt, grammar file, LoRA adapter, override-kv — empty field means the argument is skipped entirely
- **Extra arguments** — free-text field for any argument not covered above
- **Supports flag detection** — checks whether the current `llama-cli` build supports a given flag before passing it, warns and skips unsupported flags rather than failing

#### Quantize tab

A full interface for `llama-quantize` with every option exposed:

- **Quant type dropdown** — all types including K-quants (`q2_K` through `q6_K`), IQ importance-matrix quants (`iq1_s`, `iq2_xxs`, `iq3_s`, `iq4_xs`, etc.), float types (`f16`, `bf16`, `f32`), tiny quants (`tq1_0`, `tq2_0`), and `copy`
- **Output tensor type / token-embedding type** — separate dropdowns (`default`, `f32`, `f16`, `bf16`, `q8_0`)
- **Options** — `--nthread`, `--imatrix` (with file browser), `--include-weights`, `--exclude-weights`, `--override-kv`
- **Flags** — `--allow-requantize`, `--leave-output-tensor`, `--pure`, `--keep-split` as checkboxes
- **RAM recommendation** — detects system RAM at startup and recommends the appropriate quant type with a note explaining the reasoning (e.g. `16 GB → q5_K_S: good quality, moderate size`)
- **GGUF info viewer** — selecting a source GGUF file automatically reads and displays its metadata: model name, architecture, current quant type, context length, layer count, embedding dimension, file size

#### Convert Tools

A separate window (`Convert Tools` button) for the Python conversion scripts:

- **Script selector** — `convert_hf_to_gguf.py`, `convert_llama_ggml_to_gguf.py`, `convert_lora_to_gguf.py`
- **Output type dropdown** — `f32`, `f16`, `bf16`, `q8_0`, `tq1_0`, `tq2_0`, `auto` — auto-set per script
- **HF flags panel** (shown only for `convert_hf_to_gguf.py`) — `--vocab-only`, `--lm-head`, `--bigendian`, `--use-temp-file`, `--no-lazy`, `--no-tensor-first-split`, `--dry-run`
- **HF options panel** (shown only for `convert_hf_to_gguf.py`) — `--model-name`, `--awq-path`, `--metadata`, `--split-max-tensors`, `--split-max-size`
- **LoRA base model** (shown only for `convert_lora_to_gguf.py`) — required base GGUF with file browser
- **Dry Run mode** — shows the full command without executing it
- **In-app output log** — stdout and stderr streamed in real time directly into the window, no terminal needed

#### Project-root detection

The GUI locates the llama-forge project root automatically at startup regardless of where it is launched from:

- When run as a Python script, walks up from the script directory looking for `CMakeLists.txt` + `convert_hf_to_gguf.py`
- When run as a PyInstaller onefile binary, resolves from `sys.executable`
- Falls back to CWD, then `$HOME` if the above fails
- Automatically sets `build/bin` as the binary directory if it exists
- Remembers last-used binary directory, chat model, and quantization GGUF across sessions (`~/.llama_cpp_gui.json`)

### Structure

```
llama_gui/
├── app.py                   ← entry point, App (tk.Tk), config load/save, tab wiring
├── CMakeLists.txt           ← pure-CMake build: venv, PyInstaller, binary install, desktop entry
├── llama_gui.png            ← application icon
│
├── gui/
│   ├── __init__.py          ← shared helpers: scale_font(), make_scrollable(), log_widget(), append_log()
│   ├── chat_tab.py          ← Chat (SAFE) tab — llama-cli launcher with full arg panels
│   ├── quant_tab.py         ← Quantize tab — llama-quantize GUI with RAM recommendation
│   └── converter.py         ← Converter Manager Toplevel window
│
├── core/
│   ├── llama_detect.py      ← project root detection, BIN_DIR_DEFAULT, config persistence
│   ├── quant_logic.py       ← QUANT_TYPES list, TENSOR_TYPES, build_quantize_args()
│   └── converter_logic.py   ← SCRIPTS, OUTTYPE_VALUES, HF flag lists, build_convert_args()
│
└── utils/
    ├── terminal.py          ← detect_terminal(), resolves x-terminal-emulator symlink, launch_in_terminal(), shell_quote_list()
    ├── subprocess_stream.py ← stream_process() — deadlock-free dual-pipe streaming via threads
    ├── gguf_info.py         ← read_gguf_info() — gguf-py reader with raw binary fallback parser
    └── ram_detect.py        ← get_total_ram_gb(), recommend_quant(), all_recommendations()
```

### Running directly (development)

```bash
cd /path/to/llama-forge/llama_gui
python3 app.py
```

Dependencies for development (already available if built via CMake):

```bash
sudo apt install python3-tk
```

---

## Build

### Full build

Builds the complete llama.cpp toolchain, CLI tools, and the GUI in one step:

```bash
cd /path/to/llama-forge
cmake -B build -S .
cmake --build build
```

### Build without GUI

```bash
cmake -B build -S . -ULLAMA_STANDALONE
cmake --build build
```

### GUI-only rebuild

The GUI build is driven entirely at CMake configure time via `execute_process` — no `cmake --build` needed:

```bash
cd /path/to/llama-forge/llama_gui
cmake -B build_gui -S .
```

This will:
1. Check for `python3-tk` and `python3-venv`
2. Create a fresh `.venv` and install PyInstaller
3. Build the `llama-gui` onefile binary
4. Place the binary at the project root (`llama-forge/llama-gui`)
5. Remove old desktop entry and icon if present
6. Install fresh `.desktop` file to `~/.local/share/applications/`
7. Install icon to `~/.local/share/icons/`
8. Clean up venv and build artefacts

### Build output

| Output | Location |
|---|---|
| GUI binary | `<project-root>/llama-gui` |
| Desktop entry | `~/.local/share/applications/llama-gui.desktop` |
| Icon | `~/.local/share/icons/llama-gui.png` |
| llama-cli, llama-server, etc. | `<project-root>/build/bin/` |

---

## Quick start

After a full build:

```bash
# Launch the GUI from desktop menu, or:
/path/to/llama-forge/llama-gui

# Or use the CLI tools directly:
./build/bin/llama-cli -m models/my-model.gguf

# Or start the OpenAI-compatible server:
./build/bin/llama-server -m models/my-model.gguf --port 8080
```

GGUF models can be downloaded from [Hugging Face](https://huggingface.co/models?library=gguf&sort=trending) or converted from HuggingFace checkpoints using the Convert Tools window in the GUI.

---

## Upstream sync

This fork tracks the upstream `master` branch. The only fork-specific files are:

- `llama_gui/` — the entire GUI directory
- The `add_subdirectory(llama_gui)` block in the root `CMakeLists.txt`
- `AUTHORS`, `CONTRIBUTING.md`, `SECURITY.md`, `AGENTS.md`, `LICENSE`, `pyproject.toml` — rewritten for fork context

Everything else (`CLAUDE.md`, CI configs, core source) is kept as-is from upstream.

To sync with upstream:

```bash
git remote add upstream https://github.com/ggml-org/llama.cpp
git fetch upstream
git merge upstream/master
# Resolve conflicts in CMakeLists.txt (keep the add_subdirectory block)
# All other conflicts: prefer upstream
```

---

## Supported platforms

| Component | Platform |
|---|---|
| GUI (`llama_gui/`) | Debian-based Linux (desktop + ARM64/proot) |
| Core inference engine | Linux, macOS, Windows, Android |
| CUDA backend | NVIDIA GPUs |
| HIP backend | AMD GPUs |
| Metal backend | Apple Silicon |
| Vulkan backend | Cross-platform GPU |

For the full hardware and backend matrix see the [upstream README](https://github.com/ggml-org/llama.cpp).

---

## Dependencies

### Core (inherited from upstream)

The core engine has no required dependencies beyond a C/C++ compiler and CMake. Optional backends (CUDA, HIP, Vulkan, Metal) require their respective SDKs. See [upstream build docs](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md).

### GUI

| Package | How to get | Purpose |
|---|---|---|
| `python3-tk` | `sudo apt install python3-tk` | Tkinter UI framework |
| `python3-venv` | `sudo apt install python3-venv` | Build isolation for PyInstaller |
| `PyInstaller` | Auto-installed at build time | Packages GUI as onefile binary |

```bash
# Install GUI build dependencies on Debian/Ubuntu
sudo apt install python3-tk python3-venv
```

---

## Acknowledgements

llama-forge is built on the work of the [llama.cpp](https://github.com/ggml-org/llama.cpp) project and the [ggml](https://github.com/ggml-org/ggml) tensor library. All core inference, quantization, and conversion capabilities are entirely from upstream. Full contributor credits are at [AUTHORS](AUTHORS).

---

## License

MIT — same as upstream. See [LICENSE](LICENSE).
