from PySide6.QtCore import QSize, QTimer, Qt
from PySide6.QtGui import QCursor, QPainter, QPalette
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStyleOption,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid

from ui.action_support import ActionContext
from ui.buttons.delete_region import DeleteRegionButton
from ui.buttons.rename_region import RenameRegionButton
from ui.buttons.reselect_region import ReselectRegionButton
from ui.region_store import Region


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

    def __init__(self, region: Region, context: ActionContext) -> None:
        super().__init__()
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

        actions = QWidget()
        actions.setObjectName("regionActions")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)
        actions_layout.addWidget(RenameRegionButton(context, region.id))
        actions_layout.addWidget(ReselectRegionButton(context, region.id))
        actions_layout.addWidget(DeleteRegionButton(context, region.id))
        actions.setVisible(False)
        layout.addWidget(actions)
        self._actions = actions

    def enterEvent(self, event) -> None:
        self._set_hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        # 鼠标移进子按钮时父控件也会收到 leave，下一拍再确认是否真的离开。
        QTimer.singleShot(0, self._sync_hover_later)

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


def _format_meta(region: Region) -> str:
    # 存下来的是矩形两个角点，右下角那一像素也算在区域内。
    width = region.x2 - region.x1 + 1
    height = region.y2 - region.y1 + 1
    return f"{width} × {height}    ({region.x1}, {region.y1})"
