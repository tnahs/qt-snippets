from typing import Optional

import PyQt5


class QtShowMixin:
    def center_window(
        self, offset_x: Optional[int] = None, offset_y: Optional[int] = None
    ):
        if not self.isVisible():
            raise AssertionError(
                "Qt object must be visible before calling this function."
            )

        desktop = PyQt5.QtWidgets.QApplication.desktop()
        screen = desktop.screenNumber(desktop.cursor().pos())
        center = desktop.screenGeometry(screen).center()

        if offset_x is not None:
            width = desktop.screenGeometry(screen).width()
            offset_x = (width / 2) + (width / 2 * -offset_x)
            center.setX(offset_y)

        if offset_y is not None:
            height = desktop.screenGeometry(screen).height()
            offset_y = (height / 2) + (height / 2 * -offset_y)
            center.setY(offset_y)

        rectangle = self.frameGeometry()
        rectangle.moveCenter(center)
        self.move(rectangle.topLeft())
