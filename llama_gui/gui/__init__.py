"""
gui/__init__.py — shared PyQt6 helpers, theme and widgets used across tabs.

Theme: a clean, modern dark UI ("Tokyo-Night"-inspired) applied app-wide via
a single QSS stylesheet, plus small helper widgets/functions used by every
tab (scrollable panels, a log console, etc).
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QPlainTextEdit, QGroupBox,
)
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import Qt


# ── Palette ──────────────────────────────────────────────────────────────────

class Colors:
    BG          = "#1a1b26"
    BG_ALT      = "#16161e"
    SURFACE     = "#24283b"
    SURFACE_ALT = "#2a2e44"
    BORDER      = "#3b4261"
    TEXT        = "#c0caf5"
    TEXT_DIM    = "#8a92b2"
    ACCENT      = "#7aa2f7"
    ACCENT_HOV  = "#9ab8ff"
    ACCENT_DOWN = "#5d7fd6"
    GREEN       = "#9ece6a"
    YELLOW      = "#e0af68"
    RED         = "#f7768e"
    CYAN        = "#7dcfff"
    LOG_BG      = "#11121a"
    LOG_FG      = "#9ece6a"


# ── App-wide stylesheet ──────────────────────────────────────────────────────

STYLE_SHEET = f"""
* {{
    outline: none;
}}

QMainWindow, QDialog {{
    background: {Colors.BG};
}}

QWidget {{
    color: {Colors.TEXT};
    font-size: 25px;
}}

QToolTip {{
    background: {Colors.SURFACE_ALT};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    padding: 11px;
    border-radius: 11px;
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {Colors.BORDER};
    border-radius: 18px;
    background: {Colors.BG};
    top: -1px;
}}

QTabBar::tab {{
    background: {Colors.SURFACE};
    color: {Colors.TEXT_DIM};
    padding: 18px 40px;
    margin-right: 7px;
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background: {Colors.BG};
    color: {Colors.ACCENT};
    border: 1px solid {Colors.BORDER};
    border-bottom: none;
}}

QTabBar::tab:hover:!selected {{
    color: {Colors.TEXT};
}}

/* Group boxes (cards) */
QGroupBox {{
    background: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: 18px;
    margin-top: 25px;
    padding: 25px 18px 18px 18px;
    font-weight: 600;
    color: {Colors.CYAN};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 22px;
    top: -4px;
    padding: 0 11px;
    background: {Colors.SURFACE};
}}

/* Inputs */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: {Colors.BG_ALT};
    border: 1px solid {Colors.BORDER};
    border-radius: 11px;
    padding: 9px 14px;
    color: {Colors.TEXT};
    selection-background-color: {Colors.ACCENT};
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {Colors.ACCENT};
}}

QLineEdit:read-only {{
    color: {Colors.TEXT_DIM};
}}

QComboBox::drop-down {{
    border: none;
    width: 40px;
}}

QComboBox QAbstractItemView {{
    background: {Colors.SURFACE_ALT};
    border: 1px solid {Colors.BORDER};
    selection-background-color: {Colors.ACCENT};
    selection-color: {Colors.BG};
    color: {Colors.TEXT};
    outline: none;
}}

/* Buttons */
QPushButton {{
    background: {Colors.SURFACE_ALT};
    border: 1px solid {Colors.BORDER};
    border-radius: 14px;
    padding: 14px 29px;
    font-weight: 600;
    color: {Colors.TEXT};
}}

QPushButton:hover {{
    border: 1px solid {Colors.ACCENT};
    color: {Colors.ACCENT_HOV};
}}

QPushButton:pressed {{
    background: {Colors.ACCENT_DOWN};
    color: {Colors.BG};
}}

QPushButton:disabled {{
    color: {Colors.TEXT_DIM};
    border: 1px solid {Colors.BORDER};
    background: {Colors.BG_ALT};
}}

QPushButton#PrimaryButton {{
    background: {Colors.ACCENT};
    border: 1px solid {Colors.ACCENT};
    color: {Colors.BG};
    font-weight: 700;
}}

QPushButton#PrimaryButton:hover {{
    background: {Colors.ACCENT_HOV};
    border: 1px solid {Colors.ACCENT_HOV};
}}

