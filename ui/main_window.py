from pathlib import Path

from PySide6.QtCore import Property, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QCursor, QPainter, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyleOption,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid

from core.screen_selector import select_area, show_areas
from ui.region_store import Region, RegionStore

_STYLESHEET_PATH = Path(__file__).resolve().parent / "styles" / "main_window.qss"
_MIN_AREA_SPAN = 4


class ElidingLabel(QLabel):
    """横向空间不够时省略文字，避免把右侧按钮挤出列表。"""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._full_text = text
        self.setMinimumWidth(0)
        self.setToolTip(text)

    def minimumSizeHint(self) -> QSize:
        return QSize(0, super().minimumSizeHint().height())

    def sizeHint(self) -> QSize:
        return QSize(80, super().sizeHint().height())

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setFont(self.font())
        option = QStyleOption()
        option.initFrom(self)
        painter.setPen(option.palette.color(QPalette.ColorRole.WindowText))
        text = painter.fontMetrics().elidedText(
            self._full_text,
            Qt.TextElideMode.ElideRight,
            max(0, self.width()),
        )
        painter.drawText(
            self.rect(),
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            text,
        )
        painter.end()


class RegionItem(QWidget):
    """区域列表中的一行。悬停时在最右侧露出重命名、重新框选和删除。"""

    rename_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, region: Region) -> None:
        super().__init__()
        self._region_id = region.id
        self.setObjectName("regionItem")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setMouseTracking(True)
        self.setMinimumHeight(52)
        self.setToolTip(f"{region.name}\n{_format_meta(region)}")
        self.setProperty("hovered", "false")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 8, 6)
        layout.setSpacing(8)

        text_box = QWidget()
        text_box.setMinimumWidth(0)
        text_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        text_layout = QVBoxLayout(text_box)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self._name = ElidingLabel(region.name)
        self._name.setObjectName("regionName")
        self._name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        text_layout.addWidget(self._name)

        meta = QLabel(_format_meta(region))
        meta.setObjectName("regionMeta")
        meta.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        meta.setMinimumWidth(0)
        meta.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        text_layout.addWidget(meta)
        layout.addWidget(text_box, 1)

        self._actions = QWidget()
        self._actions.setObjectName("regionActions")
        actions_layout = QHBoxLayout(self._actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)

        rename_button = self._make_action("重命名", "重命名名称", self.rename_requested)
        edit_button = self._make_action("重新框选", "重新框选区域", self.edit_requested)
        delete_button = self._make_action("删除", "删除区域", self.delete_requested)
        delete_button.setObjectName("deleteButton")
        actions_layout.addWidget(rename_button)
        actions_layout.addWidget(edit_button)
        actions_layout.addWidget(delete_button)
        self._actions.setVisible(False)
        layout.addWidget(self._actions)

    def enterEvent(self, event) -> None:
        self._set_hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        # 鼠标移进子按钮时父控件也会收到 leave，下一拍再确认是否真的离开。
        QTimer.singleShot(0, self._sync_hover_later)

    def _make_action(self, text: str, tip: str, signal: Signal) -> QPushButton:
        button = QPushButton(text)
        button.setToolTip(tip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda _checked=False: signal.emit(self._region_id))
        return button

    def _sync_hover_later(self) -> None:
        if not isValid(self):
            return
        inside = self.rect().contains(self.mapFromGlobal(QCursor.pos()))
        self._set_hovered(inside)

    def _set_hovered(self, hovered: bool) -> None:
        self._actions.setVisible(hovered)
        self.setProperty("hovered", "true" if hovered else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class MainWindow(QMainWindow):
    """主窗口。左侧是操作按钮，右侧是已绑定区域列表。"""

    def __init__(self, store: RegionStore | None = None) -> None:
        super().__init__()
        self._store = store if store is not None else RegionStore()
        self.setWindowTitle("Clash of Clans Auto Attack")
        self.setMinimumSize(780, 420)
        self.resize(880, 520)

        container = QWidget()
        container.setObjectName("central")
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._content_layout = QHBoxLayout(container)

        action_panel = QWidget()
        action_panel.setObjectName("actionPanel")
        action_panel.setFixedWidth(188)
        action_layout = QVBoxLayout(action_panel)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)

        action_title = QLabel("操作")
        action_title.setObjectName("panelTitle")
        action_layout.addWidget(action_title)

        self._bind_button = QPushButton("绑定区域")
        self._bind_button.setObjectName("bindButton")
        self._bind_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._bind_button.clicked.connect(self._bind_region)
        action_layout.addWidget(self._bind_button)

        self._show_button = QPushButton("展示区域")
        self._show_button.setObjectName("showButton")
        self._show_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._show_button.clicked.connect(self._show_regions)
        action_layout.addWidget(self._show_button)
        action_layout.addStretch(1)

        region_column = QWidget()
        region_column.setObjectName("regionColumn")
        region_layout = QVBoxLayout(region_column)
        region_layout.setContentsMargins(0, 0, 0, 0)
        region_layout.setSpacing(8)

        self._list_title = QLabel("区域列表")
        self._list_title.setObjectName("panelTitle")
        region_layout.addWidget(self._list_title)

        region_panel = QWidget()
        region_panel.setObjectName("regionPanel")
        region_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        panel_layout = QVBoxLayout(region_panel)
        panel_layout.setContentsMargins(8, 8, 8, 8)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("regionScroll")
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.viewport().setObjectName("regionViewport")
        self._scroll.viewport().setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._list_host = QWidget()
        self._list_host.setObjectName("regionList")
        self._list_host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._list_layout = QVBoxLayout(self._list_host)
        self._list_layout.setContentsMargins(4, 4, 4, 4)
        self._list_layout.setSpacing(4)
        self._scroll.setWidget(self._list_host)
        panel_layout.addWidget(self._scroll)
        region_layout.addWidget(region_panel, 1)

        self._content_layout.addWidget(action_panel)
        self._content_layout.addWidget(region_column, 1)
        self.setCentralWidget(container)
        self.setStyleSheet(_STYLESHEET_PATH.read_text(encoding="utf-8"))
        self._refresh_list()

    def _content_margin(self) -> int:
        return self._content_layout.contentsMargins().left()

    def _set_content_margin(self, value: int) -> None:
        self._content_layout.setContentsMargins(value, value, value, value)

    def _content_spacing(self) -> int:
        return self._content_layout.spacing()

    def _set_content_spacing(self, value: int) -> None:
        self._content_layout.setSpacing(value)

    contentMargin = Property(int, _content_margin, _set_content_margin)
    contentSpacing = Property(int, _content_spacing, _set_content_spacing)

    def _bind_region(self) -> None:
        coords = self._run_on_screen(select_area)
        if not _is_usable_area(coords):
            if coords is not None:
                QMessageBox.information(self, "绑定区域", "选区太小，未保存。")
            return
        bounds = _as_bounds(coords)
        self._save_change("绑定区域", lambda: self._store.add(bounds))

    def _show_regions(self) -> None:
        areas = [
            (region.name, region.x1, region.y1, region.x2, region.y2)
            for region in self._store.regions()
        ]
        if not areas:
            QMessageBox.information(self, "展示区域", "还没有绑定区域。")
            return
        self._run_on_screen(lambda: show_areas(areas))

    def _rename_region(self, region_id: str) -> None:
        region = self._store.get(region_id)
        if region is None:
            self._refresh_list()
            return
        text, accepted = QInputDialog.getText(self, "重命名", "名称", text=region.name)
        if not accepted:
            return
        name = text.strip()
        if not name:
            QMessageBox.information(self, "重命名", "名称不能为空。")
            return
        if name == region.name:
            return
        self._save_change("重命名", lambda: self._store.rename(region_id, name))

    def _edit_region(self, region_id: str) -> None:
        if self._store.get(region_id) is None:
            self._refresh_list()
            return
        coords = self._run_on_screen(select_area)
        if coords is None:
            return
        if not _is_usable_area(coords):
            QMessageBox.information(self, "重新框选", "选区太小，未更新。")
            return
        bounds = _as_bounds(coords)
        self._save_change(
            "重新框选",
            lambda: self._store.update_bounds(region_id, bounds),
        )

    def _delete_region(self, region_id: str) -> None:
        region = self._store.get(region_id)
        if region is None:
            self._refresh_list()
            return
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("删除区域")
        box.setText(f"确定删除「{region.name}」吗？")
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        box.setDefaultButton(QMessageBox.StandardButton.No)
        yes_button = box.button(QMessageBox.StandardButton.Yes)
        no_button = box.button(QMessageBox.StandardButton.No)
        if yes_button is not None:
            yes_button.setText("删除")
        if no_button is not None:
            no_button.setText("取消")
        if box.exec() != QMessageBox.StandardButton.Yes:
            return
        self._save_change("删除区域", lambda: self._store.delete(region_id))

    def _save_change(self, title: str, action) -> None:
        try:
            action()
        except OSError as exc:
            self._store.reload()
            QMessageBox.warning(self, title, f"保存失败：{exc}")
        self._refresh_list()

    def _run_on_screen(self, action):
        app = QApplication.instance()
        quit_on_close = True
        if app is not None:
            quit_on_close = app.quitOnLastWindowClosed()
            # 主窗口先藏起来，遮罩是此时唯一可见窗口。关掉遮罩不能把整个程序退出。
            app.setQuitOnLastWindowClosed(False)
        self.hide()
        try:
            return action()
        finally:
            if app is not None:
                app.setQuitOnLastWindowClosed(quit_on_close)
            self.show()
            self.raise_()
            self.activateWindow()

    def _refresh_list(self) -> None:
        _clear_layout(self._list_layout)
        regions = self._store.regions()
        self._list_title.setText(
            "区域列表" if not regions else f"区域列表（{len(regions)}）"
        )
        if not regions:
            empty = QLabel("暂无区域")
            empty.setObjectName("emptyHint")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list_layout.addStretch(1)
            self._list_layout.addWidget(empty, 0, Qt.AlignmentFlag.AlignCenter)
            self._list_layout.addStretch(1)
            return

        for region in regions:
            row = RegionItem(region)
            row.rename_requested.connect(self._rename_region)
            row.edit_requested.connect(self._edit_region)
            row.delete_requested.connect(self._delete_region)
            self._list_layout.addWidget(row)
        self._list_layout.addStretch(1)


def _format_meta(region: Region) -> str:
    # 存下来的是矩形两个角点，右下角那一像素也算在区域内。
    width = region.x2 - region.x1 + 1
    height = region.y2 - region.y1 + 1
    return f"{width} × {height}    ({region.x1}, {region.y1})"


def _is_usable_area(coords: tuple[int, int, int, int] | None) -> bool:
    if coords is None or len(coords) != 4:
        return False
    x1, y1, x2, y2 = coords
    return abs(x2 - x1) >= _MIN_AREA_SPAN and abs(y2 - y1) >= _MIN_AREA_SPAN


def _as_bounds(coords: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = coords
    return int(x1), int(y1), int(x2), int(y2)


def _clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()


def create_main_window() -> MainWindow:
    """创建主窗口。调用方负责显示窗口并启动事件循环。"""
    return MainWindow()
