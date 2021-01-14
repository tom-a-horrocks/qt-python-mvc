from PySide6.QtWidgets import QLineEdit, QDialog, QPushButton, QVBoxLayout, QWidget
import binding


from binding import Source
from controller import MainViewModel


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

        bind = binding.with_objects(self.line_edit, self.vm)
        bind(QLineEdit.text, MainViewModel.text, Source.BOTH)
        bind = binding.with_objects(self.push_button, self.vm)
        bind(QWidget.isVisible, MainViewModel.button_visible, Source.MODEL)

        # Defaults
        self.vm.text = 'Initial text'
        self.vm.button_visible = False



