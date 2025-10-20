# # aiagentfinder/ui/base_tab.py
from abc import abstractmethod
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QSizePolicy,QLabel,QHBoxLayout
)
from PyQt5.QtCore import Qt
import os


class BaseTab(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        self.title = title
        
        self.load_stylesheet()
        # Outer layout
        main_layout = QVBoxLayout(self)
        self.setAutoFillBackground(True)
        main_layout.setContentsMargins(0, 0, 0, 0)
       

        # Header label
        self.topbar = QWidget()
        self.topbar.setFixedHeight(30)
        self.topbar.setStyleSheet("""
            background-color: #2b2b2b;
            border-radius: 3px;
        """)

        header_layout = QHBoxLayout(self.topbar)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.addStretch()

        main_layout.addWidget(self.topbar)

        # Scroll Area
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setStyleSheet("""
                QScrollArea {
                border: 0px;
                background: white;
            }

            QScrollBar:vertical {
                border: 0px;
                background: #e0e0e0;
                width: 2px;         /* make scrollbar thin */
                margin: 0px;
            }

            QScrollBar::handle:vertical {
                background: #888;   /* scrollbar thumb */
                min-height: 20px;
                border-radius: 3px;
            }

            QScrollBar::handle:vertical:hover {
                background: #555;   /* darker when hover */
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;        /* remove top/bottom arrows */
            }

            # QScrollBar:horizontal {
            #     border: 0px;
            #     background: #e0e0e0;
            #     height: 0px;        /* thin horizontal bar */
            #     margin: 0px;
            # }

            # QScrollBar::handle:horizontal {
            #     background: #888;
            #     min-width: 20px;
            #     border-radius: 3px;
            # }

            # QScrollBar::handle:horizontal:hover {
            #     background: #555;
            # }

            # QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            #     width: 0px;         /* remove arrows */
            # }
""")
        main_layout.addWidget(self.scroll)

        # Content widget inside scroll
        self.content = QWidget()
        self.content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Use a safe attribute name (avoid overwriting QWidget.layout())
        self.main_layout = QVBoxLayout(self.content)
        self.content.setLayout(self.main_layout)
        self.main_layout.setContentsMargins(10, 5, 10, 10)



        self.scroll.setWidget(self.content)


        self.init_ui()

    @abstractmethod
    def init_ui(self):
        """Each tab must implement this and add widgets to self.main_layout."""
        pass

    def resizeEvent(self, event):
        """Adjust scrollbars only when window is resized."""
        self.update_scrollbars()
        super().resizeEvent(event)

    def update_scrollbars(self):
            # Window not maximized → scroll only if content > viewport
        if self.content.sizeHint().height() > self.scroll.viewport().height():
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # horizontal: keep it off (vertical only)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    def load_stylesheet(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))  
        qss_path = os.path.join(base_dir, "style", "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"⚠️ QSS file not found at {qss_path}")

