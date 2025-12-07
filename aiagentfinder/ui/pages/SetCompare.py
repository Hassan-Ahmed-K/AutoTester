from aiagentfinder.ui.base_tab import BaseTab
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QHBoxLayout, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QSpinBox, QComboBox,QListWidget,QSizePolicy,QSplitter,QStyle,QDateEdit,QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QDoubleValidator 
from aiagentfinder.utils.AnitmatedToggle import AnimatedToggle
from aiagentfinder.controllers.setCompare import SetCompareController

class SetCompareUI(BaseTab):
    
    def __init__(self, parent=None):
        super().__init__("Set Compare", parent)
        self.experts = {}
    def init_ui(self):
        
        main_layout = self.main_layout

        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        title = QLabel("SetCompare")
        title.setStyleSheet("font-size: 40px;")
        title.setAlignment(Qt.AlignCenter)
        header.addWidget(title)
        main_layout.addLayout(header)


        
        csv_label = QLabel("CSV File directory:")
        self.csv_input = QLineEdit()
        self.csv_browse = QPushButton("BROWSE")

        htm_label = QLabel("HTM File Directory:")
        self.htm_input = QLineEdit()
        self.htm_browse = QPushButton("BROWSE")

        set_label = QLabel("Set File directory:")
        self.set_input = QLineEdit()
        self.set_browse = QPushButton("BROWSE")

        draw_label = QLabel("Global Drawdown Value:")

        # QLineEdit that only accepts numbers
        self.draw_input = QLineEdit()
        self.draw_input.setText("1000")  # default value

        # Validator to only allow numbers (float)
        validator = QDoubleValidator()
        validator.setBottom(0)  # optional: minimum value 0
        self.draw_input.setValidator(validator)
        

        # Arrange first row in grid
        top_grid = QGridLayout()
        top_grid.addWidget(csv_label, 0, 1)
        top_grid.addWidget(self.csv_input, 1, 1)
        top_grid.addWidget(self.csv_browse, 1, 2)
        
        top_grid.addWidget(htm_label, 0, 4)
        top_grid.addWidget(self.htm_input, 1, 4)
        top_grid.addWidget(self.htm_browse, 1, 5)

        top_grid.addWidget(set_label, 0, 6)
        top_grid.addWidget(self.set_input, 1, 6)
        top_grid.addWidget(self.set_browse, 1, 7)

        top_grid.addWidget(draw_label, 0, 8)
        top_grid.addWidget(self.draw_input, 1, 8)
        top_grid.setColumnStretch(1, 2)
        top_grid.setColumnStretch(2, 1)
        top_grid.setColumnStretch(4, 2)
        top_grid.setColumnStretch(5, 1)
        top_grid.setColumnStretch(6, 2)
        top_grid.setColumnStretch(7, 1)
        top_grid.setColumnStretch(8, 1)


        csv_detected_label = QLabel("CSV Files Detected:")
        self.csv_list = QListWidget()
        self.csv_list.setMaximumHeight(200)

        self.deselect_button = QPushButton("DESELECT")
        self.deselect_button.setMinimumWidth(120)

        msg_label = QLabel("Message Log:")
        self.message_log = QTextEdit()
        self.message_log.setReadOnly(True)
        self.message_log.setMaximumHeight(200)

        file_grid = QGridLayout()

        # --- Row 0: Labels ---
        file_grid.addWidget(csv_detected_label, 0, 0)
        file_grid.addWidget(self.deselect_button, 0, 0, alignment = Qt.AlignRight)  # same row, aligned right
        file_grid.addWidget(msg_label, 0, 1, alignment=Qt.AlignLeft)

        # --- Row 1: Text Areas ---
        file_grid.addWidget(self.csv_list, 1, 0)
        file_grid.addWidget(self.message_log, 1, 1)

        # --- Stretch to make left side wider ---
        file_grid.setColumnStretch(0, 3)  # CSV section wide
        file_grid.setColumnStretch(1, 1)  # Message Log narrow
        file_grid.setRowStretch(1, 1)

        # --- Portfolio Stats ---
        portfolio_label = QLabel("Monthly Portfolio Stats:")
        self.portfolio_stats = QTableWidget()
        self.portfolio_stats.setMaximumHeight(50)
        # self.portfolio_stats.setReadOnly(True)

        # --- Drawdown Analysis ---
        drawdown_label = QLabel("Drawdown Overlap Analysis:")
        self.drawdown_analysis = QTableWidget()

        # --- Bottom Controls ---
        self.compare_label = QLabel("Compare files for single trade approach")
        self.compare_checkbox = QCheckBox()

        self.compare_button = QPushButton("COMPARE SET FILES")
        self.compare_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # New buttons
        self.show_graph_button = QPushButton("SHOW GRAPH")
        self.show_graph_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.show_graph_button.hide()

        self.export_profile_button = QPushButton("EXPORT PROFILE")
        self.export_profile_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.export_profile_button.hide()


        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.compare_label)
        bottom_layout.addWidget(self.compare_checkbox)
        bottom_layout.addWidget(self.compare_button)
        bottom_layout.addWidget(self.show_graph_button)
        bottom_layout.addWidget(self.export_profile_button)


        # --- Main Layout ---
        main_layout.addLayout(top_grid)
        main_layout.addLayout(file_grid)
        main_layout.addWidget(portfolio_label)
        main_layout.addWidget(self.portfolio_stats)
        main_layout.addWidget(drawdown_label)
        main_layout.addWidget(self.drawdown_analysis)
        main_layout.addLayout(bottom_layout)


        self.controller = SetCompareController(self)