from PySide6.QtWidgets import QLineEdit, QDialog, QPushButton, QVBoxLayout

from binding import Binder
from .controller import MainViewModel


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
        self.push_button = QPushButton("Show Greetings")

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.line_edit)
        layout.addWidget(self.push_button)

        # Set dialog layout
        self.setLayout(layout)

        # Bindings
        self.vm = MainViewModel()

        b = Binder(self.vm)
        b.two_way(self.line_edit.text, MainViewModel.text)
        b.one_way(MainViewModel.button_visible, self.push_button.isVisible)

        # Defaults
        self.vm.text = 'Initial text'
        self.vm.button_visible = False
