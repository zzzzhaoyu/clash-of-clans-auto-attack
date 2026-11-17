"""按钮共用的窗口上下文，以及选区校验。"""

from collections.abc import Callable
from typing import TypeGuard, TypeVar

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton, QWidget

from ui.region_store import RegionStore

_MIN_AREA_SPAN = 4
_T = TypeVar("_T")


class ActionContext:
    """按钮操作需要的窗口、存储和列表刷新。"""

    def __init__(
        self,
        window: QWidget,
        store: RegionStore,
        refresh: Callable[[], None],
    ) -> None:
        self.window = window
        self.store = store
        self.refresh = refresh

    def save_change(self, title: str, action: Callable[[], None]) -> None:
        try:
            action()
        except OSError as exc:
            self.store.reload()
            QMessageBox.warning(self.window, title, f"保存失败：{exc}")
        self.refresh()

    def run_on_screen(self, action: Callable[[], _T]) -> _T:
        app = QApplication.instance()
        quit_on_close = True
        if app is not None:
            quit_on_close = app.quitOnLastWindowClosed()
            # 主窗口先藏起来，遮罩是此时唯一可见窗口。关掉遮罩不能把整个程序退出。
            app.setQuitOnLastWindowClosed(False)
        self.window.hide()
        try:
            return action()
        finally:
            if app is not None:
                app.setQuitOnLastWindowClosed(quit_on_close)
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()


def configure_button(button: QPushButton, tip: str | None = None) -> None:
    if tip is not None:
        button.setToolTip(tip)
    button.setCursor(Qt.CursorShape.PointingHandCursor)


def is_usable_area(
    coords: tuple[int, int, int, int] | None,
) -> TypeGuard[tuple[int, int, int, int]]:
    if coords is None or len(coords) != 4:
        return False
    x1, y1, x2, y2 = coords
    return abs(x2 - x1) >= _MIN_AREA_SPAN and abs(y2 - y1) >= _MIN_AREA_SPAN


def as_bounds(coords: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = coords
    return int(x1), int(y1), int(x2), int(y2)
