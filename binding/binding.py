from collections import namedtuple
from functools import partial
from threading import Lock
from typing import Any, Callable, Optional, TypeVar

from PySide2 import QtWidgets
from PySide2.QtCore import QObject, Signal, QThread
from PySide2.QtWidgets import QWidget, QLineEdit, QLabel, QCheckBox, QProgressBar, QDialog

from .observable import Observable
from .widget import BindableQTableWidget

D = namedtuple('Descriptors', 'getter setter update_signal')

# This list relates (unbound) widget getters to the related setters and
# update signal (where it exists).
qt_getter_setter_signals = [
    D(getter=QLineEdit.text,                  setter=QLineEdit.setText,               update_signal='textChanged'),
    D(getter=QLabel.text,                     setter=QLabel.setText,                  update_signal=None),
    D(getter=QWidget.isVisible,               setter=QWidget.setVisible,              update_signal=None),
    D(getter=QWidget.isEnabled,               setter=QWidget.setEnabled,              update_signal=None),
    D(getter=QCheckBox.isChecked,             setter=QCheckBox.setChecked,            update_signal='toggled'),
    D(getter=BindableQTableWidget.text_items, setter=BindableQTableWidget.set_data,   update_signal=None),
    D(getter=BindableQTableWidget.QT_items,   setter=BindableQTableWidget.set_data,   update_signal=None),
    D(getter=QProgressBar.value,              setter=QProgressBar.setValue,           update_signal=None),
    D(getter=QProgressBar.maximum,            setter=QProgressBar.setMaximum,         update_signal=None),
    D(getter=QDialog.result,                  setter=QDialog.setResult,               update_signal='finished')
]


class QWidgetUpdater(QObject):

    _sig_update_widget = Signal()

    def __init__(self, widget: QWidget, widget_setter: Callable[..., None], model_getter: Callable[[], Any]):
        super().__init__()
        self._widget = widget
        self._model_getter = model_getter
        self._widget_setter = widget_setter
        self._got = None  # retrieved value from model

        self._sig_update_widget.connect(self.update_widget)

    def update_widget(self):
        self._widget.blockSignals(True)
        self._widget_setter(self._got)
        self._widget.blockSignals(False)

    def __call__(self, *args, **kwargs):
        self._got = self._model_getter()  # Save value immediately so displayed UI value matches model at time of update
        self._sig_update_widget.emit()


class QWidgetUpdaterFactory(QObject):
    T = TypeVar('T')

    # Instance (singleton)
    _instance: Optional['QWidgetUpdaterFactory'] = None

    # Variables for inter-thread communication
    _mutex = Lock()
    _in_widget: Optional[QWidget] = None
    _in_widget_setter: Optional[Callable[..., None]] = None
    _in_model_getter: Optional[Callable[[], Any]] = None
    _out_updater: Optional[QWidgetUpdater] = None

    # Signal for invoking method on main thread
    _sig_make_object = Signal()

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
        if app.thread() != QThread.currentThread():
            raise RuntimeError('QWidgetUpdaterFactory must be created on the main thread')

        self._sig_make_object.connect(self._create_QWidgetUpdater_on_main_thread)
    
    @classmethod
    def _create_QWidgetUpdater_on_main_thread(cls):
        # Intended to be run as a slot only!
        cls._out_updater = QWidgetUpdater(cls._in_widget, cls._in_widget_setter, cls._in_model_getter)
        cls._mutex.release()
    
    @classmethod
    def create_QWidgetUpdater(
            cls,
            widget: QWidget,
            widget_setter: Callable[[T], None],
            model_getter: Callable[[], T]
    ) -> QWidgetUpdater:
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
        if app.thread() == QThread.currentThread():
            # If already on main thread then just make object directly.
            # This check works even if standard python threads (not QThreads) are used.
            return QWidgetUpdater(widget, widget_setter, model_getter)

        # On non-main thread
        cls._mutex.acquire()  # Will be released when object is created (on main thread)
        cls._in_widget = widget
        cls._in_widget_setter = widget_setter
        cls._in_model_getter = model_getter
        cls._instance._sig_make_object.emit()  # Places object in _out_updater and releases lock

        cls._mutex.acquire()  # Blocks until object is created
        out = cls._out_updater
        cls._in_widget = None
        cls._in_widget_setter = None
        cls._in_model_getter = None
        cls._out_updater = None
        cls._mutex.release()
        return out


