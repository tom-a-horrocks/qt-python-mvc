from PySide6.QtWidgets import QLineEdit, QDialog, QPushButton, QVBoxLayout, QLabel, QCheckBox
from binding import Binder
from .controller import MainModel, MainController


class MainView(QDialog):
    """
    A simple view with a text edit and a button. Not using snake_case or
    true_property as they aren't showing in PyCharm's autocomplete yet.
    """

    def __init__(self, model: MainModel, controller: MainController):
        super(MainView, self).__init__()
        self.setWindowTitle("My Form")

        # Create widgets
        line_edit = QLineEdit()
        label = QLabel()
        check_box = QCheckBox('This is a checkbox')
        push_button = QPushButton("Disable me")

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(line_edit)
        layout.addWidget(label)
        layout.addWidget(check_box)
        layout.addWidget(push_button)
        self.setLayout(layout)

        # Bind view elements
        b = Binder(model)
        b.two_way(elements=(line_edit.text, MainModel.edit_text),
                  initial_value='Enter text here...')
        b.one_way(source=MainModel.label_text,
                  sink=label.text,
                  initial_value='Enter text here...')
        b.two_way(elements=(check_box.isChecked, MainModel.is_checked),
                  initial_value=False)
        b.one_way(source=MainModel.button_enabled,
                  sink=push_button.isEnabled)

        # Bind commands which aren't initiated by view model
        # VM bindings MUST go first to ensure controller gets the updated
        # value.
        push_button.clicked.connect(controller.disable_button)

