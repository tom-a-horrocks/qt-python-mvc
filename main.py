import sys

from PySide6.QtWidgets import QApplication

from ui.controller import MainModel, MainController
from ui.view import MainView

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)

    # Instantiate MVC classes and set bindings.
    # Binding order matters so that view and model are consistent:
    # (1) V<->M; (2) C<->M; (3) V<->C
    model = MainModel()
    view = MainView()
    view.bind_to_model(model)
    controller = MainController(model)
    controller.add_callbacks()
    view.bind_to_controller(controller)

    # Show and run QT loop
    view.show()
    sys.exit(app.exec_())
