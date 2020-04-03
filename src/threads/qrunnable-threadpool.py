import logging
import random
import string
import sys
import time
import traceback
from typing import Any, Callable, Dict, Optional, Tuple

import PyQt5
import PyQt5.QtCore
import PyQt5.QtWidgets

# via https://www.learnpyqt.com/courses/concurrent-execution/multithreading-pyqt-applications-qthreadpool/
# via http://dmnfarrell.github.io/python/pyside2-threaded-process


logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(threadName)s %(name)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


logger = logging.getLogger()


class Task(object):
    def run(self, arg1: str, kwarg1: str = "default", kwarg2: str = "default") -> str:

        logger.debug("Task.run entered...")

        duration = random.randint(1, 5)
        time.sleep(duration)

        logger.debug("Task.run complete...")

        return "Ran {0}s task with arg1:{1} kwarg1:{2} kwarg2:{3}".format(
            duration, arg1, kwarg1, kwarg2
        )


class WorkerSignals(PyQt5.QtCore.QObject):

    """
    """

    started = PyQt5.QtCore.pyqtSignal()
    error = PyQt5.QtCore.pyqtSignal(object)
    result = PyQt5.QtCore.pyqtSignal(object)
    complete = PyQt5.QtCore.pyqtSignal()


class Worker(PyQt5.QtCore.QRunnable):
    def __init__(
        self,
        func: Callable,
        args: Optional[Tuple[Any, ...]],
        kwargs: Optional[Dict[str, Any]],
    ) -> None:
        super(Worker, self).__init__()

        self.signals = WorkerSignals()

        self.__func = func
        self.__args = ()
        self.__kwargs = {}

        if args is not None:
            self.__args = args  # type: ignore

        if kwargs is not None:
            self.__kwargs = kwargs

    def run(self) -> None:

        logger.debug("Worker to emit `starting`...")
        self.signals.started.emit()

        try:
            result = self.__func(*self.__args, **self.__kwargs)
        except Exception:
            traceback.print_exc()
            logger.debug("Worker to emit `error`...")
            self.signals.error.emit(traceback.format_exc())
        else:
            logger.debug("Worker to emit `result`...")
            self.signals.result.emit(result)
        finally:
            logger.debug("Worker to emit `complete`...")
            self.signals.complete.emit()


class WorkerAgent(PyQt5.QtCore.QObject):

    __threadpool = PyQt5.QtCore.QThreadPool()

    def __init__(self, global_callbacks: Optional[Dict[str, Callable]] = None) -> None:
        super(WorkerAgent, self).__init__(parent=None)
        """
        global_callbacks = {
            "started": ...,
            "error": ...,
            "result": ...,
            "complete": ...,
        }
        """

        if global_callbacks is None:
            global_callbacks = {}

        self._callback__worker_started = global_callbacks.get("started", None)
        self._callback__worker_error = global_callbacks.get("error", None)
        self._callback__worker_result = global_callbacks.get("result", None)
        self._callback__worker_complete = global_callbacks.get("complete", None)

    def dispatch(
        self,
        func: Callable,
        args: Optional[Tuple[Any, ...]],
        kwargs: Optional[Dict[str, Any]],
        local_callbacks: Optional[Dict[str, Callable]] = None,
    ) -> None:

        worker = Worker(func, args=args, kwargs=kwargs)

        if self._callback__worker_started is not None:
            worker.signals.started.connect(self._callback__worker_started)
        if self._callback__worker_error is not None:
            worker.signals.error.connect(self._callback__worker_error)
        if self._callback__worker_result is not None:
            worker.signals.result.connect(self._callback__worker_result)
        if self._callback__worker_complete is not None:
            worker.signals.complete.connect(self._callback__worker_complete)

        if local_callbacks is None:
            local_callbacks = {}

        local_callback__started = local_callbacks.get("started", None)
        local_callback__error = local_callbacks.get("error", None)
        local_callback__result = local_callbacks.get("result", None)
        local_callback__complete = local_callbacks.get("complete", None)

        if local_callback__started is not None:
            worker.signals.started.connect(local_callback__started)
        if local_callback__error is not None:
            worker.signals.error.connect(local_callback__error)
        if local_callback__result is not None:
            worker.signals.result.connect(local_callback__result)
        if local_callback__complete is not None:
            worker.signals.complete.connect(local_callback__complete)

        self.__threadpool.start(worker)

    @property
    def active_threads(self) -> int:
        return self.__threadpool.activeThreadCount()

    @property
    def max_threads(self) -> int:
        return self.__threadpool.maxThreadCount()

    @max_threads.setter
    def max_threads(self, value: int) -> None:
        self.__threadpool.setMaxThreadCount(value)


