cmake_minimum_required(VERSION 3.16)
project(llama_gui_builder NONE)

# ── Paths ─────────────────────────────────────────────────────────────────
set(APP_NAME   "llama-gui")
set(SCRIPT_DIR "${CMAKE_CURRENT_SOURCE_DIR}")
set(ENTRY      "${SCRIPT_DIR}/app.py")
set(BUILD_DIR  "${SCRIPT_DIR}/_pyinstaller_build")
set(DIST_DIR   "${SCRIPT_DIR}/_pyinstaller_dist")
set(VENV_DIR   "${SCRIPT_DIR}/.venv")

get_filename_component(PROJECT_ROOT "${SCRIPT_DIR}" DIRECTORY)
set(DEST_BIN "${PROJECT_ROOT}/${APP_NAME}")

# ── Python ────────────────────────────────────────────────────────────────
find_program(PYTHON_BIN NAMES python3 python REQUIRED)
message(STATUS "Python      : ${PYTHON_BIN}")
message(STATUS "gui/        : ${SCRIPT_DIR}")
message(STATUS "Project root: ${PROJECT_ROOT}")
message(STATUS "Binary dest : ${DEST_BIN}")

# ── Sanity: confirm we are inside the llama.cpp tree ─────────────────────
if(NOT EXISTS "${PROJECT_ROOT}/CMakeLists.txt")
    message(FATAL_ERROR
        "CMakeLists.txt not found at project root: ${PROJECT_ROOT}\n"
        "Is llama-gui/ inside the llama.cpp source tree?")
endif()
if(NOT EXISTS "${PROJECT_ROOT}/convert_hf_to_gguf.py")
    message(FATAL_ERROR
        "convert_hf_to_gguf.py not found at project root: ${PROJECT_ROOT}\n"
        "Is llama-gui/ inside the llama.cpp source tree?")
endif()

# ── tkinter check ─────────────────────────────────────────────────────────
execute_process(
    COMMAND "${PYTHON_BIN}" -c "import tkinter"
    RESULT_VARIABLE _tk_result
)
if(NOT _tk_result EQUAL 0)
    message(FATAL_ERROR
        "tkinter not available.\n"
        "  Debian/Ubuntu: sudo apt install python3-tk")
endif()
message(STATUS "tkinter     : OK")

# ── venv module check ─────────────────────────────────────────────────────
execute_process(
    COMMAND "${PYTHON_BIN}" -m venv --help
    RESULT_VARIABLE _venv_result
    OUTPUT_QUIET ERROR_QUIET
)
if(NOT _venv_result EQUAL 0)
    message(FATAL_ERROR
        "python3-venv not available.\n"
        "  Debian/Ubuntu: sudo apt install python3-venv")
endif()
message(STATUS "venv module : OK")

# ── Clean old artefacts ───────────────────────────────────────────────────
message(STATUS "Cleaning old build artefacts...")
file(REMOVE_RECURSE
    "${BUILD_DIR}"
    "${DIST_DIR}"
    "${VENV_DIR}"
    "${SCRIPT_DIR}/__pycache__"
)
file(GLOB _old_specs "${SCRIPT_DIR}/*.spec")
if(_old_specs)
    file(REMOVE ${_old_specs})
endif()

# ── Create venv ───────────────────────────────────────────────────────────
message(STATUS "Creating virtual environment...")
execute_process(
    COMMAND "${PYTHON_BIN}" -m venv "${VENV_DIR}"
    RESULT_VARIABLE _venv_create
)
if(NOT _venv_create EQUAL 0)
    message(FATAL_ERROR "Failed to create virtual environment at: ${VENV_DIR}")
endif()

set(VENV_PIP    "${VENV_DIR}/bin/pip")
set(VENV_PYTHON "${VENV_DIR}/bin/python")

# ── Upgrade pip ───────────────────────────────────────────────────────────
execute_process(
    COMMAND "${VENV_PIP}" install --upgrade pip --quiet
    RESULT_VARIABLE _pip_upgrade
)
if(NOT _pip_upgrade EQUAL 0)
    message(FATAL_ERROR "pip upgrade failed.")
endif()

# ── Install PyInstaller ───────────────────────────────────────────────────
message(STATUS "Installing PyInstaller...")
execute_process(
    COMMAND "${VENV_PIP}" install pyinstaller --quiet
    RESULT_VARIABLE _pi_install
)
if(NOT _pi_install EQUAL 0)
    message(FATAL_ERROR "PyInstaller installation failed.")
endif()
message(STATUS "PyInstaller : OK")

# ── Build with PyInstaller ────────────────────────────────────────────────
# CMake list = no shell quoting issues, no line-continuation bug
message(STATUS "Building binary...")
set(_pi_args
    -m PyInstaller
    --onefile
    --clean
    --noconfirm
    --distpath "${DIST_DIR}"
    --workpath "${BUILD_DIR}"
    --name     "${APP_NAME}"
    --paths    "${SCRIPT_DIR}"
    "${ENTRY}"
)

