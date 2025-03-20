import sys

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QGuiApplication, QCursor
from PyQt6.QtCore import Qt, QRect

from wacom_precision_mode import error

# TODO:FIXME:
# - add "+", "-" buttons that adjust scale
#   -> *partially* transparent inputs (everything but buttons pass through)
# - doesn't work if target_area spread *multiple* screens
#   (only the one that contains the cursor is overlayed)
# - kill the GUI on --disable

class Overlay(QWidget):
    def __init__(self, x:int, y:int, w:int, h:int):
        super().__init__()
        self.target_area = (x, y, w, h)

        # overlay applies to screen that contains the cursor
        self.setGeometry(QGuiApplication.screenAt(QCursor.pos()).geometry())

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |   # pass input to app underneath
            Qt.WindowType.Tool                          # don't show with alt+tab
        )

        # allow windows underneath to "shine through"
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.showFullScreen()

    def paintEvent(self, event):
        # grey-out everything but the target_area
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(QRect(*self.target_area), Qt.GlobalColor.transparent)
        painter.end()

def gui_init(x:int = 100, y:int = 100, w:int = 100, h:int = 100):
    print("initializing gui...")
    if x < 0 or y < 0 or w <= 0 or h <= 0:
        error("GUI: x < 0 or y < 0 or w <= 0 or h <= 0")

    app = QApplication(sys.argv)
    _ = Overlay(x, y, w, h)
    sys.exit(app.exec())

if __name__ == "__main__":
    gui_init()

