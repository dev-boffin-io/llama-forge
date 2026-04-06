<div align="center">

# 🔨 llama-forge

### A GUI Frontend for llama.cpp

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Android%20ARM64-lightgrey)](https://github.com/dev-boffin-io/llama-forge)
[![Built With](https://img.shields.io/badge/Built%20With-Python%20%7C%20C%2B%2B-informational)](https://github.com/dev-boffin-io/llama-forge)
[![Upstream](https://img.shields.io/badge/Upstream-ggml--org%2Fllama.cpp-orange)](https://github.com/ggml-org/llama.cpp)
[![Maintained](https://img.shields.io/badge/Maintained-Yes-brightgreen)](https://github.com/dev-boffin-io/llama-forge)

**llama-forge** is a fork of [llama.cpp](https://github.com/ggml-org/llama.cpp) extended with a native tkinter GUI frontend for running, quantizing, and converting large language models locally — with full support for Debian/Linux and Termux/Android ARM64.

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
- [Project Structure](#project-structure)
- [Upstream Sync](#upstream-sync)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

llama-forge combines the full power of the llama.cpp inference engine with a user-friendly graphical interface. No command-line knowledge required to run, quantize, or convert GGUF models. Designed for developers and power users who want a local, private, and efficient LLM workflow.

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 💬 **Chat** | Interactive chat with local GGUF models via llama-cli |
| ⚖️ **Quantize** | Quantize models to Q4_K_M, Q5_K_M, Q8_0, and more |
| 🔄 **Convert** | Convert HuggingFace models to GGUF format |
| 🔍 **Auto-detect** | Automatically finds llama.cpp binaries and models |
| 🧠 **RAM-aware** | Displays available system RAM to guide model selection |
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

### Chat Tab
Select a model, configure parameters, and start chatting with any local GGUF model.

### Quantize Tab
Select a source model and target quantization type. llama-forge will invoke `llama-quantize` automatically.

### Convert Tab
Point to a HuggingFace model directory and convert it to GGUF using `convert_hf_to_gguf.py`.

---

## 📁 Project Structure

```
llama-forge/
├── llama_gui/              # GUI frontend (Python/tkinter)
│   ├── app.py              # Entry point
│   ├── CMakeLists.txt      # GUI build script
│   ├── gui/                # Tab UI components
│   │   ├── chat_tab.py
│   │   ├── quant_tab.py
│   │   └── converter.py
│   ├── core/               # Business logic
│   │   ├── llama_detect.py
│   │   ├── quant_logic.py
│   │   └── converter_logic.py
│   └── utils/              # Helpers
│       ├── ram_detect.py
│       ├── gguf_info.py
│       ├── terminal.py
│       └── subprocess_stream.py
├── src/                    # Upstream llama.cpp C++ source
├── ggml/                   # Upstream ggml backend
├── tools/                  # llama-server, llama-cli, etc.
├── CMakeLists.txt          # Root build (includes llama_gui)
└── llama-gui               # Built binary (after cmake build)
```

---

## 🔄 Upstream Sync

llama-forge tracks [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) upstream master.

### First-time setup

```bash
# Download the sync script
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
