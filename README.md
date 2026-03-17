# llama-forge

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Upstream](https://img.shields.io/badge/upstream-llama.cpp-green.svg)](https://github.com/ggml-org/llama.cpp)

> **llama-forge** is a personal fork of [llama.cpp](https://github.com/ggml-org/llama.cpp) by [dev-boffin-io](https://github.com/dev-boffin-io), extended with a native Linux desktop GUI for local LLM management.

---

## What's different from upstream

| Feature | llama.cpp (upstream) | llama-forge |
|---|---|---|
| Core inference engine | ✅ | ✅ (synced) |
| CLI tools | ✅ | ✅ |
| Desktop GUI | ❌ | ✅ `llama_gui/` |
| CMake GUI build | ❌ | ✅ integrated |
| Desktop entry install | ❌ | ✅ auto via CMake |

---

## llama-forge GUI (`llama_gui/`)

A native Linux desktop application built with Python/Tkinter. Installed as part of the CMake build — no separate steps needed.

### Features

- **Chat tab** — interactive `llama-cli` sessions with full argument control (flags, sampling params, GPU layers, LoRA, grammar)
- **Quantize tab** — full `llama-quantize` interface with RAM-based recommendations, imatrix support, all quant types
- **Convert Tools** — HF → GGUF, LoRA → GGUF, GGML → GGUF conversion with all script options exposed
- **Auto project-root detection** — works from any location in the source tree or as a PyInstaller onefile binary
- **Config persistence** — last-used bin dir, model paths saved to `~/.llama_cpp_gui.json`
- **GGUF info viewer** — shows model name, architecture, quant type, context length, layers, file size on model select
- **Desktop entry** — `.desktop` file and icon installed to `~/.local/share/` automatically on build

### Structure

```
llama_gui/
├── app.py                  ← entry point
├── CMakeLists.txt          ← PyInstaller build + desktop entry install
├── gui/
│   ├── __init__.py         ← shared Tkinter helpers (scrollable frames, fonts, log widget)
│   ├── chat_tab.py         ← Chat (SAFE) tab
│   ├── quant_tab.py        ← Quantize tab
│   └── converter.py        ← Converter Manager window
├── core/
│   ├── llama_detect.py     ← project root detection, config persistence
│   ├── quant_logic.py      ← quant types, argument builder
│   └── converter_logic.py  ← convert script argument builder
└── utils/
    ├── terminal.py         ← terminal detection + cross-platform launch
    ├── subprocess_stream.py ← deadlock-free stdout/stderr streaming
    ├── gguf_info.py        ← GGUF metadata reader (gguf-py + raw fallback)
    └── ram_detect.py       ← system RAM detection + quant recommendation
```

### Running directly (development)

```bash
cd /opt/llama-forge/llama_gui
python3 app.py
```

---

## Build

Builds the full llama.cpp toolchain **and** the GUI in one step.

```bash
cd /opt/llama-forge
cmake -B build -S .
cmake --build build
```

The GUI binary `llama-gui` is placed at the project root (`/opt/llama-forge/llama-gui`) and a desktop entry is installed to `~/.local/share/applications/`.

To build **without** the GUI:

```bash
cmake -B build -S . -ULLAMA_STANDALONE
cmake --build build
```

### GUI-only rebuild

```bash
cd /opt/llama-forge/llama_gui
cmake -B build -S .
```

No `cmake --build` needed — the GUI build runs entirely at configure time via `execute_process`.

---

## Upstream sync

This fork tracks the upstream `master` branch. To sync:

```bash
git remote add upstream https://github.com/ggml-org/llama.cpp
git fetch upstream
git merge upstream/master
```

Upstream-only files (`AGENTS.md`, `CLAUDE.md`, CI configs) are kept as-is. The only fork-specific additions are `llama_gui/` and the `add_subdirectory(llama_gui)` block in the root `CMakeLists.txt`.

---

## Supported platforms

The GUI targets **Debian-based Linux** (desktop and ARM64/proot). The core llama.cpp engine supports all upstream platforms — see [upstream README](https://github.com/ggml-org/llama.cpp) for the full hardware/backend matrix.

---

## Dependencies

### Core (inherited from upstream)

See [upstream README § Dependencies](https://github.com/ggml-org/llama.cpp#dependencies).

### GUI

| Package | Purpose |
|---|---|
| `python3-tk` | Tkinter UI framework |
| `python3-venv` | PyInstaller build isolation |
| `PyInstaller` | onefile binary packaging (auto-installed at build time) |

Install on Debian/Ubuntu:

```bash
sudo apt install python3-tk python3-venv
```

---

## Acknowledgements

This fork builds directly on the work of the [llama.cpp](https://github.com/ggml-org/llama.cpp) project and the [ggml](https://github.com/ggml-org/ggml) library. All core inference, quantization, and conversion capabilities are from upstream — full contributor credits at [AUTHORS](AUTHORS).

---

## License

MIT — same as upstream. See [LICENSE](LICENSE).
