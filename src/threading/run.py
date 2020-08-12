import logging
import random
import string
import sys
import threading
import time
import traceback
from types import TracebackType
from typing import Any, Callable, Dict, Optional, Tuple

import PySide2
import PySide2.QtCore
import PySide2.QtWidgets


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(threadName)s %(name)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


logger = logging.getLogger()


class Task(object):
    def run(self, arg1: str, kwarg1: str = "default", kwarg2: str = "default") -> str:

        logger.debug("Task.run entered...")

        if random.random() < 0.10:
            raise Exception("Worker encounterd an `error` during excecution.")

        duration = random.randint(1, 5)
        time.sleep(duration)

        logger.debug("Task.run complete...")

        return "Ran {0}s task with arg1={1} kwarg1={2} kwarg2={3}...".format(
            duration, arg1, kwarg1, kwarg2
        )


class WorkerSignals(PySide2.QtCore.QObject):
    """ Defines signals for `Worker` objects.

    Note: The signals are decoupled from the `Worker` because `QRunnable` is
    not a subclass of `QObject` and does not support signal emission.

    started -- Emitted at the start of the `Worker.run` method. Emits the
        worker's name via the `threading` module.

    error -- Emitted only if the workers internal `__func` raises an exception
        during excecution. Emits a tuple of the exception, traceback and a
        formatted traceback.

    result - Emitted only if the workers internal `__func` executes
        sucessfully. Emits its return value.

    complete -- Emitted at the end of the `Worker.run` method independant of
        wheather or not any exceptions were raised while excecuting the
        workers internal `__func`. Emits the worker's name via the `threading`
        module. """

    NAMES = [
        "started",
        "error",
        "result",
        "complete",
    ]

    started = PySide2.QtCore.Signal(str)
    error = PySide2.QtCore.Signal(tuple)
    result = PySide2.QtCore.Signal(object)
    complete = PySide2.QtCore.Signal(str)


class Worker(PySide2.QtCore.QRunnable):
    def __init__(self, func: Callable, *args, **kwargs) -> None:
        super(Worker, self).__init__()

        self._signals = WorkerSignals()

        self.__func = func
        self.__args = args
        self.__kwargs = kwargs

    def run(self) -> None:
        """ Note: The current QThread can be access by calling the static
        function:

            PySide2.QtCore.QThread.currentThread()
        """

        self.__name = threading.current_thread().name

        self._signals.started.emit(self.__name)

        logger.debug(f"Thread started.")

        try:
            result = self.__func(*self.__args, **self.__kwargs)
        except Exception:
            logger.exception(f"Thread encountered an error during execution.")
            exception_obj: Optional[BaseException] = sys.exc_info()[-2]
            traceback_obj: Optional[TracebackType] = sys.exc_info()[-1]
            traceback_formatted: str = traceback.format_exc()
            self._signals.error.emit(
                (exception_obj, traceback_obj, traceback_formatted)
            )
        else:
            self._signals.result.emit(result)
        finally:
            self._signals.complete.emit(self.__name)

        logger.debug(f"Thread complete.")

    def connect(self, callbacks: Optional[Dict[str, Callable]]):

        if callbacks is None:
            return

        for key in callbacks.keys():
            if key not in WorkerSignals.NAMES:
                valid_keys = [f"`{name}`" for name in WorkerSignals.NAMES]
                raise AssertionError(
                    f"{self.__class__.__name__}: Invalid key in `callbacks`: "
                    f"{key}. Valid keys are: {', '.join(valid_keys)}."
                )

        for signal_name in WorkerSignals.NAMES:

            callback: Optional[Callable] = callbacks.get(signal_name, None)

            if callback is None:
                continue

            signal: PySide2.QtCore.Signal = getattr(self._signals, signal_name)
            signal.connect(callback)


