from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QSpinBox, QDialogButtonBox

class QuantityDialog(QDialog):
    def __init__(self, parent=None, title="Test Pairs", text="How many pairs will be in you test list: "):
        super().__init__(parent)
        self.setWindowTitle(title)

        layout = QVBoxLayout()

        # Label
        self.label = QLabel(text)
        layout.addWidget(self.label)

        # Quantity input (QSpinBox allows only numbers)
        self.spin_box = QSpinBox()
        self.spin_box.setRange(1, 100000)  # min, max
        self.spin_box.setValue(1)        # default value
        layout.addWidget(self.spin_box)

        # OK / Cancel buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.setLayout(layout)

    def get_value(self):
        return self.spin_box.value()
