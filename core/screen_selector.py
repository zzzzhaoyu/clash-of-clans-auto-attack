import sys
from collections.abc import Sequence

from PySide6.QtCore import QEventLoop, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget


def _install_overlay(widget: QWidget) -> None:
    # 无边框、置顶。不用 Tool：Windows 上无主窗口的 Tool
    # 经常抢不到焦点，鼠标事件进不来。
    widget.setWindowFlags(
        Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.WindowStaysOnTopHint
        | Qt.WindowType.Window
    )
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    widget.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
    widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    screen = QApplication.primaryScreen()
    widget.setGeometry(screen.geometry())


def _show_and_wait(overlay: QWidget) -> None:
    loop = QEventLoop()
    overlay.finished.connect(loop.quit)
    overlay.show()
    overlay.raise_()
    overlay.activateWindow()
    overlay.setFocus()
    loop.exec()


class _ScreenOverlay(QWidget):
    """铺满主屏幕的遮罩。Esc 或关闭时结束等待。"""

    finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._finished = False
        _install_overlay(self)

    def closeEvent(self, event) -> None:
        if self.mouseGrabber() is self:
            self.releaseMouse()
        super().closeEvent(event)
        if self._finished:
            return
        self._finished = True
        self.finished.emit()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)


class ScreenSelector(_ScreenOverlay):

    # 选择完成后返回坐标
    selected = Signal(tuple)

    def __init__(self) -> None:
        super().__init__()
        self.setMouseTracking(True)

        # 鼠标拖拽状态
        self.start_pos = None
        self.current_pos = None

        self.setCursor(Qt.CursorShape.CrossCursor)

    def paintEvent(self, event):

        painter = QPainter(self)
        # 全透明像素在 Windows 上会被判定为“点穿”，
        # 鼠标直接落到下面的窗口，这个选择层收不到按下和拖拽。
        painter.fillRect(self.rect(), QColor(0, 0, 0, 40))

        if self.start_pos is None or self.current_pos is None:
            painter.end()
            return

        rect = QRect(self.start_pos, self.current_pos).normalized()
        painter.fillRect(rect, QColor(0, 168, 255, 60))
        painter.setPen(QPen(QColor("#00A8FF"), 2))
        painter.drawRect(rect)
        painter.end()

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            self.start_pos = event.position().toPoint()
            self.current_pos = self.start_pos
            self.grabMouse()
            self.update()

    def mouseMoveEvent(self, event):

        if self.start_pos is not None:

            self.current_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):

        if event.button() != Qt.MouseButton.LeftButton or self.start_pos is None:
            return

        if self.mouseGrabber() is self:
            self.releaseMouse()

        end_pos = event.position().toPoint()
        self.current_pos = end_pos

        rect = QRect(
            self.start_pos,
            end_pos
        ).normalized()

        # 转换成屏幕绝对坐标
        top_left = self.mapToGlobal(rect.topLeft())
        bottom_right = self.mapToGlobal(rect.bottomRight())

        result = (
            top_left.x(),
            top_left.y(),
            bottom_right.x(),
            bottom_right.y()
        )

        self.selected.emit(result)
        self.close()


class RegionPreview(_ScreenOverlay):
    """把已保存的区域画在屏幕上。点击任意位置关闭。"""

    def __init__(self, regions: Sequence[tuple[str, int, int, int, int]]) -> None:
        super().__init__()
        self._regions = [
            (str(name), int(x1), int(y1), int(x2), int(y2))
            for name, x1, y1, x2, y2 in regions
        ]
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 40))
        metrics = painter.fontMetrics()

        for name, x1, y1, x2, y2 in self._regions:
            rect = QRect(
                self.mapFromGlobal(QPoint(x1, y1)),
                self.mapFromGlobal(QPoint(x2, y2)),
            ).normalized()
            painter.fillRect(rect, QColor(0, 168, 255, 60))
            painter.setPen(QPen(QColor("#00A8FF"), 2))
            painter.drawRect(rect)
            self._draw_label(painter, metrics, rect, name)

        hint = "点击任意位置或按 Esc 关闭"
        if self._regions:
            hint = f"共 {len(self._regions)} 个区域，{hint}"
        self._draw_hint(painter, metrics, hint)
        painter.end()

    def mousePressEvent(self, event) -> None:
        del event
        self.close()

    def _draw_label(self, painter: QPainter, metrics, rect: QRect, name: str) -> None:
        if not name:
            return
        label = QRect(
            rect.left(),
            rect.top(),
            metrics.horizontalAdvance(name) + 10,
            metrics.height() + 6,
        )
        if label.right() > self.width():
            label.moveRight(max(label.width(), self.width()))
        if label.bottom() > self.height():
            label.moveBottom(max(label.height(), self.height()))
        if label.left() < 0:
            label.moveLeft(0)
        if label.top() < 0:
            label.moveTop(0)
        painter.fillRect(label, QColor(0, 90, 160, 210))
        painter.setPen(QColor("white"))
        painter.drawText(label, Qt.AlignmentFlag.AlignCenter, name)

    def _draw_hint(self, painter: QPainter, metrics, hint: str) -> None:
        hint_bg = QRect(
            0,
            0,
            metrics.horizontalAdvance(hint) + 28,
            metrics.height() + 12,
        )
        hint_bg.moveCenter(QPoint(self.width() // 2, 20 + hint_bg.height() // 2))
        painter.fillRect(hint_bg, QColor(0, 0, 0, 170))
        painter.setPen(QColor("white"))
        painter.drawText(hint_bg, Qt.AlignmentFlag.AlignCenter, hint)


def select_area() -> tuple[int, int, int, int] | None:
    """拖拽框选一块屏幕区域，返回左上角和右下角的绝对坐标。

    按 Esc 或直接关闭遮罩时返回 None。
    """

    selector = ScreenSelector()
    result: list[tuple[int, int, int, int]] = []
    selector.selected.connect(result.append)
    _show_and_wait(selector)
    return result[0] if result else None


def show_areas(regions: Sequence[tuple[str, int, int, int, int]]) -> None:
    """全屏画出已经绑定的区域，点击或按 Esc 关闭。"""

    _show_and_wait(RegionPreview(regions))


if __name__ == "__main__":

    app = QApplication(sys.argv)

    coordinates = select_area()

    print("选择区域：", coordinates)
