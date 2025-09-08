# aiagentfinder/ui/base_tab.py
from abc import abstractmethod
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QPalette, QColor


class BaseTab(QWidget):
    """Abstract base class for tabs."""
    

    def __init__(self, title: str, parent=None):
        super().__init__(parent)

        self.title = title
        self.layout = QVBoxLayout(self)
        self.setAutoFillBackground(True)
        self.layout.setContentsMargins(5, 5 , 5, 5)

        self.setStyleSheet("background-color: #1e1e1e;") 
        self.init_ui()   #

    @abstractmethod
    def init_ui(self):
        """Each tab must implement this."""
        pass
