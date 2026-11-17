from PySide6.QtWidgets import QMessageBox, QPushButton

from ui.action_support import ActionContext, configure_button


class DeleteRegionButton(QPushButton):
    """删除一条已绑定区域。"""

    def __init__(self, context: ActionContext, region_id: str) -> None:
        super().__init__("删除")
        self.setObjectName("deleteButton")
        configure_button(self, "删除区域")
        self._context = context
        self._region_id = region_id
        self.clicked.connect(lambda _checked=False: self._delete())

    def _delete(self) -> None:
        region = self._context.store.get(self._region_id)
        if region is None:
            self._context.refresh()
            return
        box = QMessageBox(self._context.window)
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
        self._context.save_change(
            "删除区域",
            lambda: self._context.store.delete(self._region_id),
        )
