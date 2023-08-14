# MVC Architecture in PySide2 (or Pyside6)
Qt for Python is an excellent way to create native-looking GUIs for your python application.
However, you may prefer the _properties and bindings_ approach to UI programming over Qt's _signals and slots_. 
This repository implements bindings using signals and slots behind the scenes, and gives an example of how to fit it all together in a model-view-controller (MVC) architecture.

*Warning:* This framework is under active development and the API is likely to change.

## Components
### Model
The model is a simple class that exposes your program's state through properties. 
These properties can be modified directly (e.g. by a Controller), or through bindings (see the View section).
All that is required is that your model uses the `Observable` mix-in and the `@observable` decorator on property _setters_, as demonstrated below. This component is _Qt-free_.
```python
class Model(Observable):

    def __init__(self):
        super().__init__()
        self._edit_text = ''
        self._label_text = ''
        self._button_enabled = False

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
```

### Controller
The controller simply runs commands against the model. 
If you wish, you can also trigger commands when the model is updated.
This component is also _Qt-free_.
```python
class Controller:

    def __init__(self, model: Model):
        self.model = model
        # call 'set_label' when the model's 'edit_text' property changes.
        self.model.add_callback(Model.edit_text, self.set_label)
    
    def set_label(self):
        self.model.label_text = self.model.edit_text

    def disable_button(self):
        self.model.button_enabled = False
```

### View
The view is a typical Qt container. However, it is now also possible to bind widgets to class properties (e.g. the model):
```python
class View(QDialog):
    super(View, self).__init__()
    
    # Declare widgets
    line_edit = QWidget()
    push_button = QPushButton()
    push_button = QPushButton("Disable me")
    
    # Create layout and add widgets
    layout = QVBoxLayout()
    layout.addWidget(line_edit)
    layout.addWidget(label)
    layout.addWidget(push_button)
    self.setLayout(layout)

    # Define bindings with optional initial values.
    # If there are no initial values, model and view will be out of sync.
    model = Model()
    b = Binder(model)
    b.two_way(element1=line_edit.text, 
              element2=Model.edit_text,
              initial_value='Enter text here...')
    b.one_way(source=Model.button_enabled,
              sink=push_button.isEnabled)
    
    # Define controller bindings AFTER view element bindings above, or the
    # model won't be guaranteed to match the view's state.
    controller = Controller(model)
    push_button.clicked.connect(controller.disable_button)
```

The Binder looks up the Qt widget's setter and update signal based on a predefined list in `qt_getter_setter_signals`.

