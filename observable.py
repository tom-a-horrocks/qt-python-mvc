import functools
from collections import defaultdict
from typing import Callable


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


class Observable:

    def __init__(self):
        super().__init__()
        self._callbacks = defaultdict(list)
        self._callbacks_enabled = defaultdict(lambda: True)

    def add_callback(self, prop: property, f: Callable[[], None]):
        self._callbacks[prop.fset.__name__].append(f)

    def disable_callbacks(self, prop: property):
        self._callbacks_enabled[prop.fset.__name__] = False

    def enable_callbacks(self, prop: property):
        self._callbacks_enabled[prop.fset.__name__] = True

    def _notify(self, property_name: str):
        if self._callbacks_enabled[property_name]:
            for f in self._callbacks[property_name]:
                f()
