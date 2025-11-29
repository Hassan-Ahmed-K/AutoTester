from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QHBoxLayout, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QSpinBox, QComboBox,QListWidget,QSizePolicy,QSplitter,QStyle,QDateEdit,QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont 
from aiagentfinder.utils.AnitmatedToggle import AnimatedToggle
from aiagentfinder.controllers.HtmlHunter import HtmlHunterController

from aiagentfinder.ui.base_tab import BaseTab


class HtmlHunterUI(BaseTab):
    
    def __init__(self, parent=None):
        super().__init__("Html Hunter", parent)
        self.experts = {}
    def init_ui(self):

        main_layout = self.main_layout
        main_layout.setSpacing(5)

        # ---------- Header ----------
        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel("HTMLHunter")
        self.title.setStyleSheet("font-size: 40px;")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setObjectName("title")

        self.subtitle = QLabel(
            "This section filters HTML files saved by SetProcessor, grouping them by filename. "
            "You can review the HTMLs per group, select files in the table, and export set file "
            "and accompanying files (CSV, Graph Overview) to a chosen export folder. "
            "The directory structure <b>must match</b> that of SetProcessor's for exporting files."
        )
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setObjectName("subtitle")
        self.subtitle.setWordWrap(True)

        header.addWidget(self.title)
        header.addWidget(self.subtitle)
        main_layout.addLayout(header)

        # ---------- Top Layout ----------
        top_layout = QHBoxLayout()

        # Left side: Grouped Files
        left_layout = QVBoxLayout()
        self.grouped_label = QLabel("Grouped Files:")
        self.grouped_text = QListWidget()
        self.grouped_text.setStyleSheet(
           """
                QListWidget::item:selected {
                    background-color: #0078d7;  /* Blue */
                    color: white;               /* Optional */
                }
            """)
        self.grouped_text.setMinimumHeight(200)
        left_layout.addWidget(self.grouped_label)
        left_layout.addWidget(self.grouped_text)

        # Right side: Form fields
        right_layout = QGridLayout()
        right_layout.setSpacing(5)
        right_layout.setContentsMargins(0, 15, 0, 0)

        # --- HTML Directory ---
        self.lbl_html = QLabel("HTML Directory:")
        self.txt_html = QLineEdit()
        self.btn_html = QPushButton("BROWSE")
        right_layout.addWidget(self.lbl_html, 0, 0)
        right_layout.addWidget(self.txt_html, 0, 1)
        right_layout.addWidget(self.btn_html, 0, 2)

        # --- Export Directory ---
        self.lbl_export = QLabel("Export Directory:")
        self.txt_export = QLineEdit()
        self.btn_export = QPushButton("BROWSE")
        right_layout.addWidget(self.lbl_export, 1, 0)
        right_layout.addWidget(self.txt_export, 1, 1)
        right_layout.addWidget(self.btn_export, 1, 2)

        # --- Max Drawdown ---
        self.lbl_drawdown = QLabel("Max Drawdown:")
        self.txt_drawdown = QLineEdit()
        right_layout.addWidget(self.lbl_drawdown, 2, 0)
        right_layout.addWidget(self.txt_drawdown, 2, 1, 1, 2)

        # --- Min Recovery Factor ---
        self.lbl_recovery = QLabel("Min Recovery Factor:")
        self.txt_recovery = QLineEdit()
        right_layout.addWidget(self.lbl_recovery, 3, 0)
        right_layout.addWidget(self.txt_recovery, 3, 1, 1, 2)

        # --- Min Profit Factor ---
        self.lbl_profit = QLabel("Min Profit Factor:")
        self.txt_profit = QLineEdit()
        right_layout.addWidget(self.lbl_profit, 4, 0)
        right_layout.addWidget(self.txt_profit, 4, 1, 1, 2)

        # --- Target DD ---
        self.lbl_target = QLabel("Target DD:")
        self.txt_target = QLineEdit()
        right_layout.addWidget(self.lbl_target, 5, 0)
        right_layout.addWidget(self.txt_target, 5, 1, 1, 2)

        # --- Additional Exports Section ---
        export_grid = QGridLayout()

        self.hunt_toggle = AnimatedToggle(height=28, width=15)
        self.hunt_toggle.setMinimumWidth(45)
        self.hunt_toggle.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.chk_setfile = QCheckBox("Set File")
        self.chk_html = QCheckBox("HTML")
        self.chk_csv = QCheckBox("CSV")
        self.chk_graph = QCheckBox("Graph")
        self.chk_overview = QCheckBox("Overview")

        export_grid.addWidget(QLabel("Hunt for 1 Trade Approach"), 1, 1)
        export_grid.addWidget(self.hunt_toggle, 1, 2)
        export_grid.addWidget(QLabel("Additional Exports:"), 1, 3)
        export_grid.addWidget(self.chk_setfile, 1, 4)
        export_grid.addWidget(self.chk_html, 1, 5)
        export_grid.addWidget(self.chk_csv, 1, 6)
        export_grid.addWidget(self.chk_graph, 1, 7)
        export_grid.addWidget(self.chk_overview, 1, 8)

        right_layout.addLayout(export_grid, 6, 0, 1, 3)

        # --- Buttons ---
        self.btn_filter = QPushButton("FILTER FILES")
        self.btn_export_sel = QPushButton("EXPORT SELECTION")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_filter)
        btn_layout.addWidget(self.btn_export_sel)
        right_layout.addLayout(btn_layout, 7, 0, 1, 3)

        # Add to top layout
        top_layout.addLayout(left_layout)
        top_layout.addLayout(right_layout)
        main_layout.addLayout(top_layout)

        # ---------- Middle Message ----------
        self.middle_message = QTableWidget()
        main_layout.addWidget(self.middle_message)

        # ---------- Log Label Layout ----------
        log_label_layout = QVBoxLayout()
        horizontal_layout = QHBoxLayout()

        self.log_label = QLabel("Message Log:")
        self.profit_label = QLabel("Profit")
        self.profit_toggle = AnimatedToggle(height=28, width=45)
        self.rf_label = QLabel("RF")

        horizontal_layout.addWidget(self.log_label)
        horizontal_layout.addStretch()
        horizontal_layout.addWidget(self.profit_label, alignment=Qt.AlignVCenter)
        horizontal_layout.addWidget(self.profit_toggle, alignment=Qt.AlignVCenter)
        horizontal_layout.addWidget(self.rf_label, alignment=Qt.AlignVCenter)

        log_label_layout.addLayout(horizontal_layout)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(90)

        log_label_layout.addWidget(self.log_box)
        main_layout.addLayout(log_label_layout)
        

        self.controller = HtmlHunterController(self)

    def resizeEvent(self, event):
        height = self.height()
        if height > 864:    
            self.middle_message.setMaximumHeight(300)


        elif height < 768:     
            self.middle_message.setMaximumHeight(180)
            
    
        super().resizeEvent(event)







