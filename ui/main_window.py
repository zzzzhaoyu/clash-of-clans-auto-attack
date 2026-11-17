from pathlib import Path

from PySide6.QtCore import Property, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.action_support import ActionContext
from ui.buttons.bind_region import BindRegionButton
from ui.buttons.show_regions import ShowRegionsButton
from ui.region_item import RegionItem
from ui.region_store import RegionStore

_STYLESHEET_PATH = Path(__file__).resolve().parent / "styles" / "main_window.qss"


class MainWindow(QMainWindow):
    """主窗口。左侧是操作按钮，右侧是已绑定区域列表。"""

    def __init__(self, store: RegionStore | None = None) -> None:
        super().__init__()
        self._store = store if store is not None else RegionStore()
        self._context = ActionContext(self, self._store, self._refresh_list)
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
        action_layout.addWidget(BindRegionButton(self._context))
        action_layout.addWidget(ShowRegionsButton(self._context))
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
            self._list_layout.addWidget(RegionItem(region, self._context))
        self._list_layout.addStretch(1)


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
