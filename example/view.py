from PySide2.QtWidgets import QLineEdit, QDialog, QPushButton, QVBoxLayout, QLabel, QCheckBox, QRadioButton

from .controller import MainModel, MainController
from .. import Binder


class MainView(QDialog):
    """
    A simple view with a text edit and a button. Not using snake_case or
    true_property as they aren't showing in PyCharm's autocomplete yet.
    """

    def __init__(self):
        super(MainView, self).__init__()
        self.setWindowTitle("My Form")

        # Create widgets
        self.line_edit = QLineEdit()
        self.label = QLabel()
        self.check_box = QCheckBox('This is a checkbox')
        self.push_button = QPushButton("Disable me")
        self.radio_buttons = [QRadioButton(f'Radio {i}') for i in range(3)]

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.line_edit)
        layout.addWidget(self.label)
        layout.addWidget(self.check_box)
        layout.addWidget(self.push_button)
        for rb in self.radio_buttons:
            layout.addWidget(rb)
        self.setLayout(layout)

    def bind_to_controller(self, controller: MainController):
        # Bind commands which aren't initiated by view model
        # VM bindings MUST go first to ensure controller gets the updated
        # value.
        self.push_button.clicked.connect(controller.disable_button)

    def bind_to_model(self, model: MainModel):
        b = Binder(model)
        b.two_way(self.line_edit.text,
                  MainModel.edit_text,
                  initial_value='Enter text here...')
        b.one_way(source=MainModel.label_text,
                  sink=self.label.text,
                  initial_value='Enter text here...')
        b.two_way(self.check_box.isChecked,
                  MainModel.is_checked,
                  initial_value=False)
        b.one_way(source=MainModel.button_enabled,
                  sink=self.push_button.isEnabled)
        b.two_way(self.radio_buttons[0].isChecked,
                  MainModel.checked_1,
                  initial_value=False)
        b.two_way(self.radio_buttons[1].isChecked,
                  MainModel.checked_2,
                  initial_value=False)
        b.two_way(self.radio_buttons[2].isChecked,
                  MainModel.checked_3,
                  initial_value=True)

