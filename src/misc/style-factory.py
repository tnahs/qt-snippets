import PySide2
import PySide2.QtWidgets


def get_styles():
    """ Get all available Qt styles. """

    PySide2.QtWidgets.QStyleFactory.keys()
    # PySide2.QtWidgets.QApplication.setStyle()
