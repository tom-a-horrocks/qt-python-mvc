from binding import Observable, observable


class MainViewModel(Observable):

    def __init__(self):
        super().__init__()
        self._edit_text = ''
        self._label_text = ''
        self._button_enabled = False

    @property
    def edit_text(self) -> str:
        return self._edit_text

    @edit_text.setter
    @observable
    def edit_text(self, val: str) -> None:
        self._edit_text = val

    @property
    def label_text(self) -> str:
        return self._label_text

    @label_text.setter
    @observable
    def label_text(self, val: str) -> None:
        self._label_text = val

    @property
    def button_enabled(self) -> str:
        return self._button_enabled

    @button_enabled.setter
    @observable
    def button_enabled(self, val: bool) -> None:
        self._button_enabled = val


class MainController:

    def __init__(self, vm: MainViewModel):
        self.vm = vm

        # It is possible to change controller calls from the ViewModel.
        # This will run on the UI thread(!)
        self.vm.add_callback(MainViewModel.edit_text, self.set_label)

    def set_label(self):
        self.vm.label_text = self.vm.edit_text

    def disable_button(self):
        self.vm.button_enabled = False
