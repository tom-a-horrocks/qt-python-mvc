from binding import Observable, observable


class MainViewModel(Observable):

    def __init__(self):
        super().__init__()
        self._text = ''
        self._button_visible = False

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    @observable
    def text(self, val: str) -> None:
        self._text = val

    @property
    def button_visible(self) -> str:
        return self._button_visible

    @button_visible.setter
    @observable
    def button_visible(self, val: bool) -> None:
        self._button_visible = val
