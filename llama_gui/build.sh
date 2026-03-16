#!/usr/bin/env bash
# llama_gui Release Builder
# Builds a onefile binary and places it one level above gui/ (llama.cpp root).

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

APP_NAME="llama-gui"
ENTRY="$SCRIPT_DIR/app.py"

GREEN="\033[1;32m"; YELLOW="\033[1;33m"; RED="\033[1;31m"
CYAN="\033[1;36m";  MAGENTA="\033[1;35m"; NC="\033[0m"

echo -e "${CYAN}======================================${NC}"
echo -e "${MAGENTA}   llama.cpp GUI — Release Builder    ${NC}"
echo -e "${CYAN}======================================${NC}"
echo -e "${CYAN}gui/         :${NC} $SCRIPT_DIR"
echo -e "${CYAN}Project root :${NC} $PROJECT_ROOT"
echo -e "${CYAN}Binary dest  :${NC} $PROJECT_ROOT/$APP_NAME"
echo

# Sanity check
if [[ ! -f "$PROJECT_ROOT/CMakeLists.txt" ]] || \
   [[ ! -f "$PROJECT_ROOT/convert_hf_to_gguf.py" ]]; then
    echo -e "${RED}❌ Cannot confirm llama.cpp root at $PROJECT_ROOT${NC}"
    exit 1
fi

# Python
PYTHON_BIN=""
for p in python3 python; do
    if command -v "$p" &>/dev/null; then PYTHON_BIN="$p"; break; fi
done
[[ -z "$PYTHON_BIN" ]] && { echo -e "${RED}❌ Python not found${NC}"; exit 1; }
echo -e "${GREEN}✔ Python:${NC} $($PYTHON_BIN --version)"

"$PYTHON_BIN" -m venv --help &>/dev/null || {
    echo -e "${RED}❌ python3-venv missing — sudo apt install python3-venv${NC}"; exit 1; }
"$PYTHON_BIN" -c "import tkinter" &>/dev/null || {
    echo -e "${RED}❌ tkinter missing — sudo apt install python3-tk${NC}"; exit 1; }

# Clean
echo -e "${CYAN}🧹 Cleaning build artefacts inside gui/...${NC}"
rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/dist" "$SCRIPT_DIR/__pycache__" \
       "$SCRIPT_DIR"/*.spec "$SCRIPT_DIR/llama_gui"/__pycache__ || true

# venv
VENV="$SCRIPT_DIR/.venv"
echo -e "${CYAN}🐍 Creating venv...${NC}"
"$PYTHON_BIN" -m venv "$VENV"
PIP="$VENV/bin/pip"
PY="$VENV/bin/python"

echo -e "${CYAN}📦 Installing PyInstaller...${NC}"
"$PIP" install --upgrade pip --quiet
"$PIP" install pyinstaller --quiet
echo -e "${GREEN}✔ PyInstaller ready${NC}"

# Build
echo
echo -e "${GREEN}🚀 Building binary...${NC}"
"$PY" -m PyInstaller \
    --onefile \
    --windowed \
    --clean \
    --noconfirm \
    --distpath "$SCRIPT_DIR/dist" \
    --workpath "$SCRIPT_DIR/build" \
    --name "$APP_NAME" \
    --paths "$SCRIPT_DIR" \
    "$ENTRY"

# Place binary at project root
BUILT="$SCRIPT_DIR/dist/$APP_NAME"
DEST="$PROJECT_ROOT/$APP_NAME"

[[ -f "$BUILT" ]] || {
    echo -e "${RED}❌ Build failed — binary not found${NC}"
    rm -rf "$VENV"; exit 1; }

[[ -f "$DEST" ]] && {
    echo -e "${YELLOW}🗑  Removing old binary: $DEST${NC}"
    rm -f "$DEST"; }

echo -e "${CYAN}➜ Moving binary to project root...${NC}"
mv -f "$BUILT" "$DEST"
chmod +x "$DEST"

# Cleanup
echo -e "${CYAN}🧼 Removing build artefacts...${NC}"
rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/dist" "$SCRIPT_DIR/__pycache__" \
       "$SCRIPT_DIR"/*.spec || true
rm -rf "$VENV"

echo
echo -e "${GREEN}✅ Done!${NC}"
echo -e "${CYAN}Binary:${NC} $DEST"
echo
