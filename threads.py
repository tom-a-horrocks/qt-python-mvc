from threading import Lock
from typing import TypeVar, Optional, Callable, Any

from PySide2 import QtWidgets
from PySide2.QtCore import QObject, Signal, QThread
from PySide2.QtWidgets import QWidget


class QWidgetUpdater(QObject):
    _sig_update_widget = Signal()

    def __init__(self, widget: QWidget, widget_setter: Callable[..., None], model_getter: Callable[[], Any]):
        super().__init__()
        self._widget = widget
        self._model_getter = model_getter
        self._widget_setter = widget_setter
        self._got = None  # retrieved value from model

        self._sig_update_widget.connect(self._update_widget)

    def _update_widget(self):
        self._widget.blockSignals(True)
        self._widget_setter(self._got)
        self._widget.blockSignals(False)

    def __call__(self, *args, **kwargs):
        self._got = self._model_getter()  # Save value immediately so displayed UI value matches model at time of update
        self._sig_update_widget.emit()


class MainThread(QObject):
    T = TypeVar('T')

    # Instance (singleton)
    _instance: Optional['MainThread'] = None

    # Variables for inter-thread communication
    _updater_mutex = Lock()
    _in_widget: Optional[QWidget] = None
    _in_widget_setter: Optional[Callable[..., None]] = None
    _in_model_getter: Optional[Callable[[], Any]] = None
    _updater_out: Optional[QWidgetUpdater] = None

    # Variables for inter-thread communication of general executor
    _executor_mutex = Lock()
    _in_function: Optional[Callable[[], None]] = None

    # Signal for invoking method on main thread
    _sig_make_object = Signal()
    _sig_execute_function = Signal()

    @classmethod
    def initialise(cls) -> None:
        """
        Create the singleton. This method must be executed first, and on the main thread. This method can be enqueued
        to run upon QTApplication start by using `QTimer.singleShot(0, QWidgetUpdaterHost.initialise)`.
        """
        cls._instance = cls()

    def __init__(self):
        """
        Intended to be called by `initialise` only. Instantiates the singleton, and checks if we're on the main thread.
        If not, raises a RuntimeError.
        """
        super().__init__()
        app = QtWidgets.QApplication.instance()
        if app is None:
            print('Running without QT event queue. Callbacks will occur on the caller\'s thread, and UI bindings will '
                  'be ignored.')
        elif app.thread() != QThread.currentThread():
            raise RuntimeError('QWidgetUpdaterFactory must be created on the main thread')
        else:
            self._sig_make_object.connect(self._create_QWidgetUpdater_slot)
            self._sig_execute_function.connect(self._execute_slot)

    @classmethod
    def _execute_slot(cls):
        # Intended to be run as a slot only!
        cls._in_function()
        cls._in_function = None
        cls._executor_mutex.release()

    @classmethod
    def _create_QWidgetUpdater_slot(cls):
        # Intended to be run as a slot only!
        cls._updater_out = QWidgetUpdater(cls._in_widget, cls._in_widget_setter, cls._in_model_getter)
        cls._in_widget = None
        cls._in_widget_setter = None
        cls._in_model_getter = None
        cls._updater_mutex.release()

    @classmethod
    def execute(
            cls,
            fn: Callable[[], None],
            blocking: bool = False
    ) -> None:
        app = QtWidgets.QApplication.instance()
        if app is None or app.thread() == QThread.currentThread():
            # If already on main thread then just execute directly. This check works even if standard python threads
            # (not QThreads) are used. Function called explicitly (instead of relying on direct QT signal) as the QT
            # event queue may not be available.
            fn()
            return

        # On non-main thread
        cls._executor_mutex.acquire()  # Will be released when object is created (on main thread)
        cls._in_function = fn
        cls._instance._sig_execute_function.emit()  # releases lock

        if blocking:
            cls._executor_mutex.acquire()
            cls._executor_mutex.release()

    @classmethod
    def create_QWidgetUpdater(
            cls,
            widget: QWidget,
            widget_setter: Callable[[T], None],
            model_getter: Callable[[], T]
    ) -> Callable[[], None]:
        """
        Creates a new QWidgetUpdater. If this is called from a secondary thread, the QWidgetUpdater is created on the
         main thread via signal.
        Parameters
        ----------
        widget The widget to be updated, required so signals can be blocked during update
        widget_setter Function to be called on the widget with input from model_getter()
        model_getter Retrieves the value to be provided to widget_setter

        Returns QWidgetUpdater constructed on the main thread
        -------

        """
        app = QtWidgets.QApplication.instance()
        if app is None:
            # Headless mode; updater doesn't need to do anything.
            return lambda: None
        if app.thread() == QThread.currentThread():
            # If already on main thread then just make function directly. This check works even if standard python
            # threads (not QThreads) are used. Function called explicitly (instead of relying on direct QT signal) as
            # the QT event queue may not be available.
            return QWidgetUpdater(widget, widget_setter, model_getter)
        # On non-main thread
        # Acquire lock and set input variables. Lock will be released & inputs will be cleared on main thread.
        cls._updater_mutex.acquire()
        cls._in_widget = widget
        cls._in_widget_setter = widget_setter
        cls._in_model_getter = model_getter
        cls._instance._sig_make_object.emit()

        # Block until main thread does it's job, and get output & rest output variable.
        cls._updater_mutex.acquire()
        out = cls._updater_out
        cls._updater_out = None
        cls._updater_mutex.release()
        return out
