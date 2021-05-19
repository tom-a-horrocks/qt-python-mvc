import functools
from collections import defaultdict
from typing import Callable


class Observable:

    def __init__(self):
        super().__init__()
        self._callbacks = defaultdict(list)
        self._ui_callbacks = defaultdict(list)
        self._ui_callbacks_enabled = defaultdict(lambda: True)

    def add_callback(self, prop: property, f: Callable[[], None], ui=False):
        callbacks_map = self._ui_callbacks if ui else self._callbacks
        callbacks_map[prop.fset.__name__].append(f)

    def disable_ui_callbacks(self, prop: property):
        self._ui_callbacks_enabled[prop.fset.__name__] = False

    def enable_ui_callbacks(self, prop: property):
        self._ui_callbacks_enabled[prop.fset.__name__] = True

    def remove_callbacks(self):
        self._callbacks.clear()
        self._ui_callbacks.clear()
        self._ui_callbacks_enabled.clear()

    def _notify(self, property_name: str):
        if self._ui_callbacks_enabled[property_name]:
            for f in self._ui_callbacks[property_name]:
                f()
        for f in self._callbacks[property_name]:
            f()


def observable(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Run setter
        func(*args, **kwargs)

        # Notify observers of update
        try:
            self, val = args
            # val is unused for the sake of symmetry with QT
            self._notify(func.__name__)
        except AttributeError:
            print(f'WARNING: no observers set for {func}. '
                  f'Did you use the Observers mixin?')

    return wrapper
