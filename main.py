import sys
from PyQt5.QtWidgets import QApplication
from AutoBatchUI import AutoBatchUI
from controller import AutoBatchController

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = AutoBatchUI()
    controller = AutoBatchController(ui)
    ui.show()
    sys.exit(app.exec_())

