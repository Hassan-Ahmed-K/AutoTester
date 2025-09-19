# aiagentfinder/ui/main_window.py

from PyQt5.QtWidgets import QMainWindow, QTabWidget , QScrollArea, QSizePolicy
from aiagentfinder.ui.pages.AutoBatchUI import AutoBatchUI
from PyQt5.QtCore import Qt , QEvent
# Import more tabs here as needed
# from aiagentfinder.ui.pages.other_tab import OtherTabUI


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.tabs = QTabWidget()
        self.tabs.addTab(AutoBatchUI(), "Auto Batch")
        # self.tabs.addTab(OtherTabUI(), "Other Tab")

        # Make the QTabWidget pane transparent so each tab's background shows
        self.tabs.setStyleSheet("""
                QTabWidget::pane {
                    border: 0;
                    background: #1e1e1e; /* set the main tab area background */
                }
                QTabBar::tab {
                    background: #2b2b2b;
                    color: #e0dcdc;
                    padding: 5px;
                }
                QTabBar::tab:selected {
                    background: #3c3c3c;
                }
            """)


        # self.tabs.setStyleSheet("QTabWidget::pane { background: transparent; }")

        self.setCentralWidget(self.tabs)
        self.tabs = QTabWidget()
    

        