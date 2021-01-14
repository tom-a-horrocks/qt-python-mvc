from PySide6.QtWidgets import QLineEdit, QDialog, QPushButton, QVBoxLayout, QLabel

from binding import Binder
from .controller import MainViewModel, MainController


class MainView(QDialog):
    """
    A simple view with a text edit and a button. Not using snake_case or
    true_property as they aren't showing in PyCharm's autocomplete yet.
    """

    def __init__(self, vm: MainViewModel, controller: MainController):
        super(MainView, self).__init__()
        self.setWindowTitle("My Form")

        # Create widgets
        line_edit = QLineEdit()
        label = QLabel()
        push_button = QPushButton("Disable me")

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(line_edit)
        layout.addWidget(label)
        layout.addWidget(push_button)
        self.setLayout(layout)

        # Bind view elements
        b = Binder(vm)
        b.two_way(elements=(line_edit.text, MainViewModel.edit_text),
                  initial_value='Enter text here...')
        b.one_way(source=MainViewModel.label_text,
                  sink=label.text,
                  initial_value='Enter text here...')
        b.one_way(source=MainViewModel.button_enabled,
                  sink=push_button.isEnabled)

        # Bind commands which aren't initiated by view model
        # VM bindings MUST go first to ensure controller gets the updated
        # value.
        push_button.clicked.connect(controller.disable_button)

