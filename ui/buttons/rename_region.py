from PySide6.QtWidgets import QInputDialog, QMessageBox, QPushButton

from ui.action_support import ActionContext, configure_button


class RenameRegionButton(QPushButton):
    """修改一条区域的名称。"""

    def __init__(self, context: ActionContext, region_id: str) -> None:
        super().__init__("重命名")
        configure_button(self, "重命名名称")
        self._context = context
        self._region_id = region_id
        self.clicked.connect(lambda _checked=False: self._rename())

    def _rename(self) -> None:
        region = self._context.store.get(self._region_id)
        if region is None:
            self._context.refresh()
            return
        text, accepted = QInputDialog.getText(
            self._context.window, "重命名", "名称", text=region.name
        )
        if not accepted:
            return
        name = text.strip()
        if not name:
            QMessageBox.information(self._context.window, "重命名", "名称不能为空。")
            return
        if name == region.name:
            return
        self._context.save_change(
            "重命名",
            lambda: self._context.store.rename(self._region_id, name),
        )
