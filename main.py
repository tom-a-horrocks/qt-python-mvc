import sys

from PySide6.QtWidgets import QApplication

from ui.controller import MainModel, MainController
from ui.view import MainView

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    model = MainModel()
    controller = MainController(model)
    view = MainView(model, controller)
    view.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
