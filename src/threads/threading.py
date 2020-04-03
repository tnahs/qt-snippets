import logging
import random
import sys
import threading
import time
import traceback
from typing import Any, Callable

import PyQt5
import PyQt5.QtCore
import PyQt5.QtWidgets


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(threadName)-10s %(name)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class Sleeper(object):
    def simple(self):

        logger.debug("<Sleeper>.simple() started.")
        duration = random.randint(1, 4)
        time.sleep(duration)
        logger.debug("<Sleeper>.simple() complete.")

        return f"<Sleeper>.simple() returned. Slept: {duration} seconds."

    def args(self, argument):

        logger.debug("<Sleeper>.args() started.")
        duration = random.randint(1, 4)
        time.sleep(duration)
        logger.debug("<Sleeper>.args() complete.")

        return f"Sleeper.args() returned with: '{argument}'. Slept: {duration} seconds."

    def kwargs(self, keyword=None):

        logger.debug("<Sleeper>.kwargs() started.")
        duration = random.randint(1, 4)
        time.sleep(duration)
        logger.debug("<Sleeper>.kwargs() complete.")

        if keyword is not None:
            return f"Ran Sleeper.kwargs() with: keyword='{keyword}'. Slept: {duration} seconds."

        return f"<Sleeper>.kwargs() returned. Slept: {duration} seconds."

    def args_kwargs(self, argument, keyword=None):

        logger.debug("<Sleeper>.args_kwargs() started.")
        duration = random.randint(1, 4)
        time.sleep(duration)
        logger.debug("<Sleeper>.args_kwargs() complete.")

        message = f"<Sleeper>.args_kwargs() returned with: '{argument}'."

        if keyword is not None:
            message = f"{message[:-1]} and keyword='{keyword}'."

        return f"{message} Slept: {duration} seconds."

    def error(self):

        logger.debug("<Sleeper>.error() started.")
        duration = random.randint(1, 4)
        time.sleep(duration)
        logger.debug("<Sleeper>.error() complete.")

        raise Exception("<Sleeper>.error() aborted.")

        return "This will never be seen..."


class Thread(PyQt5.QtCore.QObject):

    starting = PyQt5.QtCore.pyqtSignal(int)
    error = PyQt5.QtCore.pyqtSignal(str)
    result = PyQt5.QtCore.pyqtSignal(object)
    complete = PyQt5.QtCore.pyqtSignal(int)

    def __init__(self, task: Callable, *args: Any, **kwargs: Any):
        super(Thread, self).__init__(parent=None)

        self.__task = task
        self.__args = args
        self.__kwargs = kwargs

    def start(self):
        self.__thread = threading.Thread(target=self._run)
        self.__thread.start()

    # def start(self):
    #     self.__thread = PyQt5.QtCore.QThread()
    #     self.__thread.start()

    def _run(self):

        self.starting.emit(self.__thread.ident)
        logger.debug("Thread to emit `starting`.")

        try:
            result = self.__task(*self.__args, **self.__kwargs)
        except Exception:
            logger.exception("Thread to emit `error`.")
            self.error.emit(traceback.format_exc().strip())
        else:
            logger.debug("Thread to emit `result`.")
            self.result.emit(result)
        finally:
            logger.debug("Thread to emit `complete`.")
            self.complete.emit(self.__thread.ident)


class MainWindow(PyQt5.QtWidgets.QFrame):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setAttribute(PyQt5.QtCore.Qt.WA_DeleteOnClose)

        self._sleeper = Sleeper()

        self._threads = [
            Thread(self._sleeper.simple),
            Thread(self._sleeper.args, "my_arg"),
            Thread(self._sleeper.kwargs, keyword="my_kwarg"),
            Thread(self._sleeper.args_kwargs, "my_arg", keyword="my_kwarg"),
        ]

        self._init_ui()

    def _init_ui(self):

        self.setFixedWidth(768)

        self._output = PyQt5.QtWidgets.QPlainTextEdit("THREAD: Idle...")
        self._output.setReadOnly(True)
        self._output.setStyleSheet(
            """
            font-family: Fira Code;
            font-size: 14pt;
        """
        )

        self._progress_bar = PyQt5.QtWidgets.QProgressBar()

        self._button_start_1 = PyQt5.QtWidgets.QPushButton("Start 1 Thread")
        self._button_start_1.clicked.connect(self._on_button_start_1_clicked)

        self._button_start_4 = PyQt5.QtWidgets.QPushButton("Start 4 Threads")
        self._button_start_4.clicked.connect(self._on_button_start_4_clicked)

        layout_buttons = PyQt5.QtWidgets.QHBoxLayout()
        layout_buttons.addWidget(self._button_start_1)
        layout_buttons.addWidget(self._button_start_4)

        layout = PyQt5.QtWidgets.QVBoxLayout()
        layout.addWidget(self._output)
        layout.addWidget(self._progress_bar)
        layout.addLayout(layout_buttons)

        self.setLayout(layout)

    def _on_button_start_1_clicked(self):

        which = random.randint(0, 3)

        thread = self._threads[which]
        thread.starting.connect(self._on_thread_starting)
        thread.error.connect(self._on_thread_error)
        thread.result.connect(self._on_thread_result)
        thread.complete.connect(self._on_thread_complete)
        thread.start()

    def _on_button_start_4_clicked(self):

        for thread in self._threads:
            thread.error.connect(self._on_thread_error)
            thread.result.connect(self._on_thread_result)
            thread.complete.connect(self._on_thread_complete)
            thread.start()

    def _on_thread_starting(self, id: int):
        self._output.appendPlainText(f"THREAD {id}: Starting...")
        self._progress_bar.setRange(0, 0)

    def _on_thread_error(self, error: str):
        self._output.appendPlainText(f"ERROR: {error}")

    def _on_thread_result(self, result: Any):
        self._output.appendPlainText(f"RESULT: {result}")

    def _on_thread_complete(self, id: int):

        self._output.appendPlainText(f"THREAD {id}: Complete...")

        active_threads = threading.active_count()

        if active_threads > 1:
            logger.debug(f"{threading.active_count()} still active...")
            return

        self._progress_bar.setRange(0, 1)


if __name__ == "__main__":

    app = PyQt5.QtWidgets.QApplication([])

    main = MainWindow()
    main.show()

    sys.exit(app.exec_())
