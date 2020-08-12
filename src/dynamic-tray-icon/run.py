import os
import pathlib
import sys

import PySide2
import PySide2.QtCore
import PySide2.QtGui
import PySide2.QtWidgets


ROOT = pathlib.Path(__file__).parent


class Icons:

    root = ROOT / "icons"

    idle = os.fspath(root / "idle.png")
    busy = os.fspath(root / "busy.png")
    alert = os.fspath(root / "alert.png")
    animated = os.fspath(root / "animated.gif")


class DynamicTrayIcon(PySide2.QtWidgets.QSystemTrayIcon):
    def __init__(self):
        super().__init__(parent=None)

        self._icon_idle = PySide2.QtGui.QIcon(Icons.idle)
        self._icon_busy = PySide2.QtGui.QIcon(Icons.busy)
        self._icon_alert = PySide2.QtGui.QIcon(Icons.alert)

        self._icon_animated = PySide2.QtGui.QMovie(Icons.animated)
        self._icon_animated.frameChanged.connect(self._update_icon_animated)

        self._set_icon()

    def idle(self):
        self._set_icon(state="idle")

    def busy(self):
        self._set_icon(state="busy")

    def alert(self):
        self._set_icon(state="alert")

    def animated(self):
        self._set_icon(state="animated")

    def _set_icon(self, state="idle"):

        self._icon_animated.stop()

        if state == "busy":
            self.setIcon(self._icon_busy)
        elif state == "alert":
            self.setIcon(self._icon_alert)
        elif state == "animated":
            self._icon_animated.start()
        else:
            self.setIcon(self._icon_idle)

    def _update_icon_animated(self):
        icon = PySide2.QtGui.QIcon(self._icon_animated.currentPixmap())
        self.setIcon(icon)


class MainWindow(PySide2.QtWidgets.QFrame):
    def __init__(self):
        super().__init__(parent=None)

        self._tray_icon = DynamicTrayIcon()
        self._tray_icon.show()

        button_idle = PySide2.QtWidgets.QPushButton("Idle")
        button_idle.clicked.connect(self._tray_icon.idle)

        button_busy = PySide2.QtWidgets.QPushButton("Busy")
        button_busy.clicked.connect(self._tray_icon.busy)

        button_alert = PySide2.QtWidgets.QPushButton("Alert")
        button_alert.clicked.connect(self._tray_icon.alert)

        button_animated = PySide2.QtWidgets.QPushButton("Animated")
        button_animated.clicked.connect(self._tray_icon.animated)

        button_quit = PySide2.QtWidgets.QPushButton("Quit")
        button_quit.clicked.connect(self.close)

        layout = PySide2.QtWidgets.QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(7)
        layout.addWidget(button_idle)
        layout.addWidget(button_busy)
        layout.addWidget(button_alert)
        layout.addWidget(button_animated)
        layout.addSpacing(10)
        layout.addWidget(button_quit)

        self.setLayout(layout)

        self.setFixedSize(self.sizeHint())


if __name__ == "__main__":

    app = PySide2.QtWidgets.QApplication([])

    main = MainWindow()
    main.show()

    sys.exit(app.exec_())
