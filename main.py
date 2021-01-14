import sys

from PySide6.QtWidgets import QApplication

from ui.view import MainView

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    main_view = MainView()
    main_view.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
