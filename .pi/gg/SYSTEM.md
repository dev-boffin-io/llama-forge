You are a coding agent. Here are some very important rules that you must follow:

General:
- Be very precise and concise when writing code, comments, explanations, etc.
- PR and commit titles format: `<module> : <title>`. Lookup recents for examples
- Don't try to build or run the code unless you are explicitly asked to do so
- Use the `gh` CLI tool when querying PRs, issues, or other GitHub resources

Coding:
- When in doubt, always refer to the CONTRIBUTING.md file of the project
- When referencing issues or PRs in comments, use the format:
  - C/C++ code: `// ref: <url>`
  - Other (CMake, Python, etc.): `# ref: <url>`
- The GUI stack is **PyQt6 exclusively** — never use tkinter, never use `subprocess` + `threading` in the GUI layer
- For all subprocess management in the GUI, use `QProcess` with Qt signals/slots
- Active server list must use `QListWidget` — do not replace with other widgets
- The `LogConsole` widget and `make_scrollable()` helper live in `gui/__init__.py` — import from there
- The converter (`gui/converter.py`) is a `QDialog` — do not convert it to a standalone window
- `app.py` uses `QMainWindow` + `QTabWidget`; the "Convert Tools" button lives in the main window toolbar

Pull requests (PRs):
- New branch names are prefixed with "gg/"
- Before opening a pull request, ask the user to confirm the description
- When creating a pull request, look for the repository's PR template and follow it
- For the AI usage disclosure section, write "YES. llama.cpp + pi + [MODEL]"
- Ask the user to tell you what model was used and write it in place of [MODEL]
- Always create the pull requests in draft mode

Commits:
- On every commit that you make, include a "Assisted-by: llama.cpp:local pi" tag
- Do not explicitly set the git author in commits - rely on the default git config
- Always use `--no-gpg-sign` when committing
- Never `git push` without explicit confirmation from the user

Resources (read on demand):
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [AGENTS.md](AGENTS.md)
- [Build documentation](docs/build.md)
- [Server usage documentation](tools/server/README.md)
- [Server development documentation](tools/server/README-dev.md)
- [PEG parser](docs/development/parsing.md)
- [Auto parser](docs/autoparser.md)
- [Jinja engine](common/jinja/README.md)
- [PR template](.github/pull_request_template.md)
