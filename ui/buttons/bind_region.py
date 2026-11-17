from PySide6.QtWidgets import QMessageBox, QPushButton

from core.screen_selector import select_area
from ui.action_support import ActionContext, as_bounds, configure_button, is_usable_area


class BindRegionButton(QPushButton):
    """框选一块屏幕区域并保存。"""

    def __init__(self, context: ActionContext) -> None:
        super().__init__("绑定区域")
        self.setObjectName("bindButton")
        configure_button(self)
        self._context = context
        self.clicked.connect(lambda _checked=False: self._bind())

    def _bind(self) -> None:
        coords = self._context.run_on_screen(select_area)
        if not is_usable_area(coords):
            if coords is not None:
                QMessageBox.information(
                    self._context.window, "绑定区域", "选区太小，未保存。"
                )
            return
        bounds = as_bounds(coords)
        self._context.save_change("绑定区域", lambda: self._context.store.add(bounds))
