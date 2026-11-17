from dataclasses import dataclass
from PySide6.QtWidgets import QApplication, QWidget
from typing import Literal
import sys


@dataclass
class Model:
    epoch: int # 当前轮数
    epoch_max: int # 最大轮数
    name: Literal['loss', 'win']

class ClickClass:
    def __init__(self) -> None:
        self.model_win: Model = {
            'epoch': 0,
            'epoch_max': 50,
            'name': 'win'
        }

        self.model_loss: Model = {
            'epoch': 0,
            'epoch_max': 50,
            'name': 'loss'
        }

    def start_win(self) -> None:
        self.model_win.epoch = 0

        for epoch in range(self.model_win.epoch_max):
            print(f'正在进行胜利模式，当前轮数 {epoch}')

        print(f'胜利模式执行完成，共 {self.model_wind.epoch_max} 轮')

        
@dataclass
class Location:
    start: tuple[int, int] | None # 开始游戏
    place_left: tuple[int, int] | None

class LocateClick:
    def __init__(self) -> None:
        self.location = Location()

    def set_location(self) -> None:
        pass


# 创建应用程序
app = QApplication(sys.argv)

# 创建窗口
window = QWidget()

# 设置窗口标题
window.setWindowTitle("我的第一个 PySide6 程序")

# 设置窗口尺寸
window.resize(800, 600)

# 显示窗口
window.show()

# 启动事件循环
sys.exit(app.exec())