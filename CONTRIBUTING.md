# Contributing to llama-forge

> **llama-forge** is a personal fork of [llama.cpp](https://github.com/ggml-org/llama.cpp).
> Contributions are welcome, but this project has different priorities from upstream — primarily around the `llama_gui/` desktop application and fork-specific infrastructure.

---

## Scope of contributions

This fork has two distinct areas:

**1. `llama_gui/` — fork-specific** — contributions are fully open here:
- Bug fixes and UX improvements to the GUI
- New features for Chat, Quantize, or Converter tabs
- CMake build system improvements
- Documentation

**2. Core llama.cpp engine** — contributions to the inference engine, backends, model support, etc. should be made **upstream** at [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp). This fork syncs from upstream periodically. PRs that duplicate upstream work will be closed.

---

## AI usage policy

AI tools may be used in an assistive capacity. The following rules apply:

- The majority of submitted code must be written by a human. Code that is primarily AI-generated will not be accepted regardless of subsequent editing.
- If AI was used in any part of the contribution, disclose how it was used in the PR description.
- All submitted code must be fully reviewed and understood by the contributor before opening a PR. Be prepared to explain any line on request.
- Do not use AI to write issue reports, PR descriptions, or any communication in this repository.

---

## Pull requests

### Before opening a PR

- Search existing PRs and issues to avoid duplicating work.
- Keep PRs focused — one feature or fix per PR.
- For GUI changes, test on a Debian-based Linux desktop environment if possible.
- For CMake changes, verify both the standalone GUI build (`cmake -B build -S llama_gui/`) and the integrated build (`cmake -B build -S .`) still work.

### PR description

Include:
- What the change does and why
- How it was tested
- Any known limitations

### After opening a PR

- Expect review feedback and be responsive to it.
- If your PR becomes stale against `master`, rebase it.

---

## GUI coding guidelines (`llama_gui/`)

The GUI follows these conventions:

- **Python 3.10+**, type hints on all function signatures
- **Tkinter** for UI — no additional UI framework dependencies
- Module layout: `gui/` for Tkinter widgets, `core/` for logic, `utils/` for helpers
- All imports are absolute from the `llama_gui/` root (e.g. `from core.llama_detect import ...`)
- Font sizes via `scale_font()` — never hardcoded pixel values
- Scrollable panels via `make_scrollable()` from `gui/__init__.py`
- Subprocess calls use `utils/subprocess_stream.py` — never `subprocess.STDOUT` with blocking reads
- Terminal launches use `utils/terminal.py` — never hardcoded `--command` flags

---

## Core C/C++ coding guidelines

For contributions to the core engine (synced from upstream), follow the [upstream coding guidelines](https://github.com/ggml-org/llama.cpp/blob/master/CONTRIBUTING.md). Key points:

- `snake_case` for all names
- Naming optimizes for longest common prefix (`number_small` / `number_big`, not `small_number` / `big_number`)
- Enum values uppercase, prefixed with enum name (`LLAMA_VOCAB_TYPE_BPE`)
- Method naming pattern: `<class>_<action>_<noun>` (e.g. `llama_sampler_chain_remove`)
- Avoid third-party dependencies and unnecessary headers
- Use `int32_t` and sized types in public APIs
- 4-space indentation, brackets on same line, `void * ptr`, `int & a`
- Vertical alignment for readability

---

## Upstream sync

When syncing from upstream, conflicts in `llama_gui/` and the root `CMakeLists.txt` GUI block must be resolved manually. All other conflicts should prefer upstream changes unless there is a specific fork reason to differ.

```bash
git remote add upstream https://github.com/ggml-org/llama.cpp
git fetch upstream
git merge upstream/master
```

---

## Documentation

- Keep `llama_gui/` code documented — docstrings on all classes and non-trivial functions
- Update `README.md` when adding new GUI features
- Incorrect or outdated docs should be fixed in the same PR as the related code change

---

## Resources

- Upstream project: https://github.com/ggml-org/llama.cpp
- ggml library: https://github.com/ggml-org/ggml
- dev-boffin-io org: https://github.com/dev-boffin-io
