# 🤖 Agent Guidelines — llama-forge

This document provides instructions and context for AI coding agents (Claude, GitHub Copilot, Gemini, etc.) working on this repository.

---

## 📌 Project Identity

| Field | Value |
|-------|-------|
| **Project** | llama-forge |
| **Type** | Fork of ggml-org/llama.cpp with GUI frontend |
| **Maintainer** | Boffin (dev-boffin-io) |
| **Upstream** | https://github.com/ggml-org/llama.cpp |
| **Target Platforms** | Debian/Linux, Termux/Android ARM64, Windows |
| **GUI Stack** | Python 3, PyQt6, PyInstaller |

---

## 🗂️ Repository Structure

```
llama-forge/
├── llama_gui/                    ← CUSTOM: GUI frontend — do NOT remove or modify carelessly
│   ├── app.py                    ← QMainWindow + QTabWidget + QToolBar ("Convert Tools")
│   ├── CMakeLists.txt
│   ├── requirements.txt          ← PyQt6>=6.6, pyinstaller
│   ├── gui/
│   │   ├── __init__.py           ← Shared QSS theme, LogConsole, make_scrollable()
│   │   ├── chat_tab.py           ← 💬 Chat tab (llama-cli, terminal launch)
│   │   ├── quant_tab.py          ← 🧪 Quantize tab (llama-quantize)
│   │   ├── server_tab.py         ← 🖥 Server tab (QProcess + QListWidget + PID persistence)
│   │   ├── bench_tab.py          ← 📊 Benchmark tab (llama-bench, QProcess)
│   │   ├── imatrix_tab.py        ← 🧮 Imatrix tab (llama-imatrix, QProcess)
│   │   ├── perplexity_tab.py     ← 📐 Perplexity tab (llama-perplexity, QProcess)
│   │   ├── gguf_tools_tab.py     ← 🗂 GGUF Tools tab (split/hash/metadata, inner QTabWidget)
│   │   ├── lora_tab.py           ← 🔗 LoRA & CVector tab (export-lora + cvector-generator)
│   │   ├── extra_tools_tab.py    ← 🛠 Extra Tools tab (TTS/MTMD/RPC/Tokenize/Speculative)
│   │   └── converter.py          ← 🔄 Convert Tools QDialog (dynamic HF/LoRA panel visibility)
│   ├── core/
│   │   ├── llama_detect.py       ← Root detection, config persistence (~/.llama_cpp_gui.json)
│   │   ├── quant_logic.py        ← QUANT_TYPES, TENSOR_TYPES, KV_CACHE_TYPES, build_quantize_args()
│   │   └── converter_logic.py    ← SCRIPTS, HF_BOOL_FLAGS, HF_TEXT_FLAGS, build_convert_args()
│   └── utils/
│       ├── ram_detect.py         ← Cross-platform RAM detection + quant recommendation
│       ├── gguf_info.py          ← GGUF binary parser (~46 architectures)
│       ├── subprocess_stream.py  ← Threaded stdout/stderr streaming (deadlock-safe)
│       └── terminal.py           ← Cross-platform terminal launch (Linux/macOS/Windows/Termux)
├── src/                          ← Upstream llama.cpp C++ source
├── ggml/                         ← Upstream ggml backend
├── tools/                        ← Upstream tools (server, cli, bench, imatrix, etc.)
├── CMakeLists.txt                ← Root build — contains custom llama_gui block at bottom
├── README.md                     ← CUSTOM
├── AGENTS.md                     ← CUSTOM
├── CONTRIBUTING.md               ← CUSTOM
├── SECURITY.md                   ← CUSTOM
├── AUTHORS                       ← CUSTOM
├── LICENSE                       ← CUSTOM
└── .gitattributes                ← CUSTOM
```

---

## ⚠️ Critical Rules

1. **Never remove or rename** `llama_gui/` under any circumstance.
2. **Never remove** the `llama_gui` block at the bottom of root `CMakeLists.txt`.
3. **Never modify** upstream llama.cpp files (`src/`, `ggml/`, `tools/`, `common/`) unless resolving a merge conflict — always prefer `--theirs` for upstream files.
4. **Never break** Termux/Android ARM64 build compatibility.
5. **Always preserve** all custom files listed above when performing upstream syncs.
6. **Do not use** `git pull` or GitHub Desktop merge for upstream sync — use `git reset --hard upstream/master` only.
7. **Never introduce** tkinter imports or `subprocess` + `threading` patterns in the GUI layer — the stack is **PyQt6 exclusively**. Use `QProcess` for subprocess management, Qt signals/slots for thread safety.
8. **Never add** external Python dependencies beyond stdlib + `PyQt6` — keep `requirements.txt` minimal.

