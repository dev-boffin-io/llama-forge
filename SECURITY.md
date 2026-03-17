# Security Policy — llama-forge

- [Reporting a vulnerability](#reporting-a-vulnerability)
- [Covered scope](#covered-scope)
- [Using llama-forge securely](#using-llama-forge-securely)
  - [Untrusted models](#untrusted-models)
  - [Untrusted inputs](#untrusted-inputs)
  - [GUI security](#gui-security)
  - [Data privacy](#data-privacy)
  - [Untrusted environments or networks](#untrusted-environments-or-networks)

---

## Reporting a vulnerability

If you discover a security vulnerability within the **fork-specific code** of this project (see [Covered scope](#covered-scope) below), please report it privately by opening a [GitHub Security Advisory](https://github.com/dev-boffin-io/llama-forge/security/advisories/new) or by contacting the maintainer directly.

**Do not disclose it as a public issue.** This allows time to develop and release a fix before public exposure.

This project is maintained on a best-effort basis. Please allow at least **90 days** before any public disclosure.

> **Note:** For vulnerabilities in the core llama.cpp engine (`src/`, `ggml/`, `gguf-py/`, `tools/`), please report them directly to the upstream project at:
> https://github.com/ggml-org/llama.cpp/security/advisories/new

---

## Covered scope

Security reports for this fork are accepted only for **fork-specific code**:

- `llama_gui/` — the desktop GUI application
  - `llama_gui/core/` — project detection, config persistence
  - `llama_gui/gui/` — Tkinter UI components
  - `llama_gui/utils/` — terminal launch, subprocess streaming, GGUF reading
  - `llama_gui/CMakeLists.txt` — build system

Everything outside `llama_gui/` is upstream code. Security issues in those areas should be reported to [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp/security/advisories/new).

---

## Using llama-forge securely

### Untrusted models

Exercise caution when loading GGUF files from unknown sources. Always run untrusted models inside an isolated environment (container, VM, or sandbox) to limit the blast radius of any malicious content embedded in the model file.

> The trustworthiness of a model is not binary. Assess risk based on the source, intended use, and your own tolerance.

### Untrusted inputs

Models that accept text, images, or audio inputs may be vulnerable to prompt injection or adversarial inputs depending on the underlying libraries. When handling untrusted inputs:

- Sandbox the inference environment
- Sanitize and validate inputs before passing them to the model
- Keep llama-forge and all dependencies up to date
- Test model behavior against known prompt injection patterns before deploying

### GUI security

The `llama_gui/` desktop application introduces its own attack surface:

- **Config file** — user settings are stored at `~/.llama_cpp_gui.json`. This file is read and written without encryption. Do not store secrets there.
- **Terminal launch** — the GUI constructs shell commands and passes them to a terminal emulator. Paths containing shell metacharacters in model filenames could lead to command injection. Always use model files from trusted sources.
- **GGUF metadata** — the GGUF info reader (`utils/gguf_info.py`) parses binary file headers. Malformed or crafted GGUF files could trigger parser errors. The reader is designed to fail safely, but untrusted GGUF files should be treated with the same caution as untrusted executables.
- **subprocess streaming** — conversion and quantization commands are run as subprocesses. The GUI does not sanitize user-supplied extra arguments before passing them to the subprocess. Do not paste untrusted argument strings into the Extra Arguments field.

### Data privacy

Model inference happens locally. No data is sent over the network by the GUI. However:

- If using `llama-server` via the upstream CLI tools, network exposure rules apply — see the upstream security guidance.
- The config file at `~/.llama_cpp_gui.json` stores absolute paths to your model files. Be aware of this if the machine is shared.

### Untrusted environments or networks

If running inference in an environment exposed to an untrusted network:

- Do not expose `llama-server` without authentication or a firewall rule
- Verify checksums of downloaded model files before loading them
- Encrypt any data transmitted over the network
- Do not use the RPC backend in untrusted network environments
