from PySide6.QtWidgets import QMessageBox, QPushButton

from core.screen_selector import select_area
from ui.action_support import ActionContext, as_bounds, configure_button, is_usable_area


class ReselectRegionButton(QPushButton):
    """重新框选一条已有区域。"""

    def __init__(self, context: ActionContext, region_id: str) -> None:
        super().__init__("重新框选")
        configure_button(self, "重新框选区域")
        self._context = context
        self._region_id = region_id
        self.clicked.connect(lambda _checked=False: self._reselect())

    def _reselect(self) -> None:
        if self._context.store.get(self._region_id) is None:
            self._context.refresh()
            return
        coords = self._context.run_on_screen(select_area)
        if coords is None:
            return
        if not is_usable_area(coords):
            QMessageBox.information(
                self._context.window, "重新框选", "选区太小，未更新。"
            )
            return
        bounds = as_bounds(coords)
        self._context.save_change(
            "重新框选",
            lambda: self._context.store.update_bounds(self._region_id, bounds),
        )
