from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox

class TextDialog(QDialog):

    def __init__(self, parent=None, title="Strategy Name", text="Please Name Strategy"):
        super().__init__(parent)
        self.setWindowTitle(title)

        layout = QVBoxLayout()

        # Label
        self.label = QLabel(text)
        layout.addWidget(self.label)

        # Text input field
        self.text_input = QLineEdit()
        layout.addWidget(self.text_input)  

        # OK / Cancel buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.setLayout(layout)

    def get_value(self):
        return self.text_input.text()
