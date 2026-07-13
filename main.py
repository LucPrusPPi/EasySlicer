from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QSettings, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from engine import Recipe, detect_parts, process_text, transform_line
from store import load_recipes, save_recipes
from themes import apply_theme


class Card(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Card")


class FieldChip(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, index: int, value: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.index = index
        self._order = 0
        self.setObjectName("Chip")
        self.setProperty("active", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(2)
        self.lbl_num = QLabel(f"Поле {index + 1}")
        self.lbl_num.setObjectName("ChipNum")
        val = value if len(value) <= 28 else value[:25] + "…"
        self.lbl_val = QLabel(val)
        self.lbl_val.setObjectName("ChipVal")
        self.lbl_val.setToolTip(value)
        lay.addWidget(self.lbl_num)
        lay.addWidget(self.lbl_val)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)
        super().mousePressEvent(event)

    def set_active(self, active: bool, order: int = 0) -> None:
        self._order = order
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        if active and order > 0:
            self.lbl_num.setText(f"#{order} · Поле {self.index + 1}")
        else:
            self.lbl_num.setText(f"Поле {self.index + 1}")


class EasySlicerApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EasySlicer")
        self.resize(1240, 760)

        self.settings = QSettings("EasySlicer", "EasySlicer")
        self._theme_mode = str(self.settings.value("theme", "system"))

        self._input_path: Path | None = None
        self._output: list[str] = []
        self._recipes = load_recipes()
        self._field_order: list[int] = []
        self._chips: list[FieldChip] = []
        self._split_btns: list[QPushButton] = []

        self._build()
        self._apply_theme(self._theme_mode)
        self._pick_split(":")
        self._refresh_all()

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("Section")
        return lbl

    def _apply_theme(self, mode: str) -> None:
        self._theme_mode = mode
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, mode)
        self.settings.setValue("theme", mode)
        idx = {"system": 0, "light": 1, "dark": 2}.get(mode, 0)
        if hasattr(self, "combo_theme"):
            self.combo_theme.blockSignals(True)
            self.combo_theme.setCurrentIndex(idx)
            self.combo_theme.blockSignals(False)

    def _build(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(14)

        head = QHBoxLayout()
        brand = QVBoxLayout()
        t = QLabel("EasySlicer")
        t.setObjectName("Title")
        sub = QLabel("Кликай по полям · собери строку блоками · сразу видишь результат")
        sub.setObjectName("Sub")
        brand.addWidget(t)
        brand.addWidget(sub)
        head.addLayout(brand, 1)

        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Системная", "Светлая", "Тёмная"])
        self.combo_theme.setFixedWidth(130)
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        head.addWidget(self.combo_theme)

        for label, slot, style in [
            ("Открыть", self.open_file, ""),
            ("Сохранить", self.save_output, ""),
            ("Копировать", self.copy_output, "Accent"),
        ]:
            b = QPushButton(label)
            if style:
                b.setObjectName(style)
            b.clicked.connect(slot)
            head.addWidget(b)
        outer.addLayout(head)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)

        # --- LEFT: input ---
        left = Card()
        ll = QVBoxLayout(left)
        ll.addWidget(self._section("Исходный текст"))
        self.txt_in = QTextEdit()
        self.txt_in.setPlaceholderText("Вставь строки или открой .txt…")
        self.txt_in.textChanged.connect(self._refresh_all)
        ll.addWidget(self.txt_in)
        splitter.addWidget(left)

        # --- CENTER: block builder ---
        mid = Card()
        ml = QVBoxLayout(mid)
        ml.setSpacing(10)

        ml.addWidget(self._section("① Разделитель входа"))
        split_row = QHBoxLayout()
        self.split_group = QButtonGroup(self)
        self.split_group.setExclusive(True)
        for sym, label in [(":", ":"), (";", ";"), ("|", "|"), ("\t", "Tab"), (" ", "Пробел")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("sym", sym)
            if sym == ":":
                btn.setObjectName("SplitOn")
            self.split_group.addButton(btn)
            self._split_btns.append(btn)
            btn.clicked.connect(lambda _=False, s=sym: self._pick_split(s))
            split_row.addWidget(btn)
        self.edt_custom_split = QLineEdit()
        self.edt_custom_split.setPlaceholderText("свой…")
        self.edt_custom_split.setMaximumWidth(64)
        self.edt_custom_split.textChanged.connect(self._on_custom_split)
        split_row.addWidget(self.edt_custom_split)
        split_row.addStretch()
        ml.addLayout(split_row)

        ml.addWidget(self._section("② Кликни поля — порядок кликов = порядок в строке"))
        self.hint = QLabel("Открой файл или вставь строку — появятся блоки полей")
        self.hint.setObjectName("Hint")
        ml.addWidget(self.hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.chips_host = QWidget()
        self.chips_host.setObjectName("ChipsHost")
        self.chips_row = QHBoxLayout(self.chips_host)
        self.chips_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.chips_row.setSpacing(8)
        scroll.setWidget(self.chips_host)
        scroll.setMinimumHeight(110)
        ml.addWidget(scroll)

        ml.addWidget(self._section("③ Склейка между полями"))
        join_row = QHBoxLayout()
        self.join_group = QButtonGroup(self)
        self.join_group.setExclusive(True)
        for sym, label in [(";", ";"), (":", ":"), ("|", "|"), (",", ","), ("\t", "Tab")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("sym", sym)
            if sym == ";":
                btn.setChecked(True)
            self.join_group.addButton(btn)
            btn.clicked.connect(lambda _=False, s=sym: self._pick_join(s))
            join_row.addWidget(btn)
        self.edt_custom_join = QLineEdit()
        self.edt_custom_join.setPlaceholderText("свой…")
        self.edt_custom_join.setMaximumWidth(64)
        self.edt_custom_join.textChanged.connect(self._on_custom_join)
        join_row.addWidget(self.edt_custom_join)
        join_row.addStretch()
        ml.addLayout(join_row)

        opt_row = QHBoxLayout()
        self.btn_dedupe = QPushButton("Без дубликатов")
        self.btn_dedupe.setCheckable(True)
        self.btn_dedupe.setChecked(True)
        self.btn_dedupe.clicked.connect(self._refresh_all)
        self.btn_reset = QPushButton("Сбросить выбор")
        self.btn_reset.setObjectName("Ghost")
        self.btn_reset.clicked.connect(self._reset_fields)
        opt_row.addWidget(self.btn_dedupe)
        opt_row.addWidget(self.btn_reset)
        opt_row.addStretch()
        ml.addLayout(opt_row)

        ml.addWidget(self._section("Живое превью (первая строка)"))
        self.lbl_live = QLabel("—")
        self.lbl_live.setObjectName("Live")
        self.lbl_live.setWordWrap(True)
        ml.addWidget(self.lbl_live)

        self.lbl_stats = QLabel("")
        self.lbl_stats.setObjectName("Stats")
        ml.addWidget(self.lbl_stats)

        recipe_row = QHBoxLayout()
        self.edt_recipe_name = QLineEdit()
        self.edt_recipe_name.setPlaceholderText("Имя шаблона")
        self.btn_save_recipe = QPushButton("Сохранить шаблон")
        self.btn_save_recipe.clicked.connect(self.save_recipe)
        recipe_row.addWidget(self.edt_recipe_name, 1)
        recipe_row.addWidget(self.btn_save_recipe)
        ml.addLayout(recipe_row)

        splitter.addWidget(mid)

        # --- RIGHT: output + saved ---
        right = Card()
        rl = QVBoxLayout(right)
        rl.addWidget(self._section("Результат"))
        self.txt_out = QTextEdit()
        self.txt_out.setReadOnly(True)
        rl.addWidget(self.txt_out, 1)

        rl.addWidget(self._section("Мои шаблоны"))
        self.list_recipes = QListWidget()
        self.list_recipes.setMaximumHeight(120)
        self.list_recipes.itemClicked.connect(self._load_recipe_item)
        rl.addWidget(self.list_recipes)
        del_row = QHBoxLayout()
        self.btn_del_recipe = QPushButton("Удалить")
        self.btn_del_recipe.setObjectName("Danger")
        self.btn_del_recipe.clicked.connect(self.delete_recipe)
        del_row.addStretch()
        del_row.addWidget(self.btn_del_recipe)
        rl.addLayout(del_row)
        splitter.addWidget(right)

        splitter.setSizes([360, 420, 380])
        outer.addWidget(splitter, 1)

        self._split_char = ":"
        self._join_char = ";"
        self._reload_recipe_list()

    def _on_theme_changed(self, index: int) -> None:
        mode = {0: "system", 1: "light", 2: "dark"}.get(index, "system")
        self._apply_theme(mode)

    def _recipe(self) -> Recipe:
        return Recipe(
            name=self.edt_recipe_name.text().strip() or "Мой шаблон",
            split_char=self._split_char,
            field_order=list(self._field_order),
            join_char=self._join_char,
            dedupe_first=self.btn_dedupe.isChecked(),
        )

    def _sample_line(self) -> str:
        for raw in self.txt_in.toPlainText().splitlines():
            if raw.strip():
                return raw.strip()
        return ""

    def _pick_split(self, sym: str) -> None:
        self._split_char = sym
        for btn in self._split_btns:
            on = btn.property("sym") == sym
            btn.setChecked(on)
            btn.setObjectName("SplitOn" if on else "")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._rebuild_chips()
        self._refresh_all()

    def _pick_join(self, sym: str) -> None:
        self._join_char = sym
        self._refresh_all()

    def _on_custom_split(self, text: str) -> None:
        if text:
            self._split_char = text[:8]
            for btn in self._split_btns:
                btn.setChecked(False)
            self._rebuild_chips()
            self._refresh_all()

    def _on_custom_join(self, text: str) -> None:
        if text:
            self._join_char = text[:8]
            self._refresh_all()

    def _rebuild_chips(self) -> None:
        while self.chips_row.count():
            item = self.chips_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._chips.clear()

        parts = detect_parts(self._sample_line(), self._split_char)
        if not parts:
            self.hint.setText("Нет строки для разбора — вставь текст слева")
            return

        self.hint.setText(f"Найдено полей: {len(parts)} · клик = добавить в выход")
        for i, val in enumerate(parts):
            chip = FieldChip(i, val)
            chip.clicked.connect(self._toggle_field)
            self._chips.append(chip)
            self.chips_row.addWidget(chip)
        self._sync_chip_visuals()

    def _toggle_field(self, index: int) -> None:
        if index in self._field_order:
            self._field_order.remove(index)
        else:
            self._field_order.append(index)
        self._sync_chip_visuals()
        self._refresh_all()

    def _reset_fields(self) -> None:
        self._field_order.clear()
        self._sync_chip_visuals()
        self._refresh_all()

    def _sync_chip_visuals(self) -> None:
        order_map = {idx: pos + 1 for pos, idx in enumerate(self._field_order)}
        for chip in self._chips:
            chip.set_active(chip.index in self._field_order, order_map.get(chip.index, 0))

    def _refresh_all(self) -> None:
        if not self._chips:
            self._rebuild_chips()

        recipe = self._recipe()
        sample = self._sample_line()
        if sample and recipe.field_order:
            preview = transform_line(sample, recipe)
            self.lbl_live.setText(preview or "— не собралось, проверь поля —")
        elif not recipe.field_order:
            self.lbl_live.setText("Выбери хотя бы одно поле блоком ↑")
        else:
            self.lbl_live.setText("—")

        lines, stats = process_text(self.txt_in.toPlainText(), recipe)
        self._output = lines
        self.txt_out.setPlainText("\n".join(lines))
        self.lbl_stats.setText(
            f"Вход {stats['input']} → выход {stats['output']} · "
            f"пропуск {stats['skipped']} · дубли {stats['duplicates']}"
        )

    def _reload_recipe_list(self) -> None:
        self.list_recipes.clear()
        for r in self._recipes:
            fields = " → ".join(str(i + 1) for i in r.field_order)
            self.list_recipes.addItem(
                QListWidgetItem(f"{r.name}  [{r.split_char} → {r.join_char}]  {fields}")
            )

    def _load_recipe_item(self, item: QListWidgetItem) -> None:
        idx = self.list_recipes.row(item)
        if idx < 0 or idx >= len(self._recipes):
            return
        r = self._recipes[idx]
        self.edt_recipe_name.setText(r.name)
        self._field_order = list(r.field_order)
        self._pick_split(r.split_char if r.split_char != "\t" else "\t")
        if r.join_char:
            self._join_char = r.join_char
        self.btn_dedupe.setChecked(r.dedupe_first)
        self._sync_chip_visuals()
        self._refresh_all()

    def save_recipe(self) -> None:
        r = self._recipe()
        if not r.field_order:
            QMessageBox.warning(self, "Шаблон", "Сначала кликни поля в конструкторе.")
            return
        name, ok = QInputDialog.getText(self, "Имя", "Название шаблона:", text=r.name)
        if not ok or not name.strip():
            return
        r.name = name.strip()
        replaced = False
        for i, old in enumerate(self._recipes):
            if old.name == r.name:
                self._recipes[i] = r
                replaced = True
                break
        if not replaced:
            self._recipes.append(r)
        save_recipes(self._recipes)
        self._reload_recipe_list()
        QMessageBox.information(self, "Сохранено", f"«{r.name}»")

    def delete_recipe(self) -> None:
        row = self.list_recipes.currentRow()
        if row < 0:
            return
        self._recipes.pop(row)
        save_recipes(self._recipes)
        self._reload_recipe_list()

    def open_file(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(self, "Открыть", "", "Text (*.txt);;All (*.*)")
        if not path:
            return
        self._input_path = Path(path)
        try:
            self.txt_in.setPlainText(
                self._input_path.read_text(encoding="utf-8", errors="replace")
            )
        except OSError as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))
            return
        self.setWindowTitle(f"EasySlicer — {self._input_path.name}")
        self._field_order.clear()
        self._rebuild_chips()
        self._refresh_all()

    def save_output(self) -> None:
        if not self._output:
            QMessageBox.warning(self, "Пусто", "Нет результата.")
            return
        from PyQt6.QtWidgets import QFileDialog

        default = "output.txt"
        if self._input_path:
            default = f"{self._input_path.stem}_out.txt"
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить", default, "Text (*.txt)")
        if not path:
            return
        Path(path).write_text("\n".join(self._output), encoding="utf-8")
        QMessageBox.information(self, "OK", f"{len(self._output)} строк")

    def copy_output(self) -> None:
        text = self.txt_out.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Пусто", "Нечего копировать.")
            return
        QApplication.clipboard().setText(text)
        self.lbl_stats.setText(self.lbl_stats.text() + " · в буфере")


def main() -> None:
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    settings = QSettings("EasySlicer", "EasySlicer")
    theme = str(settings.value("theme", "system"))
    apply_theme(app, theme)
    win = EasySlicerApp()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
