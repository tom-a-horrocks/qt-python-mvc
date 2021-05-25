from .. import Observable, observable


class MainModel(Observable):

    def __init__(self):
        super().__init__()
        self._edit_text = ''
        self._label_text = ''
        self._button_enabled = False
        self._is_checked = False
        self._checked_1 = False
        self._checked_2 = False
        self._checked_3 = False

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
    def button_enabled(self) -> bool:
        return self._button_enabled

    @button_enabled.setter
    @observable
    def button_enabled(self, val: bool) -> None:
        self._button_enabled = val

    @property
    def is_checked(self) -> bool:
        return self._is_checked

    @is_checked.setter
    @observable
    def is_checked(self, val: bool) -> None:
        self._is_checked = val

    @property
    def checked_1(self) -> bool:
        return self._checked_1

    @checked_1.setter
    @observable
    def checked_1(self, val: bool) -> None:
        self._checked_1 = val

    @property
    def checked_2(self) -> bool:
        return self._checked_2

    @checked_2.setter
    @observable
    def checked_2(self, val: bool) -> None:
        self._checked_2 = val

    @property
    def checked_3(self) -> bool:
        return self._checked_3

    @checked_3.setter
    @observable
    def checked_3(self, val: bool) -> None:
        self._checked_3 = val

    def __repr__(self):
        klass = self.__class__
        prop_names = [a for a in dir(klass)
                      if type(getattr(klass, a)) == property]
        return str({n: getattr(self, n) for n in prop_names})


class MainController:

    def __init__(self, model: MainModel):
        self.model = model

    def add_callbacks(self):
        # It is possible to change controller calls from the ViewModel.
        # This will run on the UI thread(!)
        self.model.add_callback(MainModel.edit_text, self.set_label)
        # When exclusive button selection is changed, old button is set
        # False, then new button is set true. In-between, all model
        # props will be false.
        self.model.add_callback(MainModel.checked_1, self.print_selected_radio)
        self.model.add_callback(MainModel.checked_2, self.print_selected_radio)
        self.model.add_callback(MainModel.checked_3, self.print_selected_radio)

    def set_label(self):
        self.model.label_text = self.model.edit_text

    def disable_button(self):
        self.model.button_enabled = False

    def print_selected_radio(self):
        if self.model.checked_1:
            print('1')
        elif self.model.checked_2:
            print('2')
        elif self.model.checked_3:
            print('3')
        else:
            print('Called mid-selection')
