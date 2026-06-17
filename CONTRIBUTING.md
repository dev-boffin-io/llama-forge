# 🤝 Contributing to llama-forge

Thank you for considering a contribution to llama-forge! This document outlines how to contribute effectively.

---

## 📌 Scope of Contributions

llama-forge is a fork of [llama.cpp](https://github.com/ggml-org/llama.cpp). The upstream C++ inference engine is maintained by the ggml-org team.

**Contributions to this fork are accepted for:**

- `llama_gui/` — Python/PyQt6 GUI frontend (all tabs)
- `CMakeLists.txt` — GUI build system improvements
- Documentation (`README.md`, `AGENTS.md`, etc.)
- Termux/Android ARM64 compatibility fixes

**For contributions to the core inference engine**, please open a PR at [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) directly.

---

## 🛠️ Development Setup

```bash
# Clone
git clone https://github.com/dev-boffin-io/llama-forge.git
cd llama-forge

# Build (creates venv, installs PyQt6 + PyInstaller, compiles GUI binary)
cmake -B build -S .
cmake --build build

# Run GUI directly from source (without the compiled binary)
cd llama_gui
pip install -r requirements.txt
python app.py
```

---

## 📐 Code Style

### Python (`llama_gui/`)
- Follow PEP 8
- Use type hints where practical
- **One file per tab** — keep tab UI components in `gui/<name>_tab.py`
- Use `QProcess` for all subprocess management — do **not** use `subprocess` + `threading`
- Use `LogConsole` + `append_log()` from `gui/__init__.py` for all log output
- Use `card()` from `gui/__init__.py` for grouped option sections
- Background tools (bench, imatrix, perplexity, server, rpc, tokenize): use `QProcess`
- Interactive/terminal tools (chat, quantize, lora, tts, mtmd, speculative): use `launch_in_terminal()` from `utils/terminal.py`
- No external dependencies beyond Python stdlib and `PyQt6` — keep `requirements.txt` minimal
- All tabs must implement a `startup_log(msg: str)` method for startup messages from `app.py`

### Tab pattern (new tabs must follow this)

```python
class MyNewTab(QWidget):
    def __init__(self, app: QWidget):
        super().__init__()
        self.app = app          # reference to MainWindow for shared state
        self._proc: QProcess | None = None
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        # ... scrollable content area ...
        outer.addWidget(make_scrollable(content), 1)
        self.logbox = LogConsole(height=280)
        outer.addWidget(self.logbox)

    def startup_log(self, msg: str):
        append_log(self.logbox, msg)
```

### Shell Scripts
- Use `#!/usr/bin/env bash`
- Always `set -e`
- Quote all variables

---

## 🖥️ Adding a New Tab

1. Create `llama_gui/gui/<name>_tab.py` following the tab pattern above
2. Import it in `llama_gui/app.py`
3. Instantiate and add to `self.tabs` with a short emoji label
4. Add `startup_log()` calls in `MainWindow._startup_info()` for config values
5. Add config keys to `MainWindow.save()` if the tab has persistent model/path state
6. Document the new tab in `README.md` and `AGENTS.md`

---

## 🌿 Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/name` | `feature/embedding-tab` |
| Bug Fix | `fix/name` | `fix/bench-overflow` |
| Docs | `docs/name` | `docs/extra-tools-guide` |

---

## 📬 Submitting a Pull Request

1. Fork the repository
2. Create your branch from `master`
3. Make your changes
4. Test on Debian/Linux (and Termux if relevant)
5. Run a quick syntax check: `python3 -m py_compile llama_gui/**/*.py`
6. Commit with a clear message
7. Open a Pull Request with a description of what and why

---

## 🐛 Reporting Bugs

Open a [GitHub Issue](https://github.com/dev-boffin-io/llama-forge/issues) with:

- OS and architecture
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or screenshots (the LogConsole output is especially helpful)

---

## 📬 Contact

Boffin — tradeguruboffin@gmail.com
