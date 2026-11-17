import sys
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget


class ScreenSelector(QWidget):

    # 选择完成后返回坐标
    selected = Signal(tuple)

    def __init__(self) -> None:
        super().__init__()

        # 无边框、置顶。不用 Tool：Windows 上无主窗口的 Tool
        # 经常抢不到焦点，鼠标事件进不来。
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Window
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        # 覆盖整个屏幕
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.geometry())

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
            return

        rect = QRect(self.start_pos, self.current_pos).normalized()
        painter.fillRect(rect, QColor(0, 168, 255, 60))
        painter.setPen(QPen(QColor("#00A8FF"), 2))
        painter.drawRect(rect)

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

        self.close()

        self.selected.emit(result)

def select_area():

    selector = ScreenSelector()

    result = []

    selector.selected.connect(
        lambda coordinates: result.append(coordinates)
    )

    selector.show()
    selector.raise_()
    selector.activateWindow()

    # 等待用户完成选择
    loop = __import__(
        "PySide6.QtCore",
        fromlist=["QEventLoop"]
    ).QEventLoop()

    selector.selected.connect(loop.quit)

    loop.exec()

    return result[0] if result else None


print(f'当前 name {__name__}')
if __name__ == "__main__":

    app = QApplication(sys.argv)

    coordinates = select_area()

    print("选择区域：", coordinates)