class MainWindow(PyQt5.QtWidgets.QFrame):
    def __init__(self) -> None:
        super(MainWindow, self).__init__(parent=None)

        self._worker_agent = WorkerAgent(
            global_callbacks={
                "started": self._callback__worker_started,
                "error": self._callback__worker_error,
                "result": self._callback__worker_result,
                "complete": self._callback__worker_complete,
            },
        )

        self._init_ui()

    def _init_ui(self) -> None:

        self.setFixedSize(768, 512)

        self._worker_agent_output = PyQt5.QtWidgets.QPlainTextEdit("Idle...")
        self._worker_agent_output.setReadOnly(True)
        self._worker_agent_output.setStyleSheet(
            """
            font-family: Monaco, monospace;
            font-size: 12pt;
        """
        )

        self._worker_output = PyQt5.QtWidgets.QPlainTextEdit()
        self._worker_output.setReadOnly(True)
        self._worker_output.setStyleSheet(
            """
            font-family: Monaco, monospace;
            font-size: 12pt;
        """
        )

        self._progress_bar = PyQt5.QtWidgets.QProgressBar()

        self._button_new = PyQt5.QtWidgets.QPushButton("Start New Task...")
        self._button_new.clicked.connect(self._on_button_new_clicked)

        layout = PyQt5.QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._worker_agent_output)
        layout.addWidget(self._worker_output)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._button_new)

        self.setLayout(layout)

    def _on_button_new_clicked(self) -> None:

        self._progress_bar.setRange(0, 0)
        self._worker_agent_output.appendPlainText("Queuing new task...")

        task = Task()

        arg1 = self._random_string()
        kwarg1 = self._random_string()
        kwarg2 = self._random_string()

        self._worker_agent.dispatch(
            task.run,
            args=(arg1,),
            kwargs={"kwarg1": kwarg1, "kwarg2": kwarg2},
            local_callbacks={"complete": self._local_callback__complete},
        )

        self._post_worker_agent_status()

    def _post_worker_agent_status(self) -> None:

        self._worker_agent_output.appendPlainText(
            f"{self._worker_agent.active_threads} tasks remaining..."
        )
        self._worker_agent_output.appendPlainText(
            f"{self._worker_agent.active_threads} of "
            f"{self._worker_agent.max_threads} threads in use..."
        )

    def _local_callback__complete(self) -> None:
        self._worker_output.appendPlainText("CUSTOM COMPLETED CALLBACK CALLED!")

    def _callback__worker_started(self) -> None:
        self._worker_output.appendPlainText("Worker Starting...")

    def _callback__worker_error(self, error) -> None:
        self._worker_output.appendPlainText(f"Worker Error: {error}")

    def _callback__worker_result(self, result) -> None:
        self._worker_output.appendPlainText(f"Worker Result: {result}")

    def _callback__worker_complete(self) -> None:
        self._worker_output.appendPlainText(f"Worker Complete...")

        if self._worker_agent.active_threads:
            self._post_worker_agent_status()
            return

        self._worker_agent_output.appendPlainText("Idle...")
        self._progress_bar.setRange(0, 1)

    @staticmethod
    def _random_string() -> str:
        letters = string.ascii_lowercase
        length = random.randint(5, 10)
        return "".join(random.choice(letters) for i in range(length))


if __name__ == "__main__":

    app = PyQt5.QtWidgets.QApplication([])

    main = MainWindow()
    main.show()

    sys.exit(app.exec_())
