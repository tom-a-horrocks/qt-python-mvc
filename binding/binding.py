from collections import namedtuple
from functools import partial

from PySide6.QtWidgets import QWidget, QLineEdit, QLabel, QCheckBox
from .observable import Observable

D = namedtuple('Descriptors', 'getter setter signal')

# This list relates (unbound) widget getters to the related setters and
# update signal (where it exists).
qt_getter_setter_signals = [
    D(getter=QLineEdit.text,    setter=QLineEdit.setText,  signal=QLineEdit.textChanged),
    D(getter=QLabel.text,       setter=QLabel.setText,     signal=None),
    D(getter=QWidget.isVisible, setter=QWidget.setVisible, signal=None),
    D(getter=QWidget.isEnabled, setter=QWidget.setEnabled, signal=None),
    D(getter=QCheckBox.isChecked, setter=QCheckBox.setChecked, signal=QCheckBox.toggled),
]


class Binder:
    _descriptors = {
        getter: (setter, signal)
        for getter, setter, signal in qt_getter_setter_signals
    }

    def __init__(self, model: Observable):
        self.model = model

    def two_way(self, elements, initial_value=None):
        assert len(elements) == 2, "Can only bind two elements at a time"
        widget_getter, model_prop = self._identify(*elements)
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
                   model_prop,
                   source,
                   initial_value)

    @staticmethod
    def _inflate(getter_descriptor, setter_descriptor, signal_descriptor, widget):
        return (
            getter_descriptor.__get__(widget),
            setter_descriptor.__get__(widget),
            signal_descriptor.__get__(widget) if signal_descriptor is not None else None
        )

    @staticmethod
    def _inflate_model_functions(prop, model):
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
            def update_widget():
                widget.blockSignals(True)
                w_setter(m_getter())
                widget.blockSignals(False)

            model.add_callback(model_property_descriptor, update_widget, ui=True)

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
                return getter_descriptor, *cls._descriptors[getter_descriptor]
            except (AttributeError, KeyError):
                # AttributeError: missing descriptor
                # KeyError: no entry for given descriptor
                pass

        # Could not find binding for this element
        raise RuntimeError(f'Matching setter not found for {getter_name} '
                           f'under the parent classes:  {[c.__name__ for c in widget_classes]}. '
                           f'Please add to the binding module.')
