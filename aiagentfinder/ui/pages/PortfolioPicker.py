from aiagentfinder.ui.base_tab import BaseTab
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QHBoxLayout, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QSpinBox, QComboBox,QListWidget,QSizePolicy,QSplitter,QStyle,QDateEdit,QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont 
from aiagentfinder.utils.AnitmatedToggle import AnimatedToggle


class PortfolioPickerUI(BaseTab):
    
    def __init__(self, parent=None):
        super().__init__("Portfolio Picker", parent)
        self.experts = {}
    def init_ui(self):
        
        main_layout = self.main_layout

        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Portfolio Picker")
        title.setStyleSheet("font-size: 40px;")
        title.setAlignment(Qt.AlignCenter)
        header.addWidget(title)
        main_layout.addLayout(header)

        csv_label = QLabel("CSV File directory:")
        self.csv_dir = QLineEdit()
        csv_browse = QPushButton("BROWSE")

        html_label = QLabel("HTML File Directory:")
        self.html_dir = QLineEdit()
        html_browse = QPushButton("BROWSE")

        set_label = QLabel("Set File directory:")
        self.set_dir = QLineEdit()
        set_browse = QPushButton("BROWSE")

        # Top layout
        top_grid = QGridLayout()
        top_grid.addWidget(csv_label, 0, 1)
        top_grid.addWidget(self.csv_dir, 1, 1)
        top_grid.addWidget(csv_browse, 1, 2)
        top_grid.addWidget(html_label,  0, 3)
        top_grid.addWidget(self.html_dir, 1, 3)
        top_grid.addWidget(html_browse, 1, 4)
        top_grid.addWidget(set_label, 0, 5)
        top_grid.addWidget(self.set_dir, 1, 5)
        top_grid.addWidget(set_browse, 1, 6)
        top_grid.setColumnStretch(1,3)
        top_grid.setColumnStretch(2,2)
        top_grid.setColumnStretch(3,3)
        top_grid.setColumnStretch(4,2)
        top_grid.setColumnStretch(5,3)
        top_grid.setColumnStretch(6,2)
        main_layout.addLayout(top_grid)


        self.num_portfolios = QSpinBox()
        self.num_portfolios.setRange(1, 9999)
        self.num_portfolios.setValue(10)

        self.max_sets = QSpinBox()
        self.max_sets.setRange(1, 1000)

        self.peak_dd = QLineEdit("1000")
        self.max_same_symbol = QSpinBox()
        self.max_same_symbol.setRange(1, 1000)
        self.allow_duplicate = QCheckBox()

        self.api_key = QLineEdit()
        build_single_trade = QCheckBox()
        build_btn = QPushButton("BUILD PORTFOLIOS")

        # Row layout
        options_grid = QGridLayout()
        options_grid.addWidget(QLabel("No of Portfolios:"), 0, 0)
        options_grid.addWidget(self.num_portfolios, 0, 1)
        options_grid.addWidget(QLabel("Max Sets in Portfolio:"), 0, 2)
        options_grid.addWidget(self.max_sets,0,3)
        options_grid.addWidget(QLabel("Peak Portfolio DD:"), 0, 4)
        options_grid.addWidget(self.peak_dd, 0, 5)
        options_grid.addWidget(QLabel("Max Same Symbol Use:"), 0, 6)
        options_grid.addWidget(self.max_same_symbol, 0, 7)
        options_grid.addWidget(QLabel("Allow same set more than once:"),0, 8)
        options_grid.addWidget(self.allow_duplicate, 0, 9)
        options_grid.setColumnStretch(3,2)
        options_grid.setColumnStretch(5,2)
        options_grid.setColumnStretch(7,2)
        

        api_grid = QGridLayout()
        api_grid.addWidget(QLabel("Portfolio API Key:"), 1, 0)
        api_grid.addWidget(self.api_key, 1, 1)
        api_grid.addWidget(QLabel("Build for single trade approach"), 1, 2)
        api_grid.addWidget(build_single_trade, 1, 3)
        api_grid.addWidget(build_btn, 1, 4)
        api_grid.setColumnStretch(1,5)
        api_grid.setColumnStretch(4,5)


        # ----------------------------- TEXT AREAS -----------------------------
        portfolios_label = QLabel("Portfolios Created:")
        self.portfolios_created = QTextEdit()
        self.portfolios_created.setReadOnly(True)

        setfiles_label = QLabel("Set Files Used:")
        self.set_files_used = QTextEdit()
        self.set_files_used.setReadOnly(True)

        text_grid = QGridLayout()
        text_grid.addWidget(portfolios_label, 0, 0)
        text_grid.addWidget(setfiles_label, 0, 1)
        text_grid.addWidget(self.portfolios_created, 1, 0)
        text_grid.addWidget(self.set_files_used, 1, 1)

        text_grid.setColumnStretch(0, 1)
        text_grid.setColumnStretch(1, 1)

        # ----------------------------- MONTHLY + DRAW -----------------------------
        monthly_label = QLabel("Monthly Portfolio Stats:")
        self.monthly_stats = QTextEdit()
        self.monthly_stats.setMaximumHeight(90)
        self.monthly_stats.setReadOnly(True)

        draw_label = QLabel("Global Drawdown Value:")
        self.draw_input = QLineEdit("1000")
        analyze_btn = QPushButton("ANALYZE")

        top_draw_grid = QGridLayout()
        top_draw_grid.addWidget(monthly_label, 0, 0)
        top_draw_grid.addWidget(draw_label, 0, 1)
        top_draw_grid.addWidget(self.draw_input, 0, 2)
        top_draw_grid.addWidget(analyze_btn, 0, 3)
        top_draw_grid.addWidget(self.monthly_stats, 1, 0, 1, 4)
        
        top_draw_grid.setColumnStretch(0, 4)
        top_draw_grid.setColumnStretch(2, 4)
        top_draw_grid.setColumnStretch(1, 1)

        # ----------------------------- DRAWDOWN OVERLAP -----------------------------
        drawdown_label = QLabel("Drawdown Overlap Analysis:")
        self.drawdown_analysis = QTextEdit()
        self.drawdown_analysis.setReadOnly(True)

        # ----------------------------- BOTTOM BUTTONS -----------------------------
        export_btn = QPushButton("EXPORT PROFILE")
        show_graph_btn = QPushButton("SHOW GRAPH")

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(export_btn)
        bottom_layout.addWidget(show_graph_btn)

        # main_layout.addLayout(top_grid)
        main_layout.addSpacing(5)
        main_layout.addLayout(options_grid)
        main_layout.addSpacing(5)
        main_layout.addLayout(api_grid)
        main_layout.addSpacing(5)
        main_layout.addLayout(text_grid)
        main_layout.addSpacing(5)
        main_layout.addLayout(top_draw_grid)
        main_layout.addWidget(drawdown_label)
        main_layout.addWidget(self.drawdown_analysis)
        main_layout.addLayout(bottom_layout)


    def resizeEvent(self, event):
        height = self.height()
        if height > 864:    
           self.monthly_stats.setMaximumHeight(120)
        
        super().resizeEvent(event)
