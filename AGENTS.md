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
| **Target Platforms** | Debian/Linux, Termux/Android ARM64 |
| **GUI Stack** | Python 3, tkinter, PyInstaller |

---

## 🗂️ Repository Structure

```
llama-forge/
├── llama_gui/          ← CUSTOM: GUI frontend — do NOT remove or modify carelessly
│   ├── app.py
│   ├── CMakeLists.txt
│   ├── gui/
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

The GUI `CMakeLists.txt` creates a Python venv, installs PyInstaller, and produces the `llama-gui` binary.

---

## 🧪 Conflict Resolution

When merge conflicts occur in upstream files, always resolve with:

```bash
git checkout --theirs <file>
git add <file>
```

Never manually edit upstream C++ headers or source files to resolve conflicts — take the upstream version entirely.

---

## 📬 Contact

Boffin — tradeguruboffin@gmail.com
