# main.py

import sys
import warnings
# Suppress requests/urllib3 version mismatch warnings
warnings.filterwarnings("ignore", message=".*urllib3.*")
from PyQt5.QtWidgets import QApplication
from aiagentfinder.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
