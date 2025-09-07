from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QRadioButton, QDialogButtonBox, QButtonGroup
)

class RadioDialog(QDialog):
    def __init__(self, parent=None, title="Choose Option", text="Please select an option:", options=None):
        super().__init__(parent)
        self.setWindowTitle(title)

        layout = QVBoxLayout()

        # Label
        self.label = QLabel(text)
        layout.addWidget(self.label)

        # Radio buttons
        self.button_group = QButtonGroup(self)
        self.radio_buttons = []
        if options:
            for i, option in enumerate(options):
                rb = QRadioButton(option)
                layout.addWidget(rb)
                self.button_group.addButton(rb, i)
                self.radio_buttons.append(rb)

        # OK / Cancel buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.setLayout(layout)

    def get_value(self):
        checked_id = self.button_group.checkedId()
        if checked_id != -1:
            return self.radio_buttons[checked_id].text()
        return None
