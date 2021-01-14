from enum import Enum, auto
from functools import partial

from PySide6.QtWidgets import QWidget, QLineEdit

from observable import Observable

widget_descriptors = [
    [QLineEdit.text, QLineEdit.setText, QLineEdit.textChanged],
    [QWidget.isVisible, QWidget.setVisible, None]
]


class Source(Enum):
    MODEL = auto()
    VIEW = auto()
    BOTH = auto()


_descriptors = {
    getter: (setter, signal)
    for getter, setter, signal in widget_descriptors
}


def _inflate_widget_functions(getter_descriptor, widget: QWidget):
    try:
        setter_descriptor, signal_descriptor = _descriptors[getter_descriptor]
    except KeyError:
        raise RuntimeError(
            f'Setter and signal not specified for {getter_descriptor},'
            f' please add to binding.widget_descriptors.'
        )
    return (
        getter_descriptor.__get__(widget),
        setter_descriptor.__get__(widget),
        signal_descriptor.__get__(widget) if signal_descriptor is not None else None
    )


def _inflate_model_functions(prop, model):
    # These partial classes can be eliminated for better performance
    return (
        partial(prop.fget, model),
        partial(prop.fset, model),
    )


def _bind(widget: QWidget,
          model: Observable,
          widget_getter_descriptor,
          model_property_descriptor,
          source: Source):

    widget_getter, widget_setter, widget_signal = _inflate_widget_functions(widget_getter_descriptor, widget)
    model_getter, model_setter = _inflate_model_functions(model_property_descriptor, model)

    if widget_signal is None and source in (Source.VIEW, Source.BOTH):
        raise RuntimeError(f'Binding source set to VIEW, but widget has no signal.'
                           f' Relevant setter is {widget_getter}.')

    if source in (Source.MODEL, Source.BOTH):
        def update_widget():
            widget.blockSignals(True)
            widget_setter(model_getter())
            widget.blockSignals(False)

        model.add_callback(model_property_descriptor, update_widget)

    if source in (Source.VIEW, Source.BOTH):
        def update_model():
            model.disable_callbacks(model_property_descriptor)
            model_setter(widget_getter())
            model.enable_callbacks(model_property_descriptor)

        widget_signal.connect(update_model)


def with_objects(widget: QWidget, model: Observable):
    return partial(_bind, widget, model)
