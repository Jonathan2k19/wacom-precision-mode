import sys
import signal

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QGuiApplication, QCursor
from PyQt6.QtCore import Qt, QRect

class Overlay(QWidget):
    def __init__(self, x:int, y:int, w:int, h:int):
        super().__init__()
        self.target_area = (x, y, w, h)

        # overlay applies to screen that contains the cursor
        screen = QGuiApplication.screenAt(QCursor.pos())
        assert screen
        self.setGeometry(screen.geometry())

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |   # pass input to app underneath
            Qt.WindowType.Tool                          # don't show with alt+tab
        )

        # allow windows underneath to "shine through"
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.showFullScreen()

    def paintEvent(self, a0):
        # grey-out everything but the target_area
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(QRect(*self.target_area), Qt.GlobalColor.transparent)
        painter.end()

def gui_init(x:int = 100, y:int = 100, w:int = 100, h:int = 100):
    assert x >= 0 and y >= 0 and w > 0 and h > 0

    # Use OS's default signal handlers for SIGTERM or SIGINT.
    # See https://stackoverflow.com/questions/4938723.
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    _ = Overlay(x, y, w, h)
    sys.exit(app.exec())

if __name__ == "__main__":
    gui_init()