class Binder:
    """
    Class for binding properties. Any binding which updates the UI (i.e. source='model') _must_ be created on the
    main thread.
    """

    _descriptors = {
        getter: (setter, signal)
        for getter, setter, signal in qt_getter_setter_signals
    }

    def __init__(self, model: Observable):
        self.model = model

    def two_way(self, element1, element2, initial_value=None):
        widget_getter, model_prop = self._identify(element1, element2)
        self._bind(widget_getter.__self__,
                   self.model,
                   *self._get_descriptors(widget_getter),
                   model_prop,
                   'both',
                   initial_value)

    def one_way(self, source, sink, initial_value=None):
        widget_getter, model_prop = self._identify(source, sink)
        source = 'model' if source == model_prop else 'view'
        self._bind(widget_getter.__self__,
                   self.model,
                   *self._get_descriptors(widget_getter),
                   model_property_descriptor=model_prop,
                   source=source,
                   initial_value=initial_value)

    @staticmethod
    def _inflate(getter_descriptor, setter_descriptor, signal_name, widget: QWidget):
        # signal retrieved dynamically (via string) because it resolves as a class attribute, so can't be used
        # as a descriptor.
        return (
            getter_descriptor.__get__(widget),
            setter_descriptor.__get__(widget),
            widget.__getattribute__(signal_name) if signal_name is not None else None
        )

    @staticmethod
    def _inflate_model_functions(prop: property, model):
        # These partial classes can be eliminated for better performance
        return (
            partial(prop.fget, model),
            partial(prop.fset, model),
        )

    @classmethod
    def _bind(cls,
              widget: QWidget,
              model: Observable,
              widget_getter_descriptor,
              widget_setter_descriptor,
              widget_signal_descriptor,
              model_property_descriptor,
              source: str,
              initial_value):
        w_getter, w_setter, w_sig = cls._inflate(widget_getter_descriptor,
                                                 widget_setter_descriptor,
                                                 widget_signal_descriptor,
                                                 widget)

        m_getter, m_setter = cls._inflate_model_functions(model_property_descriptor,
                                                          model)

        if initial_value is not None:
            w_setter(initial_value)
            m_setter(initial_value)

        if w_sig is None and source in ('view', 'both'):
            raise RuntimeError(
                f'Binding '
                f'"{type(widget).__name__}.{w_getter.__name__}" '
                f'-> '
                f'"{type(model).__name__}.{model_property_descriptor.fget.__name__}" '
                f'is missing a signal in qt_getter_setter_signals.')

        if source in ('model', 'both'):
            # Note that callback will get model value -just- before update, not necessarily of model value at change.
            model.add_callback(
                model_property_descriptor,
                QWidgetUpdaterFactory.create_QWidgetUpdater(widget, w_setter, m_getter),
                ui=True
            )

        if source in ('view', 'both'):
            def update_model():
                model.disable_ui_callbacks(model_property_descriptor)
                m_setter(w_getter())
                model.enable_ui_callbacks(model_property_descriptor)

            w_sig.connect(update_model)

    @staticmethod
    def _identify(arg1, arg2):
        """
        Identify the property and the method from the mixed args.
        :param arg1: Either a property descriptor or a bound method.
        :param arg2: Either a property descriptor or a bound method.
        :return: The bound method and the property descriptor, in that order.
        """
        if callable(arg1) and type(arg2) is property:
            return arg1, arg2
        if type(arg1) is property and callable(arg2):
            return arg2, arg1
        raise RuntimeError('Expected a function and a model property, '
                           f'but received {type(arg1)} and {type(arg2)}')

    @classmethod
    def _get_descriptors(cls, widget_getter):
        """
        Retrieves the descriptors for a widget's getter, setter, and signal
        functions. Signal descriptor will be None if no matching signal
        is found.
        :param widget_getter: The (bound) widget's getter method
        :return: Descriptors of the getter, setter, and signal
        """
        # Look up widget class details
        getter_name = widget_getter.__name__
        widget_obj = widget_getter.__self__
        widget_classes = type(widget_obj).mro()

        # Look up matching setter and signal descriptors.
        # If they are missing for the widget class in the dictionary,
        # check under the parent classes instead.
        for klass in widget_classes:
            try:
                getter_descriptor = getattr(klass, getter_name)
                if not callable(getter_descriptor):
                    continue
                out = getter_descriptor, *cls._descriptors[getter_descriptor]
                return out
            except (AttributeError, KeyError):
                # AttributeError: missing descriptor
                # KeyError: no entry for given descriptor
                pass

        # Could not find binding for this element
        raise RuntimeError(f'Matching setter not found for {getter_name} '
                           f'under the parent classes:  {[c.__name__ for c in widget_classes]}. '
                           f'Please add to the binding module.')
