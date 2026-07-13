from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QApplication


def system_prefers_dark() -> bool:
    app = QApplication.instance()
    if app is not None:
        try:
            scheme = app.styleHints().colorScheme()
            return scheme == Qt.ColorScheme.Dark
        except AttributeError:
            pass
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return int(value) == 0
    except OSError:
        return True


def resolve_theme(mode: str) -> str:
    if mode == "system":
        return "dark" if system_prefers_dark() else "light"
    return mode if mode in ("dark", "light") else "dark"


DARK = """
QWidget { color: #e8edf5; background: transparent; }
QMainWindow { background: #11141b; }
QFrame#Card {
    background: #1a1f2b;
    border: 1px solid #2d3548;
    border-radius: 14px;
}
QLabel { color: #e8edf5; }
QLabel#Title { font-size: 22px; font-weight: 800; color: #f8fafc; }
QLabel#Sub { color: #94a3b8; font-size: 12px; }
QLabel#Section { color: #cbd5e1; font-size: 13px; font-weight: 700; }
QLabel#Hint { color: #94a3b8; font-size: 11px; }
QLabel#Live { color: #38bdf8; font-family: Consolas; font-size: 12px; }
QLabel#Stats { color: #4ade80; font-size: 12px; font-weight: 600; }
QFrame#Chip {
    background: #232a38;
    border: 2px solid #3d465c;
    border-radius: 10px;
    min-height: 36px;
}
QFrame#Chip[active="true"] {
    background: #352560;
    border: 2px solid #8b5cf6;
}
QLabel#ChipNum { color: #c4b5fd; font-weight: 700; font-size: 11px; }
QLabel#ChipVal { color: #f1f5f9; font-family: Consolas; font-size: 11px; }
QTextEdit {
    background: #12161f;
    border: 1px solid #2d3548;
    border-radius: 10px;
    padding: 10px;
    color: #f1f5f9;
    font-family: Consolas;
    font-size: 11px;
    selection-background-color: #5b21b6;
}
QLineEdit {
    background: #12161f;
    border: 1px solid #3d465c;
    border-radius: 8px;
    padding: 8px 10px;
    color: #f8fafc;
    selection-background-color: #5b21b6;
}
QPushButton {
    background: #252d3d;
    border: 1px solid #3d465c;
    border-radius: 10px;
    padding: 8px 14px;
    color: #f1f5f9;
    font-weight: 600;
}
QPushButton:hover { background: #2f384c; border-color: #4b5568; }
QPushButton:checked, QPushButton#SplitOn {
    background: #6d28d9;
    border-color: #8b5cf6;
    color: #ffffff;
}
QPushButton#Ghost { background: transparent; color: #cbd5e1; }
QPushButton#Accent { background: #047857; border-color: #10b981; color: #fff; }
QPushButton#Accent:hover { background: #059669; }
QPushButton#Danger { background: #991b1b; border-color: #dc2626; color: #fff; }
QComboBox {
    background: #12161f;
    border: 1px solid #3d465c;
    border-radius: 8px;
    padding: 6px 10px;
    color: #f1f5f9;
}
QComboBox QAbstractItemView {
    background: #1a1f2b;
    color: #f1f5f9;
    selection-background-color: #5b21b6;
}
QListWidget {
    background: #12161f;
    border: 1px solid #2d3548;
    border-radius: 10px;
    color: #e2e8f0;
}
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: #1a1f2b; }
QWidget#ChipsHost { background: #1a1f2b; }
QSplitter::handle {
    background: #1a1f2b;
    width: 2px;
    margin: 8px 4px;
    border-radius: 1px;
}
QSplitter::handle:hover { background: #5b21b6; }
"""

LIGHT = """
QWidget { color: #1e293b; background: transparent; }
QMainWindow { background: #eef2f7; }
QFrame#Card {
    background: #ffffff;
    border: 1px solid #d8dee9;
    border-radius: 14px;
}
QLabel { color: #1e293b; }
QLabel#Title { font-size: 22px; font-weight: 800; color: #0f172a; }
QLabel#Sub { color: #64748b; font-size: 12px; }
QLabel#Section { color: #334155; font-size: 13px; font-weight: 700; }
QLabel#Hint { color: #64748b; font-size: 11px; }
QLabel#Live { color: #0369a1; font-family: Consolas; font-size: 12px; }
QLabel#Stats { color: #15803d; font-size: 12px; font-weight: 600; }
QFrame#Chip {
    background: #f8fafc;
    border: 2px solid #cbd5e1;
    border-radius: 10px;
    min-height: 36px;
}
QFrame#Chip[active="true"] {
    background: #ede9fe;
    border: 2px solid #7c3aed;
}
QLabel#ChipNum { color: #6d28d9; font-weight: 700; font-size: 11px; }
QLabel#ChipVal { color: #0f172a; font-family: Consolas; font-size: 11px; }
QTextEdit {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    padding: 10px;
    color: #0f172a;
    font-family: Consolas;
    font-size: 11px;
    selection-background-color: #a78bfa;
}
QLineEdit {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 10px;
    color: #0f172a;
    selection-background-color: #a78bfa;
}
QPushButton {
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    padding: 8px 14px;
    color: #1e293b;
    font-weight: 600;
}
QPushButton:hover { background: #e2e8f0; }
QPushButton:checked, QPushButton#SplitOn {
    background: #7c3aed;
    border-color: #6d28d9;
    color: #ffffff;
}
QPushButton#Ghost { background: transparent; color: #475569; }
QPushButton#Accent { background: #059669; border-color: #047857; color: #fff; }
QPushButton#Accent:hover { background: #10b981; }
QPushButton#Danger { background: #dc2626; border-color: #b91c1c; color: #fff; }
QComboBox {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 6px 10px;
    color: #1e293b;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    color: #1e293b;
    selection-background-color: #ddd6fe;
}
QListWidget {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    color: #1e293b;
}
QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: #ffffff; }
QWidget#ChipsHost { background: #ffffff; }
QSplitter::handle {
    background: #e2e8f0;
    width: 2px;
    margin: 8px 4px;
    border-radius: 1px;
}
QSplitter::handle:hover { background: #7c3aed; }
"""


def stylesheet_for(mode: str) -> str:
    return DARK if resolve_theme(mode) == "dark" else LIGHT


def apply_theme(app: QApplication, mode: str) -> str:
    resolved = resolve_theme(mode)
    app.setStyleSheet(stylesheet_for(mode))
    if resolved == "dark":
        app.setPalette(app.style().standardPalette())
    else:
        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window, pal.color(QPalette.ColorRole.Base))
        app.setPalette(pal)
    return resolved