execute_process(
    COMMAND "${VENV_PYTHON}" ${_pi_args}
    WORKING_DIRECTORY "${SCRIPT_DIR}"
    RESULT_VARIABLE _build_result
)
if(NOT _build_result EQUAL 0)
    file(REMOVE_RECURSE "${VENV_DIR}")
    message(FATAL_ERROR "PyInstaller build failed (exit code: ${_build_result})")
endif()

# ── Verify binary ─────────────────────────────────────────────────────────
set(_built_bin "${DIST_DIR}/${APP_NAME}")
if(NOT EXISTS "${_built_bin}")
    file(REMOVE_RECURSE "${VENV_DIR}")
    message(FATAL_ERROR "Build completed but binary not found: ${_built_bin}")
endif()

# ── Move binary to project root ───────────────────────────────────────────
message(STATUS "Moving binary to: ${DEST_BIN}")
if(EXISTS "${DEST_BIN}")
    file(REMOVE "${DEST_BIN}")
endif()

# file(RENAME) across filesystems can fail — use copy + remove instead
file(COPY_FILE "${_built_bin}" "${DEST_BIN}")
file(REMOVE "${_built_bin}")

# chmod +x  (file(CHMOD) needs CMake >= 3.19; use execute_process for compatibility)
execute_process(COMMAND chmod +x "${DEST_BIN}")

# ── Final cleanup ─────────────────────────────────────────────────────────
message(STATUS "Cleaning up...")
file(REMOVE_RECURSE
    "${BUILD_DIR}"
    "${DIST_DIR}"
    "${VENV_DIR}"
    "${SCRIPT_DIR}/__pycache__"
)
file(GLOB _specs "${SCRIPT_DIR}/*.spec")
if(_specs)
    file(REMOVE ${_specs})
endif()

# ── Desktop entry ─────────────────────────────────────────────────────────
# Icon: use llama_gui.png from llama-gui/ source dir
set(ICON_SRC "${SCRIPT_DIR}/llama_gui.png")
set(ICON_DEST "$ENV{HOME}/.local/share/icons/llama-gui.png")
set(DESKTOP_DIR "$ENV{HOME}/.local/share/applications")
set(DESKTOP_FILE "${DESKTOP_DIR}/llama-gui.desktop")

message(STATUS "Installing desktop entry...")

# Remove old desktop entry and icon if they exist
if(EXISTS "${DESKTOP_FILE}")
    file(REMOVE "${DESKTOP_FILE}")
    message(STATUS "Removed old desktop entry: ${DESKTOP_FILE}")
endif()
if(EXISTS "${ICON_DEST}")
    file(REMOVE "${ICON_DEST}")
    message(STATUS "Removed old icon: ${ICON_DEST}")
endif()

# Copy icon to ~/.local/share/icons/
if(EXISTS "${ICON_SRC}")
    file(MAKE_DIRECTORY "$ENV{HOME}/.local/share/icons")
    file(COPY_FILE "${ICON_SRC}" "${ICON_DEST}")
    message(STATUS "Icon installed : ${ICON_DEST}")
else()
    # fallback: use a standard system icon
    set(ICON_DEST "utilities-terminal")
    message(STATUS "llama_gui.png not found — using fallback icon: ${ICON_DEST}")
endif()

# Write .desktop file
file(MAKE_DIRECTORY "${DESKTOP_DIR}")
file(WRITE "${DESKTOP_FILE}"
"[Desktop Entry]
Version=1.0
Type=Application
Name=llama.cpp GUI
GenericName=LLM Manager
Comment=llama.cpp Tools — Chat, Quantize, Convert
Exec=${DEST_BIN}
Icon=${ICON_DEST}
Terminal=false
Categories=Science;Education;Utility;
Keywords=llm;llama;ai;gguf;quantize;
StartupWMClass=llama-gui
StartupNotify=true
")

# Mark as trusted (required on some desktops e.g. XFCE)
execute_process(
    COMMAND chmod +x "${DESKTOP_FILE}"
    RESULT_VARIABLE _chmod_desktop
)

# Refresh desktop database if gio or update-desktop-database available
find_program(_GIO gio)
find_program(_UDD update-desktop-database)
if(_GIO)
    execute_process(
        COMMAND "${_GIO}" set "${DESKTOP_FILE}" metadata::trusted true
        RESULT_VARIABLE _gio_result
        OUTPUT_QUIET ERROR_QUIET
    )
endif()
if(_UDD)
    execute_process(
        COMMAND "${_UDD}" "${DESKTOP_DIR}"
        OUTPUT_QUIET ERROR_QUIET
    )
endif()

message(STATUS "Desktop entry : ${DESKTOP_FILE}")

# ── Summary ───────────────────────────────────────────────────────────────
message(STATUS "")
message(STATUS "Build complete!")
message(STATUS "  Binary       : ${DEST_BIN}")
message(STATUS "  Desktop entry: ${DESKTOP_FILE}")
message(STATUS "  Icon         : ${ICON_DEST}")
message(STATUS "")
