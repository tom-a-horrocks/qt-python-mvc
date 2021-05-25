import functools
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, List

from .threads import MainThread


@dataclass
class Callback:
    f: Callable[[], None]
    run_in_main_thread: bool
    is_view_binding: bool


class Observable:

    def __init__(self):
        super().__init__()
        self._callbacks: Dict[str, List[Callback]] = defaultdict(list)
        self._view_binding_callbacks_enabled = defaultdict(lambda: True)

    def add_callback(
            self,
            prop: property,
            f: Callable[[], None],
            on_main_thread=False,
            is_view_binding=False
    ) -> None:
        """
        Calls a function when a property is updated.
        Parameters
        ----------
        prop:           The property which triggers the callback when modified.
        f:              The function called when prop is changed (i.e. the callback).
        on_main_thread: Callback is guaranteed to be executed on the GUI thread if true and a QT Application
                         instance exists.
        is_view_binding: If true, this callback is *not* called if the property is modified as a part of a binding
                          update (originating from the view). Prevents cyclical updates.
        """
        self._callbacks[prop.fset.__name__].append(Callback(f=f,
                                                            run_in_main_thread=on_main_thread,
                                                            is_view_binding=False))

    def _add_binding_callback(self, prop: property, f: Callable[[], None]):
        """
        Calls a function when a property is updated. This callback is disabled by calling _disable_view_bindings.
        Parameters
        ----------
        prop:           The property which triggers the callback when modified.
        f:              The function called when prop is changed (i.e. the callback).
        """
        # No need to run callback on main thread as QWidgetUpdater (in bindings) already takes care of that.
        self._callbacks[prop.fset.__name__].append(Callback(f=f,
                                                            run_in_main_thread=False,
                                                            is_view_binding=True))

    def _disable_view_bindings(self, prop: property) -> None:
        self._view_binding_callbacks_enabled[prop.fset.__name__] = False

    def _enable_view_bindings(self, prop: property) -> None:
        self._view_binding_callbacks_enabled[prop.fset.__name__] = True

    def remove_all_callbacks(self) -> None:
        self._callbacks.clear()
        self._view_binding_callbacks_enabled.clear()

    def _notify(self, property_name: str) -> None:
        callbacks = self._callbacks[property_name]
        # ignore callbacks which bind this property to the view
        if not self._view_binding_callbacks_enabled[property_name]:
            callbacks = (c for c in callbacks if not c.is_view_binding)

        # Execute remaining callbacks
        for callback in callbacks:
            f = callback.f
            if callback.run_in_main_thread:
                MainThread.execute(f)
            else:
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
