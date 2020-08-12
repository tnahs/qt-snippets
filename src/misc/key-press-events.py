import PySide2
import PySide2.QtCore
import PySide2.QtGui
import PySide2.QtWidgets


class CustomButton(PySide2.QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def event(self, event):

        triggers = [PySide2.QtCore.Qt.Key_Return, PySide2.QtCore.Qt.Key_Enter]

        if type(event) == PySide2.QtGui.QKeyEvent:
            if event.key() in triggers:
                """ Custom handling goes here... """
                pass

        return super().event(event)

    def keyPressEvent(self, event):

        triggers = [PySide2.QtCore.Qt.Key_Return, PySide2.QtCore.Qt.Key_Enter]

        if event.key() in triggers:
            """ Custom handling goes here... """
            pass

        return super().event(event)