QPushButton#StopButton {{
    background: {Colors.RED};
    border: 1px solid {Colors.RED};
    color: {Colors.BG_ALT};
    font-weight: 700;
}}

QPushButton#StopButton:hover {{
    background: #ff8fa3;
}}

QPushButton#StopButton:disabled {{
    background: {Colors.BG_ALT};
    border: 1px solid {Colors.BORDER};
    color: {Colors.TEXT_DIM};
}}

/* Checkboxes */
QCheckBox {{
    spacing: 14px;
    padding: 4px;
}}

QCheckBox::indicator {{
    width: 29px;
    height: 29px;
    border: 1px solid {Colors.BORDER};
    border-radius: 7px;
    background: {Colors.BG_ALT};
}}

QCheckBox::indicator:checked {{
    background: {Colors.ACCENT};
    border: 1px solid {Colors.ACCENT};
}}

QCheckBox::indicator:hover {{
    border: 1px solid {Colors.ACCENT};
}}

/* Labels */
QLabel {{
    color: {Colors.TEXT};
}}

QLabel#Heading {{
    font-size: 29px;
    font-weight: 700;
    color: {Colors.ACCENT};
}}

QLabel#Muted {{
    color: {Colors.TEXT_DIM};
}}

QLabel#Banner {{
    background: {Colors.SURFACE_ALT};
    border: 1px solid {Colors.BORDER};
    border-radius: 14px;
    padding: 14px 22px;
    color: {Colors.CYAN};
    font-weight: 600;
}}

/* Scroll areas / bars */
QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    background: {Colors.BG};
    width: 22px;
    margin: 4px;
}}

QScrollBar::handle:vertical {{
    background: {Colors.BORDER};
    border-radius: 9px;
    min-height: 43px;
}}

QScrollBar::handle:vertical:hover {{
    background: {Colors.ACCENT};
}}

QScrollBar:horizontal {{
    background: {Colors.BG};
    height: 22px;
    margin: 4px;
}}

QScrollBar::handle:horizontal {{
    background: {Colors.BORDER};
    border-radius: 9px;
    min-width: 43px;
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0px;
    width: 0px;
}}

/* List widget (active servers) */
QListWidget {{
    background: {Colors.LOG_BG};
    border: 1px solid {Colors.BORDER};
    border-radius: 14px;
    color: {Colors.GREEN};
    padding: 7px;
}}

QListWidget::item {{
    padding: 7px 11px;
    border-radius: 7px;
}}

QListWidget::item:selected {{
    background: {Colors.ACCENT};
    color: {Colors.BG};
}}

/* Log console */
QPlainTextEdit#LogConsole {{
    background: {Colors.LOG_BG};
    color: {Colors.LOG_FG};
    border: 1px solid {Colors.BORDER};
    border-radius: 14px;
    padding: 14px;
    selection-background-color: {Colors.ACCENT};
    selection-color: {Colors.BG};
}}
"""


def monospace_font(size: int = 12) -> QFont:
    """Return the best available monospace font at the given point size."""
    families = QFontDatabase.families()
    for name in ("JetBrains Mono", "Cascadia Code", "Fira Code",
                  "DejaVu Sans Mono", "Consolas", "Monospace"):
        if name in families:
            f = QFont(name, size)
            f.setStyleHint(QFont.StyleHint.Monospace)
            return f
    f = QFont()
    f.setStyleHint(QFont.StyleHint.Monospace)
    f.setPointSize(size)
    return f


def make_scrollable(content: QWidget) -> QScrollArea:
    """Wrap *content* in a borderless, vertically-scrollable area."""
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    area.setWidget(content)
    return area


class LogConsole(QPlainTextEdit):
    """Dark, monospaced, read-only log console."""

    def __init__(self, parent: QWidget | None = None, height: int = 260):
        super().__init__(parent)
        self.setObjectName("LogConsole")
        self.setReadOnly(True)
        self.setFont(monospace_font(22))
        self.setMaximumBlockCount(5000)
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)


def append_log(widget: LogConsole, text: str) -> None:
    """Append *text* (no trailing newline needed) to the log console."""
    widget.appendPlainText(text.rstrip("\n"))
    sb = widget.verticalScrollBar()
    sb.setValue(sb.maximum())


def card(title: str) -> QGroupBox:
    """Create an empty styled QGroupBox; caller sets its layout."""
    return QGroupBox(title)
