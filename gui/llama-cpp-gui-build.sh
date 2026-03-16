#!/usr/bin/env bash
# llama.cpp Manager - Release Builder
# Binary is placed ONE level above gui/ (i.e. the llama.cpp project root).

set -Eeuo pipefail

# ==============================
# CONFIG
# ==============================
APP_NAME="llama_cpp_manager"
ENTRY_FILE="llama_cpp_manager.py"

# gui/ directory (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# llama.cpp project root = one level above gui/
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Sanity-check: make sure we really are inside the llama.cpp tree
if [[ ! -f "$PROJECT_ROOT/CMakeLists.txt" ]] || [[ ! -f "$PROJECT_ROOT/convert_hf_to_gguf.py" ]]; then
    echo -e "\033[1;31m❌ Cannot confirm llama.cpp project root at: $PROJECT_ROOT\033[0m"
    echo -e "\033[1;33m   Expected CMakeLists.txt and convert_hf_to_gguf.py to exist there.\033[0m"
    exit 1
fi

# Build artifacts stay inside gui/ (never pollute the llama.cpp root)
BUILD_DIR="$SCRIPT_DIR"
VENV_DIR="$BUILD_DIR/.venv"

# ==============================
# COLORS
# ==============================
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
CYAN="\033[1;36m"
MAGENTA="\033[1;35m"
NC="\033[0m"

echo -e "${CYAN}====================================${NC}"
echo -e "${MAGENTA}  llama.cpp Manager Release Build  ${NC}"
echo -e "${CYAN}====================================${NC}"
echo
echo -e "${CYAN}gui/ dir    :${NC} $SCRIPT_DIR"
echo -e "${CYAN}Project root:${NC} $PROJECT_ROOT"
echo -e "${CYAN}Binary dest :${NC} $PROJECT_ROOT/$APP_NAME"
echo

# ==============================
# Detect python binary
# ==============================
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo -e "${RED}❌ Python not found. Please install python3.${NC}"
    exit 1
fi
echo -e "${GREEN}✔ Python found:${NC} $($PYTHON_BIN --version)"

# ==============================
# Check python3-venv / venv module
# ==============================
if ! "$PYTHON_BIN" -m venv --help &>/dev/null; then
    echo -e "${RED}❌ python3-venv not available.${NC}"
    echo -e "${YELLOW}   On Debian/Ubuntu: sudo apt install python3-venv${NC}"
    exit 1
fi
echo -e "${GREEN}✔ venv module available.${NC}"

# ==============================
# Check tkinter availability
# ==============================
if ! "$PYTHON_BIN" -c "import tkinter" &>/dev/null; then
    echo -e "${RED}❌ tkinter not available.${NC}"
    echo -e "${YELLOW}   On Debian/Ubuntu: sudo apt install python3-tk${NC}"
    exit 1
fi
echo -e "${GREEN}✔ tkinter available.${NC}"

# ==============================
# Clean old build artifacts inside gui/
# ==============================
echo
echo -e "${CYAN}🧹 Cleaning old build files inside gui/...${NC}"
rm -rf "$BUILD_DIR/build" "$BUILD_DIR/dist" "$BUILD_DIR/__pycache__" "$BUILD_DIR"/*.spec || true

# ==============================
# Create .venv inside gui/
# ==============================
echo
echo -e "${CYAN}🐍 Creating virtual environment...${NC}"
"$PYTHON_BIN" -m venv "$VENV_DIR"
VENV_PIP="$VENV_DIR/bin/pip"
VENV_PYTHON="$VENV_DIR/bin/python"

# ==============================
# Install PyInstaller inside venv
# ==============================
echo -e "${CYAN}📦 Installing PyInstaller...${NC}"
"$VENV_PIP" install --upgrade pip --quiet
"$VENV_PIP" install pyinstaller --quiet
echo -e "${GREEN}✔ PyInstaller installed.${NC}"

# ==============================
# Build (distpath inside gui/ so we never touch llama.cpp root during build)
# ==============================
echo
echo -e "${GREEN}🚀 Building binary...${NC}"

"$VENV_PYTHON" -m PyInstaller \
    --onefile \
    --windowed \
    --clean \
    --noconfirm \
    --distpath "$BUILD_DIR/dist" \
    --workpath "$BUILD_DIR/build" \
    --name "$APP_NAME" \
    "$BUILD_DIR/$ENTRY_FILE"

# ==============================
# Move binary one level up → llama.cpp project root
# ==============================
BUILT_BIN="$BUILD_DIR/dist/$APP_NAME"
DEST_BIN="$PROJECT_ROOT/$APP_NAME"

if [[ ! -f "$BUILT_BIN" ]]; then
    echo -e "${RED}❌ Build failed. Binary not found: $BUILT_BIN${NC}"
    rm -rf "$VENV_DIR"
    exit 1
fi

# Check for existing binary at destination
if [[ -f "$DEST_BIN" ]]; then
    echo -e "${YELLOW}🗑  Removing old binary at project root: $DEST_BIN${NC}"
    rm -f "$DEST_BIN"
fi

echo -e "${CYAN}➜ Moving binary to project root: $DEST_BIN${NC}"
mv -f "$BUILT_BIN" "$DEST_BIN"
chmod +x "$DEST_BIN"

# ==============================
# Final Cleanup (gui/ only)
# ==============================
echo
echo -e "${CYAN}🧼 Removing build artifacts from gui/...${NC}"
rm -rf "$BUILD_DIR/build" "$BUILD_DIR/dist" "$BUILD_DIR/__pycache__" "$BUILD_DIR"/*.spec || true

echo -e "${CYAN}🗑  Removing virtual environment...${NC}"
rm -rf "$VENV_DIR"

echo
echo -e "${GREEN}✅ Release Ready!${NC}"
echo -e "${CYAN}Binary Location:${NC} $DEST_BIN"
echo
