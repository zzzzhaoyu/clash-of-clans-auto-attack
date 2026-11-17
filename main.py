import sys

from PySide6.QtWidgets import QApplication

from ui import create_main_window


def main() -> None:
    app = QApplication(sys.argv)
    window = create_main_window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
