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
├── llama_gui/          ← CUSTOM: GUI frontend — do NOT remove or modify carelessly
│   ├── app.py          ← QMainWindow entry point with QTabWidget + "Convert Tools" button
│   ├── CMakeLists.txt
│   ├── requirements.txt  ← PyQt6>=6.6, pyinstaller
│   ├── gui/
│   │   ├── __init__.py   ← Shared QSS themes, LogConsole, make_scrollable()
│   │   ├── chat_tab.py   ← PyQt6 Chat tab
│   │   ├── quant_tab.py  ← PyQt6 Quantize tab
│   │   ├── server_tab.py ← QProcess-based server management + QListWidget
│   │   └── converter.py  ← QDialog with dynamic HF/LoRA panel visibility
│   ├── core/
│   └── utils/
├── src/                ← Upstream llama.cpp C++ source
├── ggml/               ← Upstream ggml backend
├── tools/              ← Upstream tools (server, cli, etc.)
├── CMakeLists.txt      ← Root build — contains custom llama_gui block at bottom
├── README.md           ← CUSTOM
├── AGENTS.md           ← CUSTOM
├── CONTRIBUTING.md     ← CUSTOM
├── SECURITY.md         ← CUSTOM
├── AUTHORS             ← CUSTOM
├── LICENSE             ← CUSTOM
└── .gitattributes      ← CUSTOM
```

---

## ⚠️ Critical Rules

1. **Never remove or rename** `llama_gui/` under any circumstance.
2. **Never remove** the `llama_gui` block at the bottom of root `CMakeLists.txt`.
3. **Never modify** upstream llama.cpp files (`src/`, `ggml/`, `tools/`, `common/`) unless resolving a merge conflict — and always prefer `--theirs` for upstream files.
4. **Never break** Termux/Android ARM64 build compatibility.
5. **Always preserve** the custom files listed above when performing upstream syncs.
6. **Do not use** `git pull` or GitHub Desktop merge for upstream sync — use `git reset --hard upstream/master` only.
7. **Never introduce** tkinter imports or `subprocess` + `threading` patterns in the GUI layer — the GUI stack is PyQt6 exclusively. Use `QProcess` for subprocess management and Qt signals/slots for thread safety.

---

## 🔁 Upstream Sync Procedure

```bash
bash ~/llama-forge-sync.sh
```

This script:
- Backs up `llama_gui/` and all custom files
- Resets to `upstream/master`
- Restores all custom files
- Commits and force-pushes to origin

---

## 🛠️ Build System

The GUI is built automatically during cmake configure if `llama_gui/CMakeLists.txt` exists:

```cmake
if (LLAMA_STANDALONE AND EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/llama_gui/CMakeLists.txt)
    message(STATUS "Building llama_gui")
    add_subdirectory(llama_gui)
endif()
```

The GUI `CMakeLists.txt` creates a Python venv, installs `PyQt6>=6.6` and PyInstaller from `requirements.txt`, and produces the `llama-gui` binary.

---

## 🧪 Conflict Resolution

When merge conflicts occur in upstream files, always resolve with:

```bash
git checkout --theirs <file>
git add <file>
```

Never manually edit upstream C++ headers or source files to resolve conflicts — take the upstream version entirely.

---

## 🖥️ GUI Architecture Notes

- **Entry point**: `app.py` implements `QMainWindow` with a `QTabWidget` hosting Chat, Quantize, and Server tabs. The "Convert Tools" button in the toolbar opens the converter as a separate window.
- **Shared utilities**: `gui/__init__.py` provides the app-wide QSS theme, the `LogConsole` widget (used by Server and Quantize tabs), and the `make_scrollable()` helper for wrapping any widget in a `QScrollArea`.
- **Server process management**: `server_tab.py` uses `QProcess` exclusively — no `subprocess` module, no manual threading. Active servers are displayed in a `QListWidget`.
- **Convert Tools**: `converter.py` is a `QDialog`. Panel sections for HuggingFace-specific and LoRA-specific options show/hide dynamically when the user changes the conversion script.

---

## 📬 Contact

Boffin — tradeguruboffin@gmail.com
