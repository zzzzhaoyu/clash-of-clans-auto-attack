from PySide6.QtWidgets import QMessageBox, QPushButton

from core.screen_selector import show_areas
from ui.action_support import ActionContext, configure_button


class ShowRegionsButton(QPushButton):
    """在屏幕上标出全部已绑定区域。"""

    def __init__(self, context: ActionContext) -> None:
        super().__init__("展示区域")
        self.setObjectName("showButton")
        configure_button(self)
        self._context = context
        self.clicked.connect(lambda _checked=False: self._show())

    def _show(self) -> None:
        areas = [
            (region.name, region.x1, region.y1, region.x2, region.y2)
            for region in self._context.store.regions()
        ]
        if not areas:
            QMessageBox.information(self._context.window, "展示区域", "还没有绑定区域。")
            return
        self._context.run_on_screen(lambda: show_areas(areas))
