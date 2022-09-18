import PySide6
import PySide6.QtWidgets


def get_styles():
    """ Get all available Qt styles. """

    PySide6.QtWidgets.QStyleFactory.keys()
    # PySide6.QtWidgets.QApplication.setStyle()
