import PySide6
import PySide6.QtCore
import PySide6.QtGui
import PySide6.QtWidgets


class CustomButton(PySide6.QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def event(self, event):

        triggers = [PySide6.QtCore.Qt.Key_Return, PySide6.QtCore.Qt.Key_Enter]

        if type(event) == PySide6.QtGui.QKeyEvent:
            if event.key() in triggers:
                """ Custom handling goes here... """
                pass

        return super().event(event)

    def keyPressEvent(self, event):

        triggers = [PySide6.QtCore.Qt.Key_Return, PySide6.QtCore.Qt.Key_Enter]

        if event.key() in triggers:
            """ Custom handling goes here... """
            pass

        return super().event(event)