class WorkerAgent(PySide2.QtCore.QObject):

    __threadpool = PySide2.QtCore.QThreadPool()

    def __init__(
        self,
        max_thread_count: Optional[int] = None,
        global_callbacks: Optional[Dict[str, Callable]] = None,
    ) -> None:
        super(WorkerAgent, self).__init__(parent=None)
        """ Manages instantiation and dispatch of worker to threads in a
        QThreadPool. Each worker is connected to a set of global and local
        callbacks to respective Qt signals.

        max_thread_count -- Sets the maxiumum number of concurrent threads
            allowed in the threadpool. By default this is set to the number of
            processor cores, both real and logical, in the system.

        global_callbacks -- Global callbacks are connected to every worker
            created by the `WorkerAgent`. Each callback is connected to one of
            four worker signals (found in `WorkerSignals`) through a dictionay
            of key:value pairs where the key is signal name and the value is
            the callable. Valid keys are: `started`, `error`, `result`
            and `complete` (found in `WorkerSignals.NAMES`):

                callbacks = {
                    "started": on_worker_started,
                    "error": on_worker_error,
                    "result": on_worker_result,
                    "complete": on_worker_complete,
                }

        https://doc.qt.io/qtforpython/PySide2/QtCore/QThread.html
        https://doc.qt.io/qtforpython/PySide2/QtCore/QThreadPool.html """

        self._global_callbacks = global_callbacks

        if max_thread_count is not None:
            self.max_thread_count = max_thread_count

    def dispatch(
        self,
        func: Callable,
        args: Optional[Tuple[Any, ...]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        local_callbacks: Optional[Dict[str, Callable]] = None,
    ) -> None:
        """ Creats a `Worker` from a callable object and dispatches it to a
        `QThreadPool`.

        func -- The function to call in the thread.
        args -- The function arguments.
        kwargs -- The function keyword arguments.
        local_callbacks -- Local callback are identical to global ones but are
            connected only the current worker. See `global_callbacks`. """

        if args is None:
            args = ()

        if kwargs is None:
            kwargs = {}

        worker = Worker(func, *args, **kwargs)
        worker.connect(callbacks=self._global_callbacks)
        worker.connect(callbacks=local_callbacks)

        logger.debug("Dispatching thread.")

        self.__threadpool.start(worker)

    @property
    def active_threads(self) -> int:
        return self.__threadpool.activeThreadCount()

    @property
    def max_thread_count(self) -> int:
        return self.__threadpool.maxThreadCount()

    @max_thread_count.setter
    def max_thread_count(self, value: int) -> None:
        self.__threadpool.setMaxThreadCount(value)


class MainWindow(PySide2.QtWidgets.QFrame):
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

        self._label_worker_agent_log = PySide2.QtWidgets.QLabel("Agent Log:")
        self._worker_agent_log = PySide2.QtWidgets.QPlainTextEdit()
        self._worker_agent_log.setReadOnly(True)

        self._worker_agent_progress_bar = PySide2.QtWidgets.QProgressBar()

        self._label_worker_log = PySide2.QtWidgets.QLabel("Worker Log:")
        self._worker_log = PySide2.QtWidgets.QPlainTextEdit()
        self._worker_log.setReadOnly(True)

        self._button_new = PySide2.QtWidgets.QPushButton("Start New Task...")
        self._button_new.clicked.connect(self._on_button_new_clicked)

        layout = PySide2.QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)
        layout.addWidget(self._label_worker_agent_log)
        layout.addSpacing(5)
        layout.addWidget(self._worker_agent_log)
        layout.addWidget(self._worker_agent_progress_bar)
        layout.addSpacing(10)
        layout.addWidget(self._label_worker_log)
        layout.addSpacing(5)
        layout.addWidget(self._worker_log)
        layout.addWidget(self._button_new)

        self.setStyleSheet(
            """
            QPlainTextEdit {

                font-family: Monaco, monospace;
                font-size: 14pt;
            }

            QLabel {

                font-size: 11pt;
            }
        """
        )

        self.setLayout(layout)

    def _on_button_new_clicked(self) -> None:

        self._worker_agent_progress_bar.setRange(0, 0)
        self._worker_agent_log.appendPlainText("Adding new worker...")

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

        if self._worker_agent.active_threads:
            self._worker_agent_log.appendPlainText(
                f"{self._worker_agent.active_threads} active workers..."
            )
            return

        self._worker_agent_log.appendPlainText("No active workers...")
        self._worker_agent_progress_bar.setRange(0, 1)

    def _local_callback__complete(self) -> None:
        self._worker_log.appendPlainText("Local callback called...")

    def _callback__worker_started(self, name) -> None:
        self._worker_log.appendPlainText(f"Worker `{name}` starting...")

    def _callback__worker_error(self, error) -> None:
        exception, exception_type, output = error
        self._worker_log.appendPlainText(f"Worker Error: {output}")

    def _callback__worker_result(self, result) -> None:
        self._worker_log.appendPlainText(f"Worker Result: {result}")

    def _callback__worker_complete(self, name) -> None:
        self._worker_log.appendPlainText(f"Worker `{name}` complete...")
        self._post_worker_agent_status()

    @staticmethod
    def _random_string() -> str:
        length = random.randint(5, 10)
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for l in range(length))


if __name__ == "__main__":

    app = PySide2.QtWidgets.QApplication([])

    main = MainWindow()
    main.show()

    sys.exit(app.exec_())
