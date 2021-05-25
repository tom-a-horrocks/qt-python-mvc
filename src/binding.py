from collections import namedtuple
from functools import partial

from PySide2.QtWidgets import QWidget, QLineEdit, QLabel, QCheckBox, QProgressBar, QDialog

from .threads import MainThread
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


class Binder:
    """
    Class for src properties. Any src which updates the UI (i.e. source='model') _must_ be created on the
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
            # noinspection PyProtectedMember
            model._add_binding_callback(
                model_property_descriptor,
                MainThread.create_QWidgetUpdater(widget, w_setter, m_getter)
            )

        if source in ('view', 'both'):
            # noinspection PyProtectedMember
            def update_model():
                model._disable_view_bindings(model_property_descriptor)
                m_setter(w_getter())
                model._enable_view_bindings(model_property_descriptor)

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

        # Could not find src for this element
        raise RuntimeError(f'Matching setter not found for {getter_name} '
                           f'under the parent classes:  {[c.__name__ for c in widget_classes]}. '
                           f'Please add to the src module.')
