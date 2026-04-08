<div align="center">

# 🔨 llama-forge

### A GUI Frontend for llama.cpp

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Android%20ARM64-lightgrey)](https://github.com/dev-boffin-io/llama-forge)
[![Built With](https://img.shields.io/badge/Built%20With-Python%20%7C%20C%2B%2B-informational)](https://github.com/dev-boffin-io/llama-forge)
[![Upstream](https://img.shields.io/badge/Upstream-ggml--org%2Fllama.cpp-orange)](https://github.com/ggml-org/llama.cpp)
[![Maintained](https://img.shields.io/badge/Maintained-Yes-brightgreen)](https://github.com/dev-boffin-io/llama-forge)

**llama-forge** is a fork of [llama.cpp](https://github.com/ggml-org/llama.cpp) extended with a native tkinter GUI frontend for running, quantizing, converting, and serving large language models locally — with full support for Debian/Linux and Termux/Android ARM64.

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Installation](#installation)
  - [Debian / Linux](#debian--linux)
  - [Termux / Android ARM64](#termux--android-arm64)
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

llama-forge combines the full power of the llama.cpp inference engine with a user-friendly graphical interface. No command-line knowledge required to run, quantize, serve, or convert GGUF models. Designed for developers and power users who want a local, private, and efficient LLM workflow.

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 💬 **Chat** | Interactive chat with local GGUF models via `llama-cli` |
| ⚖️ **Quantize** | Quantize models to Q4_K_M, Q5_K_M, Q8_0, and more |
| 🌐 **Server** | Launch and manage `llama-server` instances with a full argument GUI |
| 🔄 **Convert** | Convert HuggingFace models to GGUF format |
| 🔍 **Auto-detect** | Automatically finds llama.cpp binaries and models |
| 🧠 **RAM-aware** | Displays available system RAM to guide model selection |
| 📌 **PID Persistence** | Server processes survive GUI restarts — stop them any time |
| 🖥️ **Multi-server** | Run multiple `llama-server` instances on different ports simultaneously |
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
- `python3-tk` (tkinter)

### Debian / Linux
```bash
sudo apt install cmake gcc g++ python3 python3-tk git
```

### Termux / Android ARM64
```bash
pkg install cmake clang python git
pip install pyinstaller
```

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

> The build system automatically creates a Python virtual environment, installs PyInstaller, and compiles the GUI into a standalone binary.

---

## 🚀 Usage

Launch the GUI:

```bash
./llama-gui
```

Or use the installed desktop entry from your application menu.

---

### Chat Tab

Select a GGUF model and configure core inference parameters (`--ctx-size`, `--threads`, `--chat-template`, `--n-gpu-layers`, etc.). Boolean flags like `--flash-attn`, `--mlock`, and `--interactive-first` can be toggled via checkboxes. `llama-cli` launches in an external terminal with the fully composed command.

---

### Quantize Tab

Select a source GGUF and a target quantization type. A RAM-based recommendation banner suggests the best quant type for your system. Supports all standard `llama-quantize` types including `Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`, and full F16/F32. Output and token-embedding tensor types are configurable via dropdown. The built command is shown in the log before execution.

---

### Server Tab

The Server tab launches and manages `llama-server` entirely in the background — no terminal window needed. Server stdout/stderr streams directly into the in-GUI log box.

#### Core Arguments

| Argument | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8080` | Listening port |
| `--ctx-size` | `2048` | Context window size |
| `--threads` | `2` | CPU thread count |
| `--n-gpu-layers` | `0` | GPU offload layers |
| `--batch-size` | `512` | Prompt batch size |
| `--parallel` | `1` | Concurrent request slots |
| `--n-predict` | `-1` | Max tokens per response |

#### Boolean Flags

Toggle via checkboxes (unchecked = not passed):

`--flash-attn` · `--mlock` · `--no-mmap` · `--no-warmup` · `--embedding` · `--reranking` · `--log-disable` · `--verbose` · `--slots-endpoint-disable` · `--metrics`

> Flags not supported by the current build are automatically skipped with a warning in the log.

#### Optional Arguments

Leave empty to skip. Supported fields:

`--api-key` · `--chat-template` · `--system-prompt` · `--rope-freq-base` · `--rope-freq-scale` · `--override-kv` · `--lora` · `--path` · `--ssl-key-file` · `--ssl-cert-file`

An **Extra args** free-text field is also available for any flags not covered above.

#### Multi-Server Support

Multiple `llama-server` instances can run simultaneously on different ports. Each running instance appears in the **Active Servers** list as:

```
port 8080  PID 12345  [model-name.gguf]
```

Select a server from the list and press **⏹ Stop Selected** to send `SIGTERM` to that process. Press **🌐 Open Web UI** to open the selected server's built-in chat interface in a browser.

#### PID Persistence

When a server is started, its PID is written to `~/.cache/llama-forge/server_<port>.pid`. If the GUI is closed while a server is running, reopening the GUI will detect the surviving process and restore it to the Active Servers list — the Stop button remains functional across sessions.

---

### Convert Tools

Opens a separate **Convert Tools** window (top-right button, outside the main tabs). Point to a HuggingFace model directory and convert it to GGUF using `convert_hf_to_gguf.py`. Additional converters for legacy GGML and LoRA formats are also available.

---

## 📁 Project Structure

```
llama-forge/
├── llama_gui/                  # GUI frontend (Python/tkinter)
│   ├── app.py                  # Entry point & App class
│   ├── CMakeLists.txt          # GUI build script
│   ├── llama_gui.png           # App icon
│   ├── gui/                    # Tab UI components
│   │   ├── __init__.py         # Shared widget helpers
│   │   ├── chat_tab.py         # Chat (SAFE) tab
│   │   ├── quant_tab.py        # Quantize tab
│   │   ├── server_tab.py       # Server tab (multi-server, PID persistence)
│   │   └── converter.py        # Convert Tools window
│   ├── core/                   # Business logic
│   │   ├── llama_detect.py     # Root detection, config persistence
│   │   ├── quant_logic.py      # Quant type definitions, arg builder
│   │   └── converter_logic.py  # Converter helpers
│   └── utils/                  # Helpers
│       ├── ram_detect.py       # System RAM detection
│       ├── gguf_info.py        # GGUF metadata reader
│       ├── terminal.py         # Terminal launcher helpers
│       └── subprocess_stream.py # Non-blocking stdout streaming
├── src/                        # Upstream llama.cpp C++ source
├── ggml/                       # Upstream ggml backend
├── tools/                      # llama-server, llama-cli, llama-quantize, etc.
├── CMakeLists.txt              # Root build (includes llama_gui)
└── llama-gui                   # Built binary (after cmake build)
```

---

## 🔄 Upstream Sync

llama-forge tracks [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) upstream master.

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

> The sync script automatically preserves all custom files (`llama_gui/`, `README.md`, `LICENSE`, `.gitattributes`, etc.) and restores itself — safe to run daily.

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
