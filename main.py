# main.py

import sys
import warnings
import os
# Suppress requests/urllib3 version mismatch warnings
warnings.filterwarnings("ignore", message=".*urllib3.*")
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from aiagentfinder.ui.main_window import MainWindow
from aiagentfinder.utils.paths import get_resource_path


def main():
    app = QApplication(sys.argv)

    # Set the app icon so it appears in the taskbar, title bar, and Alt+Tab.
    # get_resource_path resolves to _MEIPASS when bundled, or project root in dev.
    icon_path = get_resource_path(os.path.join("data", "favicon_black_bg.ico"))
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    window = MainWindow()
    window.setWindowIcon(app_icon)   # also set on the window itself for the title bar
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
