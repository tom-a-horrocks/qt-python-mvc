import sys

from PySide6.QtWidgets import QApplication

from ui.controller import MainViewModel, MainController
from ui.view import MainView

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    view_model = MainViewModel()
    controller = MainController(view_model)
    view = MainView(view_model, controller)
    view.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
