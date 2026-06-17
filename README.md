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
  - [Benchmark Tab](#benchmark-tab)
  - [Imatrix Tab](#imatrix-tab)
  - [Perplexity Tab](#perplexity-tab)
  - [GGUF Tools Tab](#gguf-tools-tab)
  - [LoRA & CVector Tab](#lora--cvector-tab)
  - [Extra Tools Tab](#extra-tools-tab)
  - [Convert Tools](#convert-tools)
- [Project Structure](#project-structure)
- [Upstream Sync](#upstream-sync)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

llama-forge combines the full power of the llama.cpp inference engine with a user-friendly graphical interface built on **PyQt6**. No command-line knowledge required to run, quantize, serve, benchmark, or convert GGUF models. Designed for developers and power users who want a local, private, and efficient LLM workflow.

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| 💬 **Chat** | Interactive chat with local GGUF models via `llama-cli` |
| 🧪 **Quantize** | Quantize models to Q4_K_M, Q5_K_M, Q8_0, IQ variants, and more via `llama-quantize` |
| 🖥️ **Server** | Launch and manage `llama-server` instances with full argument GUI; powered by `QProcess` |
| 📊 **Benchmark** | Measure inference speed (tokens/sec) via `llama-bench` with live output |
| 🧮 **Imatrix** | Generate importance matrix files for IQ quants via `llama-imatrix` |
| 📐 **Perplexity** | Measure model quality (PPL score) via `llama-perplexity`; supports hellaswag, winogrande, KL-divergence modes |
| 🗂️ **GGUF Tools** | Split/merge GGUF shards (`llama-gguf-split`), verify file integrity (`llama-gguf-hash`), read/edit metadata (`llama-gguf`) |
| 🔗 **LoRA & CVector** | Merge LoRA adapters into base models (`llama-export-lora`); generate control vectors (`llama-cvector-generator`) |
| 🛠️ **Extra Tools** | TTS (`llama-tts`), multimodal/vision chat (`llama-mtmd-cli`), RPC server (`llama-rpc-server`), tokenizer (`llama-tokenize`), speculative decoding (`llama-speculative`) |
| 🔄 **Convert** | Convert HuggingFace models to GGUF via a `QDialog` with dynamic panel visibility |
| 🔍 **Auto-detect** | Automatically finds llama.cpp binaries and models |
| 🧠 **RAM-aware** | Displays available system RAM to guide model and quant selection |
| 📌 **PID Persistence** | Server processes survive GUI restarts — stop them any time |
| 🖥️ **Multi-server** | Run multiple `llama-server` instances on different ports simultaneously |
| 🗂️ **KV Cache Control** | Configure `--cache-type-k/v`, `--cache-reuse`, `--defrag-thold` from the GUI |
| 🤔 **Reasoning Model Support** | `--thinking`, `--jinja`, `--reasoning-budget` flags for CoT/reasoning models |
| 📦 **Portable Binary** | Ships as a single self-contained binary via PyInstaller |
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

### Windows

**Option A — Download pre-built binary (recommended)**

Download `llama-forge-windows-x64.zip` from [GitHub Actions Artifacts](https://github.com/dev-boffin-io/llama-forge/actions/workflows/build-windows.yml), extract, and run `llama-forge-gui.exe`.

**Option B — Build from source**

Open **Developer PowerShell for VS 2022**:

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

---

## 🔨 Building from Source

```bash
git clone https://github.com/dev-boffin-io/llama-forge.git
cd llama-forge
cmake -B build -S .
cmake --build build
./llama-gui
```

> The build system automatically creates a Python virtual environment, installs PyInstaller and PyQt6, and compiles the GUI into a standalone binary.

---

## 🚀 Usage

```bash
# Linux / Android
./llama-gui

# Windows
llama-forge-gui.exe
```

---

### Chat Tab

Select a GGUF model and configure core inference parameters (`--ctx-size`, `--threads`, `--n-gpu-layers`, `--batch-size`, `--ubatch-size`). Boolean flags like `--flash-attn`, `--mlock`, `--jinja`, and `--thinking` can be toggled via checkboxes. `llama-cli` launches in an external terminal.

**`--chat-template`** supports all built-in llama.cpp 2025 templates: `chatml`, `llama3/4`, `mistral-v1/v3/v7`, `gemma`, `phi3/4`, `deepseek`/`deepseek2/3`, `qwen2/3`, `command-r`, `falcon3`, `granite`, `grok-2`, and many more.

**KV Cache** settings (`--cache-type-k/v`) support `f16`, `f32`, `bf16`, `q8_0`, `q4_0`, `q4_1`, `iq4_nl`, `q5_0`, `q5_1`.

**Reasoning flags**: `--thinking`, `--reasoning-budget`, `--prio`.

---

### Quantize Tab

Select a source GGUF and target quant type. A RAM-based recommendation banner suggests the best type for your system. Supports all `llama-quantize` types: standard K-quants (`Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`), float types (`F16`, `BF16`, `F32`), IQ types (`iq2_xxs` through `iq4_nl`), TQ types (`tq1_0`, `tq2_0`), and SIMD-optimised variants (`q4_0_4_4`, `q4_0_4_8`, `q4_0_8_8`).

The `--imatrix` field points to a `.dat` file generated by the **Imatrix tab** for significantly better quality at low bit rates.

---

### Server Tab

Launches and manages `llama-server` in the background via `QProcess`. Multiple instances can run on different ports simultaneously. Each appears in the **Active Servers** list as `port 8080  PID 12345  [model-name.gguf]`. PID files persist across GUI restarts.

Supports all 2025 server flags: KV cache control, `--cont-batching`, `--kv-unified`, `--jinja`, `--embedding`, `--reranking`, `--metrics`, SSL, slot management, and more.

---

### Benchmark Tab

Runs `llama-bench` in the background and streams results live. Configure prompt token count (`-p`), generation count (`-n`), GPU layers (`-ngl`), threads, batch sizes, and repetitions. Output format: `md` (default), `json`, `jsonl`, `csv`, `sql`.

---

### Imatrix Tab

Generates an importance matrix (`.dat` file) from a calibration dataset using `llama-imatrix`. The output file is used in the **Quantize tab** (`--imatrix` field) to produce significantly higher-quality IQ quantizations (`iq2_xxs`, `iq3_xs`, etc.).

Configure calibration data file, output path, context size, threads, GPU layers, chunk count, and PPL options.

---

### Perplexity Tab

Measures model quality using `llama-perplexity`. Supports multiple evaluation modes:

| Mode | Description |
|------|-------------|
| perplexity (default) | Standard PPL measurement on a text dataset |
| hellaswag | HellaSwag benchmark (multiple choice) |
| winogrande | Winogrande benchmark |
| multiple-choice | Generic multiple-choice evaluation |
| kl-divergence | KL divergence between two model outputs |

Useful for comparing quality before and after quantization. Lower PPL = better quality.

---

### GGUF Tools Tab

Three sub-tools for working with GGUF files directly:

**🔀 Split / Merge** (`llama-gguf-split`)
Split large GGUF files into smaller shards (`--split-max-size`, `--split-max-tensors`) or merge shards back into a single file (`--merge`).

**#️⃣ Hash** (`llama-gguf-hash`)
Verify GGUF file integrity with SHA256 (default), SHA1, UUID, or xxHash. Useful for confirming downloads are uncorrupted.

**🏷️ Metadata** (`llama-gguf`)
Read and edit GGUF KV metadata fields (e.g. `general.name`, `tokenizer.chat_template`). Supports read, write (`--set`), and remove (`--rm`) operations.

---

### LoRA & CVector Tab

**📤 Export LoRA** (`llama-export-lora`)
Merge a LoRA adapter GGUF into a base model GGUF to produce a standalone merged model. Configure `--lora-scaled` factor and thread count.

**🎛️ Control Vector** (`llama-cvector-generator`)
Generate control vectors from positive/negative prompt pairs using PCA. Control vectors steer model behaviour (tone, style, verbosity) at inference time via `--control-vector` in the Chat or Server tab.

---

### Extra Tools Tab

Five additional tools in sub-tabs:

**🔊 TTS** (`llama-tts`)
Text-to-speech synthesis using OuteTTS-compatible GGUF models. Configure TTS model, optional vocoder, speaker file, and output WAV path.

**🖼️ Multimodal** (`llama-mtmd-cli`)
Vision/audio chat supporting LLaVA, Qwen2-VL, Gemma4V, InternVL, Pixtral, MiniCPM-V, and 20+ other multimodal architectures. Attach images or audio files alongside text prompts.

**🌐 RPC Server** (`llama-rpc-server`)
Start a remote GPU offload server. On the main machine, use `-rpc <host>:<port>` with `llama-server` or `llama-cli` to offload layers to this machine. Runs in background via `QProcess`.

**🔢 Tokenize** (`llama-tokenize`)
Tokenize arbitrary text with a given model's vocabulary. Shows token IDs, token count, and supports `--no-bos`. Useful for prompt engineering and context budget planning.

**⚡ Speculative** (`llama-speculative` / `llama-speculative-simple`)
Speculative decoding: a small draft model generates candidate tokens which the large target model verifies in parallel — significantly faster generation at no quality cost. Configure draft model, target model, draft length, and context size.

---

### Convert Tools

Opens a **Convert Tools** dialog (toolbar button). Converts HuggingFace model directories or LoRA adapters to GGUF format. Supported scripts:

| Script | Use case |
|--------|----------|
| `convert_hf_to_gguf.py` | HuggingFace model → GGUF |
| `convert_llama_ggml_to_gguf.py` | Legacy GGML format → GGUF |
| `convert_lora_to_gguf.py` | LoRA adapter → GGUF |

HF-specific and LoRA-specific option panels show/hide dynamically based on the selected script.

---

## 📁 Project Structure

```
llama-forge/
├── llama_gui/                    # GUI frontend (Python/PyQt6)
│   ├── app.py                    # Entry point — QMainWindow + QTabWidget + toolbar
│   ├── CMakeLists.txt            # GUI build script
│   ├── requirements.txt          # Python deps (PyQt6>=6.6, pyinstaller)
│   ├── llama_gui.png             # App icon
│   ├── gui/                      # Tab UI components
│   │   ├── __init__.py           # Shared QSS theme, LogConsole, make_scrollable()
│   │   ├── chat_tab.py           # 💬 Chat tab
│   │   ├── quant_tab.py          # 🧪 Quantize tab
│   │   ├── server_tab.py         # 🖥 Server tab (QProcess + QListWidget)
│   │   ├── bench_tab.py          # 📊 Benchmark tab (llama-bench)
│   │   ├── imatrix_tab.py        # 🧮 Imatrix tab (llama-imatrix)
│   │   ├── perplexity_tab.py     # 📐 Perplexity tab (llama-perplexity)
│   │   ├── gguf_tools_tab.py     # 🗂 GGUF Tools tab (split / hash / metadata)
│   │   ├── lora_tab.py           # 🔗 LoRA & CVector tab
│   │   ├── extra_tools_tab.py    # 🛠 Extra Tools tab (TTS / MTMD / RPC / Tokenize / Speculative)
│   │   └── converter.py          # 🔄 Convert Tools QDialog
│   ├── core/                     # Business logic
│   │   ├── llama_detect.py       # Root detection, config persistence
│   │   ├── quant_logic.py        # Quant type definitions, arg builder
│   │   └── converter_logic.py    # Converter helpers
│   └── utils/                    # Helpers
│       ├── ram_detect.py         # System RAM detection
│       ├── gguf_info.py          # GGUF metadata reader
│       ├── subprocess_stream.py  # Threaded stdout/stderr streaming
│       └── terminal.py           # Cross-platform terminal launcher
├── src/                          # Upstream llama.cpp C++ source
├── ggml/                         # Upstream ggml backend
├── tools/                        # llama-server, llama-cli, llama-bench, etc.
├── CMakeLists.txt                # Root build (includes llama_gui)
└── llama-gui                     # Built binary (Linux/Android)
    llama-forge-gui.exe           # Built binary (Windows)
```

---

## 🔄 Upstream Sync

llama-forge is pinned to **`b9297`** of [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp).

```bash
bash ~/llama-forge-sync.sh
```

> The sync script preserves all custom files (`llama_gui/`, `README.md`, `AGENTS.md`, etc.) and restores them after resetting to upstream.

---

## 🤝 Contributing

Contributions are welcome for the `llama_gui/` frontend.
For upstream llama.cpp changes, please contribute to [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) directly.

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
Upstream llama.cpp is also MIT licensed.

---

<div align="center">

Made with ❤️ by [Boffin](https://github.com/dev-boffin-io)

</div>
