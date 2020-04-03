import PyQt5


def get_styles():
    """ Get all available Qt styles. """

    PyQt5.QtWidgets.QStyleFactory.keys()
    # PyQt5.QtWidgets.QApplication.setStyle()
