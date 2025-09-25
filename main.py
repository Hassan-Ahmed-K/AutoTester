# main.py

import sys
import os
from PyQt5.QtWidgets import QApplication
from aiagentfinder.ui.main_window import MainWindow
from aiagentfinder.utils import Logger
from PyQt5.QtWidgets import QApplication, QMessageBox

def main():
    app = QApplication(sys.argv)

    # ✅ Test logger right away so we know logs work
    Logger.info("Application started.")

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()