---

## 🖥️ GUI Architecture Notes

### Entry point (`app.py`)
`MainWindow` creates a `QTabWidget` with **9 tabs** and a `QToolBar` containing the **Convert Tools** button. The toolbar is at `Qt.ToolBarArea.TopToolBarArea`. `tabBar().setUsesScrollButtons(True)` and `setExpanding(False)` ensure all tabs are reachable when the window is narrow.

Config persists to `~/.llama_cpp_gui.json` via `core/llama_detect.py`. Saved keys: `bin_dir`, `chat_model`, `quant_gguf`, `server_model`, `bench_model`, `imatrix_model`, `ppl_model`.

### Tab inventory

| Tab | File | Binary | Launch method |
|-----|------|--------|---------------|
| 💬 Chat | `chat_tab.py` | `llama-cli` | External terminal |
| 🧪 Quantize | `quant_tab.py` | `llama-quantize` | External terminal |
| 🖥 Server | `server_tab.py` | `llama-server` | `QProcess` (background) |
| 📊 Benchmark | `bench_tab.py` | `llama-bench` | `QProcess` (background) |
| 🧮 Imatrix | `imatrix_tab.py` | `llama-imatrix` | `QProcess` (background) |
| 📐 Perplexity | `perplexity_tab.py` | `llama-perplexity` | `QProcess` (background) |
| 🗂 GGUF Tools | `gguf_tools_tab.py` | `llama-gguf-split`, `llama-gguf-hash`, `llama-gguf` | `QProcess` (background) |
| 🔗 LoRA & CVector | `lora_tab.py` | `llama-export-lora`, `llama-cvector-generator` | External terminal |
| 🛠 Extra Tools | `extra_tools_tab.py` | `llama-tts`, `llama-mtmd-cli`, `llama-rpc-server`, `llama-tokenize`, `llama-speculative` | Mixed (terminal / QProcess) |
| 🔄 Convert Tools | `converter.py` | `convert_hf_to_gguf.py`, `convert_lora_to_gguf.py`, `convert_llama_ggml_to_gguf.py` | `QProcess` (dialog) |

### Shared utilities (`gui/__init__.py`)
- `STYLE_SHEET` — app-wide Tokyo Night dark QSS
- `LogConsole` — fixed-height, read-only, monospaced `QPlainTextEdit`
- `append_log(widget, text)` — appends text and auto-scrolls
- `make_scrollable(content)` — wraps any widget in a `QScrollArea`
- `card(title)` — creates a styled `QGroupBox`

### Tabs with inner QTabWidget
`gguf_tools_tab.py` and `extra_tools_tab.py` each contain an inner `QTabWidget` with sub-tabs. All sub-tabs share a single `LogConsole` instance from the parent tab.

### Server tab specifics (`server_tab.py`)
- `QProcess` exclusively — no `subprocess`, no threading
- PID persistence: `~/.cache/llama-forge/server_<port>.pid`
- Multi-server: `_servers: dict[str, dict]` keyed by port string
- Restores surviving processes on startup via `_restore_state()`

### Process launch patterns
- **Background** (Bench, Imatrix, Perplexity, Server, RPC, Tokenize): `QProcess` — stdout streamed to `LogConsole` via `readyReadStandardOutput`
- **Terminal** (Chat, Quantize, LoRA, CVector, TTS, MTMD, Speculative): `launch_in_terminal()` from `utils/terminal.py`
- Both patterns connect `finished` and `errorOccurred` signals for cleanup

---

## 🔁 Upstream Sync Procedure

```bash
bash ~/llama-forge-sync.sh
```

This script backs up `llama_gui/` and custom files, resets to `upstream/master`, restores, commits, and force-pushes.

---

## 🛠️ Build System

```cmake
if (LLAMA_STANDALONE AND EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/llama_gui/CMakeLists.txt)
    message(STATUS "Building llama_gui")
    add_subdirectory(llama_gui)
endif()
```

The GUI `CMakeLists.txt` creates a Python venv, installs `PyQt6>=6.6` + PyInstaller, and produces the `llama-gui` binary.

---

## 🧪 Conflict Resolution

```bash
git checkout --theirs <file>
git add <file>
```

Never manually edit upstream C++ headers or source files — take the upstream version entirely.

---

## 📬 Contact

Boffin — tradeguruboffin@gmail.com
