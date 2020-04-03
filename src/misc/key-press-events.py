import PyQt5


class CustomButton(PyQt5.QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def event(self, event):

        triggers = [PyQt5.QtCore.Qt.Key_Return, PyQt5.QtCore.Qt.Key_Enter]

        if type(event) == PyQt5.QtGui.QKeyEvent:
            if event.key() in triggers:
                """ Custom handling goes here... """
                pass

        return super().event(event)

    def keyPressEvent(self, event):

        triggers = [PyQt5.QtCore.Qt.Key_Return, PyQt5.QtCore.Qt.Key_Enter]

        if event.key() in triggers:
            """ Custom handling goes here... """
            pass

        return super().event(event)
