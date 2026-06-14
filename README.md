<div align="center">

# 🔨 llama-forge

### A GUI Frontend for llama.cpp

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Android%20ARM64%20%7C%20Windows-lightgrey)](https://github.com/dev-boffin-io/llama-forge)
[![Built With](https://img.shields.io/badge/Built%20With-Python%20%7C%20C%2B%2B-informational)](https://github.com/dev-boffin-io/llama-forge)
[![Upstream](https://img.shields.io/badge/Upstream-ggml--org%2Fllama.cpp-orange)](https://github.com/ggml-org/llama.cpp)
[![Pinned](https://img.shields.io/badge/Pinned-b9297-yellow)](https://github.com/ggml-org/llama.cpp/releases/tag/b9297)
[![Maintained](https://img.shields.io/badge/Maintained-Yes-brightgreen)](https://github.com/dev-boffin-io/llama-forge)

**llama-forge** is a fork of [llama.cpp](https://github.com/ggml-org/llama.cpp) extended with a native **PyQt6** GUI frontend for running, quantizing, converting, and serving large language models locally — with full support for Debian/Linux, Termux/Android ARM64, and Windows.

</div>

---

> ⚠️ **Version Info:** Pinned to llama.cpp release [`b9297`](https://github.com/ggml-org/llama.cpp/releases/tag/b9297) (24 May 2026). Stable & tested. Daily master sync is disabled.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Debian / Linux](#debian--linux)
  - [Termux / Android ARM64](#termux--android-arm64)
  - [Windows](#windows)
- [Building from Source](#building-from-source)
- [Usage](#usage)
  - [Chat Tab](#chat-tab)
  - [Quantize Tab](#quantize-tab)
  - [Server Tab](#server-tab)
  - [Convert Tools](#convert-tools)
- [Project Structure](#project-structure)
- [Upstream Sync](#upstream-sync)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

llama-forge combines the full power of the llama.cpp inference engine with a user-friendly graphical interface built on **PyQt6**. No command-line knowledge required to run, quantize, serve, or convert GGUF models. Designed for developers and power users who want a local, private, and efficient LLM workflow.

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 💬 **Chat** | Interactive chat with local GGUF models via `llama-cli` |
| ⚖️ **Quantize** | Quantize models to Q4_K_M, Q5_K_M, Q8_0, SIMD-optimised variants, and more |
| 🌐 **Server** | Launch and manage `llama-server` instances with a full argument GUI; powered by Qt-native `QProcess` |
| 🔄 **Convert** | Convert HuggingFace models to GGUF format via a `QDialog` with dynamic panel visibility |
| 🔍 **Auto-detect** | Automatically finds llama.cpp binaries and models |
| 🧠 **RAM-aware** | Displays available system RAM to guide model selection |
| 📌 **PID Persistence** | Server processes survive GUI restarts — stop them any time |
| 🖥️ **Multi-server** | Run multiple `llama-server` instances on different ports simultaneously; tracked in a `QListWidget` |
| 🗂️ **KV Cache Control** | Configure `--cache-type-k/v`, `--cache-reuse`, `--defrag-thold` from the GUI |
| 🤔 **Reasoning Model Support** | `--thinking`, `--jinja`, `--reasoning-budget` flags for CoT/reasoning models |
| 📦 **Portable Binary** | Ships as a single self-contained binary via PyInstaller |
| 🖥️ **Desktop Entry** | Auto-installs `.desktop` launcher and icon |
| 📱 **ARM64 Support** | Fully tested on Termux/Android ARM64 |

---

## 📸 Screenshots

> Coming soon.

---

## 🖥️ Requirements

### Common
- `cmake` >= 3.14
- `gcc` / `g++` >= 12
- `Python` >= 3.10
- `PyQt6` >= 6.6

### Debian / Linux
```bash
sudo apt install cmake gcc g++ python3 python3-pip git
pip install PyQt6>=6.6
```

### Termux / Android ARM64
```bash
pkg install cmake clang python git
pip install PyQt6 pyinstaller
```

### Windows
- [Visual Studio 2022](https://visualstudio.microsoft.com/) (with **Desktop development with C++** workload) or [Build Tools for Visual Studio 2022](https://aka.ms/vs/17/release/vs_BuildTools.exe)
- [CMake](https://cmake.org/download/) >= 3.16 (add to PATH during install)
- [Python](https://www.python.org/downloads/windows/) >= 3.10 (add to PATH during install)
- [Git for Windows](https://git-scm.com/download/win)

---

## 📥 Installation

### Debian / Linux

```bash
git clone https://github.com/dev-boffin-io/llama-forge.git
cd llama-forge
cmake -B build -S .
cmake --build build
```

### Termux / Android ARM64

```bash
git clone https://github.com/dev-boffin-io/llama-forge.git
cd llama-forge
cmake -B build -S .
cmake --build build
```

The binary `llama-gui` will be placed at the project root after a successful build.

### Windows

**Option A — Download pre-built binary (recommended)**

Download `llama-forge-windows-x64.zip` from [GitHub Actions Artifacts](https://github.com/dev-boffin-io/llama-forge/actions/workflows/build-windows.yml), extract, and run `llama-forge-gui.exe`.

**Option B — Build from source**

Open **Developer PowerShell for VS 2022** (or run `x64 Native Tools Command Prompt`):

```powershell
git clone https://github.com/dev-boffin-io/llama-forge.git
cd llama-forge

cmake -B build -G Ninja `
  -DCMAKE_BUILD_TYPE=Release `
  -DLLAMA_BUILD_TESTS=OFF `
  -DLLAMA_BUILD_EXAMPLES=ON `
  -DGGML_NATIVE=OFF

cmake --build build --parallel
```

The binary `llama-forge-gui.exe` will be placed at the project root.

> **Note:** Run cmake from a Visual Studio Developer shell so that `cl.exe` and `ninja` are on the PATH.

---

## 🔨 Building from Source

```bash
# Clone the repository
git clone https://github.com/dev-boffin-io/llama-forge.git
cd llama-forge

# Configure
cmake -B build -S .

# Build everything including the GUI
cmake --build build

# Run the GUI
./llama-gui
```

> The build system automatically creates a Python virtual environment, installs PyInstaller and PyQt6, and compiles the GUI into a standalone binary.

---

## 🚀 Usage

Launch the GUI:

```bash
# Linux / Android
./llama-gui

# Windows
llama-forge-gui.exe
```

Or use the installed desktop entry from your application menu.

---

### Chat Tab

Select a GGUF model and configure core inference parameters (`--ctx-size`, `--threads`, `--n-gpu-layers`, `--batch-size`, `--ubatch-size`, etc.). Boolean flags like `--flash-attn`, `--mlock`, `--jinja`, and `--thinking` can be toggled via checkboxes. `llama-cli` launches in an external terminal with the fully composed command.

**`--chat-template`** is a searchable ComboBox populated with all built-in templates supported by llama.cpp 2025: `chatml`, `llama3`, `llama4`, `mistral-v1/v3/v7`, `gemma`, `phi3`, `phi4`, `deepseek`/`deepseek2`/`deepseek3`, `qwen2`, `qwen3`, `command-r`, `falcon3`, `granite`, `grok-2`, and many more.

**KV Cache** settings (`--cache-type-k` / `--cache-type-v`) are exposed as readonly ComboBoxes supporting `f16`, `f32`, `bf16`, `q8_0`, `q4_0`, `q4_1`, `iq4_nl`, `q5_0`, `q5_1`. Only non-default values are passed to the binary.

**Reasoning model flags**: `--thinking` enables CoT output for reasoning models; `--reasoning-budget` sets the token budget (-1 = unlimited, 0 = off); `--prio` controls thread priority (0–3).

---

### Quantize Tab

Select a source GGUF and a target quantization type. A RAM-based recommendation banner suggests the best quant type for your system. Supports all standard `llama-quantize` types including `Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`, full `F16`/`F32`/`BF16`, and SIMD-optimised variants `q4_0_4_4`, `q4_0_4_8`, `q4_0_8_8` (ARM NEON / AVX-512 / AVX-VNNI). Output and token-embedding tensor types are configurable via dropdown. The built command is shown in the log before execution.

---

### Server Tab

The Server tab launches and manages `llama-server` entirely in the background using Qt-native **`QProcess`** — no terminal window or manual threading needed. Server stdout/stderr streams directly into the in-GUI `LogConsole`.

#### Core Arguments

| Argument | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8080` | Listening port |
| `--ctx-size` | `2048` | Context window size |
| `--threads` | `2` | CPU thread count |
| `--n-gpu-layers` | `0` | GPU offload layers |
| `--batch-size` | `512` | Prompt batch size |
| `--ubatch-size` | `512` | Physical batch size (micro-batch) |
| `--parallel` | `1` | Concurrent request slots |
| `--n-predict` | `-1` | Max tokens per response |

#### KV Cache (2025)

| Argument | Default | Description |
|---|---|---|
| `--cache-type-k` | `f16` | Key cache quantization type |
| `--cache-type-v` | `f16` | Value cache quantization type |
| `--cache-reuse` | *(off)* | Prefix token reuse threshold (0 = off) |
| `--defrag-thold` | *(off)* | KV cache defrag threshold (0.0–1.0, -1 = off) |

Supported cache types: `f16` · `f32` · `bf16` · `q8_0` · `q4_0` · `q4_1` · `iq4_nl` · `q5_0` · `q5_1`

#### Boolean Flags

Toggle via checkboxes (unchecked = not passed):

`--flash-attn` · `--mlock` · `--no-mmap` · `--no-warmup` · `--embedding` · `--reranking` · `--log-disable` · `--verbose` · `--slots-endpoint-disable` · `--metrics` · `--jinja` · `--cont-batching` · `--kv-unified` · `--no-prefill-assistant` · `--ctx-shift-disable`

> Flags not supported by the current build are automatically skipped with a warning in the log.

#### Optional Arguments

Leave empty to skip. Supported fields:

`--api-key` · `--chat-template` · `--system-prompt` · `--rope-freq-base` · `--rope-freq-scale` · `--override-kv` · `--lora` · `--path` · `--ssl-key-file` · `--ssl-cert-file` · `--slot-save-path` · `--tensor-split` · `--reasoning-budget` · `--prio`

An **Extra args** free-text field is also available for any flags not covered above.

#### Multi-Server Support

Multiple `llama-server` instances can run simultaneously on different ports. Each running instance appears in the **Active Servers** `QListWidget` as:

```
port 8080  PID 12345  [model-name.gguf]
```

Select a server from the list and press **⏹ Stop Selected** to terminate that `QProcess`. Press **🌐 Open Web UI** to open the selected server's built-in chat interface in a browser.

#### PID Persistence

When a server is started, its PID is written to `~/.cache/llama-forge/server_<port>.pid`. If the GUI is closed while a server is running, reopening the GUI will detect the surviving process and restore it to the Active Servers list — the Stop button remains functional across sessions.

---

### Convert Tools

Opens a **Convert Tools** `QDialog` (via the top-right button on the main window). Point to a HuggingFace model directory or LoRA adapter and convert it to GGUF using `convert_hf_to_gguf.py`. Panel visibility toggles dynamically based on the selected conversion script — HF-specific and LoRA-specific fields appear only when relevant.

---

## 📁 Project Structure

```
llama-forge/
├── llama_gui/                  # GUI frontend (Python/PyQt6)
│   ├── app.py                  # Entry point — QMainWindow + QTabWidget + "Convert Tools" button
│   ├── CMakeLists.txt          # GUI build script
│   ├── requirements.txt        # Python deps (PyQt6>=6.6, pyinstaller)
│   ├── llama_gui.png           # App icon
│   ├── gui/                    # Tab UI components
│   │   ├── __init__.py         # Shared QSS themes, LogConsole, make_scrollable()
│   │   ├── chat_tab.py         # Chat tab (PyQt6 widgets)
│   │   ├── quant_tab.py        # Quantize tab (PyQt6 widgets)
│   │   ├── server_tab.py       # Server tab (QProcess, QListWidget)
│   │   └── converter.py        # Convert Tools QDialog (dynamic panel visibility)
│   ├── core/                   # Business logic
│   │   ├── llama_detect.py     # Root detection, config persistence
│   │   ├── quant_logic.py      # Quant type definitions, arg builder
│   │   └── converter_logic.py  # Converter helpers
│   └── utils/                  # Helpers
│       ├── ram_detect.py       # System RAM detection
│       ├── gguf_info.py        # GGUF metadata reader
│       └── terminal.py         # Terminal launcher helpers
├── src/                        # Upstream llama.cpp C++ source
├── ggml/                       # Upstream ggml backend
├── tools/                      # llama-server, llama-cli, llama-quantize, etc.
├── CMakeLists.txt              # Root build (includes llama_gui)
└── llama-gui                   # Built binary (Linux/Android)
    llama-forge-gui.exe         # Built binary (Windows)
```

---

## 🔄 Upstream Sync

llama-forge is pinned to a specific [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) release tag for stability. The current pinned tag is **`b9297`**.

To update to a newer tag, edit `PINNED_TAG` in `scripts/sync-upstream.sh` and re-run.

### First-time setup

```bash
curl -fsSL https://raw.githubusercontent.com/dev-boffin-io/llama-forge/master/scripts/sync-upstream.sh \
    -o ~/llama-forge-sync.sh
chmod +x ~/llama-forge-sync.sh
```

### Run

```bash
bash ~/llama-forge-sync.sh
```

> The sync script automatically preserves all custom files (`llama_gui/`, `README.md`, `LICENSE`, `.gitattributes`, etc.) and restores itself — safe to run any time you want to update the pinned tag.

---

## 🤝 Contributing

Contributions are welcome for the `llama_gui/` frontend.
For upstream llama.cpp changes, please contribute to [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) directly.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

Upstream llama.cpp is also MIT licensed. See [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) for their license.

---

<div align="center">

Made with ❤️ by [Boffin](https://github.com/dev-boffin-io)

</div>
