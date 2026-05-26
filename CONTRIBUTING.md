# 🤝 Contributing to llama-forge

Thank you for considering a contribution to llama-forge! This document outlines how to contribute effectively.

---

## 📌 Scope of Contributions

llama-forge is a fork of [llama.cpp](https://github.com/ggml-org/llama.cpp). The upstream C++ inference engine is maintained by the ggml-org team.

**Contributions to this fork are accepted for:**

- `llama_gui/` — Python/tkinter GUI frontend
- `CMakeLists.txt` — GUI build system improvements
- Documentation (`README.md`, `AGENTS.md`, etc.)
- Termux/Android ARM64 compatibility fixes

**For contributions to the core inference engine**, please open a PR at [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp).

---

## 🛠️ Development Setup

```bash
# Clone
git clone https://github.com/dev-boffin-io/llama-forge.git
cd llama-forge

# Build
cmake -B build -S .
cmake --build build

# Run GUI
./llama-gui
```

---

## 📐 Code Style

### Python (llama_gui/)
- Follow PEP 8
- Use type hints where practical
- Keep tkinter widgets organized per tab file
- No external dependencies beyond Python stdlib

### Shell Scripts
- Use `#!/usr/bin/env bash`
- Always `set -e`
- Quote all variables

---

## 🌿 Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/name` | `feature/model-browser` |
| Bug Fix | `fix/name` | `fix/chat-crash` |
| Docs | `docs/name` | `docs/termux-guide` |

---

## 📬 Submitting a Pull Request

1. Fork the repository
2. Create your branch from `master`
3. Make your changes
4. Test on Debian/Linux (and Termux if relevant)
5. Commit with a clear message
6. Open a Pull Request with a description of what and why

---

## 🐛 Reporting Bugs

Open a [GitHub Issue](https://github.com/dev-boffin-io/llama-forge/issues) with:

- OS and architecture
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or screenshots

---

## 📬 Contact

Boffin — tradeguruboffin@gmail.com
