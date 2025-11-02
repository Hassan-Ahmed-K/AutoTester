from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QHBoxLayout, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QSpinBox, QComboBox,QListWidget,QSizePolicy,QSplitter,QStyle,QDateEdit,QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont 
from aiagentfinder.utils.AnitmatedToggle import AnimatedToggle

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

        title = QLabel("HTMLHunter")
        title.setStyleSheet("font-size: 40px;")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")

        subtitle = QLabel(
            "This section filters HTML files saved by SetProcessor, grouping them by filename. "
            "You can review the HTMLs per group, select files in the table, and export set file "
            "and accompanying files (CSV, Graph Overview) to a chosen export folder. "
            "The directory structure <b>must match</b> that of SetProcessor's for exporting files."
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)

        header.addWidget(title)
        header.addWidget(subtitle)
        main_layout.addLayout(header)

        # ---------- Top Layout ----------
        top_layout = QHBoxLayout()

        # Left side: Grouped Files
        left_layout = QVBoxLayout()
        grouped_label = QLabel("Grouped Files:")
        grouped_text = QTextEdit()
        grouped_text.setReadOnly(True)
        grouped_text.setMinimumHeight(200)
        left_layout.addWidget(grouped_label)
        left_layout.addWidget(grouped_text)

        # Right side: Form fields
        right_layout = QGridLayout()
        right_layout.setSpacing(5)
        right_layout.setContentsMargins(0, 15, 0, 0)

        # --- HTML Directory ---
        lbl_html = QLabel("HTML Directory:")
        txt_html = QLineEdit()
        btn_html = QPushButton("BROWSE")
        right_layout.addWidget(lbl_html, 0, 0)
        right_layout.addWidget(txt_html, 0, 1)
        right_layout.addWidget(btn_html, 0, 2)

      

        # --- Export Directory ---
        lbl_export = QLabel("Export Directory:")
        txt_export = QLineEdit()
        btn_export = QPushButton("BROWSE")
        right_layout.addWidget(lbl_export, 1, 0)
        right_layout.addWidget(txt_export, 1, 1)
        right_layout.addWidget(btn_export, 1, 2)

        # --- Max Drawdown ---
        lbl_drawdown = QLabel("Max Drawdown:")
        txt_drawdown = QLineEdit()
        right_layout.addWidget(lbl_drawdown, 2, 0)
        right_layout.addWidget(txt_drawdown, 2, 1,1, 2)

        # --- Min Recovery Factor ---
        lbl_recovery = QLabel("Min Recovery Factor:")
        txt_recovery = QLineEdit()
        right_layout.addWidget(lbl_recovery, 3, 0)
        right_layout.addWidget(txt_recovery, 3, 1,1, 2)

        # --- Min Profit Factor ---
        lbl_profit = QLabel("Min Profit Factor:")
        txt_profit = QLineEdit()
        right_layout.addWidget(lbl_profit, 4, 0)
        right_layout.addWidget(txt_profit, 4, 1,1, 2)

        # --- Target DD ---
        lbl_target = QLabel("Target DD:")
        txt_target = QLineEdit()
        right_layout.addWidget(lbl_target, 5, 0)
        right_layout.addWidget(txt_target, 5, 1,1, 2)


        # --- Additional Exports Section in Separate Grid ---
        export_grid = QGridLayout()
        hunt_toggle = AnimatedToggle(height=28, width=15)
        hunt_toggle.setMinimumWidth(45)  
        hunt_toggle.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        chk_setfile = QCheckBox("Set File")
        chk_html = QCheckBox("HTML")
        chk_csv = QCheckBox("CSV")
        chk_graph = QCheckBox("Graph")
        chk_overview = QCheckBox("Overview")
        export_grid.addWidget(QLabel("Hunt for 1 Trade Approach"),1,1)
        export_grid.addWidget(hunt_toggle,1,2)
        export_grid.addWidget(QLabel("Additional Exports:"),1,3)
        export_grid.addWidget(chk_setfile,1,4)
        export_grid.addWidget(chk_html,1,5)
        export_grid.addWidget(chk_csv,1,6)
        export_grid.addWidget(chk_graph,1,7)
        export_grid.addWidget(chk_overview,1,8)
    

        # Add the export grid to the main left layout
        right_layout.addLayout(export_grid, 6, 0, 1, 3)


        # --- Buttons ---
        btn_filter = QPushButton("FILTER FILES")
        btn_export_sel = QPushButton("EXPORT SELECTION")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_filter)
        btn_layout.addWidget(btn_export_sel)
        right_layout.addLayout(btn_layout, 7, 0, 1, 3)

        # Add to top layout
        top_layout.addLayout(left_layout)
        top_layout.addLayout(right_layout)
        main_layout.addLayout(top_layout)

        # ---------- Middle Message ----------
        middle_message = QTextEdit()
        middle_message.setReadOnly(True)
        main_layout.addWidget(middle_message)

        # ---------- Log Label Layout ----------
        log_label_layout = QVBoxLayout()
        horizontal_layout = QHBoxLayout()
        log_label = QLabel("Message Log:")
        profit_label = QLabel("Profit")
        profit_toggle = AnimatedToggle(height=28,width=45)
       
        rf_label = QLabel("RF")

        horizontal_layout.addWidget(log_label)
        horizontal_layout.addStretch()
        horizontal_layout.addWidget(profit_label, alignment=Qt.AlignVCenter)
        horizontal_layout.addWidget(profit_toggle, alignment=Qt.AlignVCenter)
        horizontal_layout.addWidget(rf_label, alignment=Qt.AlignVCenter)


        log_label_layout.addLayout(horizontal_layout)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(90)

        log_label_layout.addWidget(self.log_box)

        main_layout.addLayout(log_label_layout)

    def resizeEvent(self, event):
        height = self.height()
        if height > 864:    
            self.log_box.setMaximumHeight(120)
        
        super().resizeEvent(event)






