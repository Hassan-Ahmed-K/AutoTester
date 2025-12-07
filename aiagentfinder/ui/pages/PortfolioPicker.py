from aiagentfinder.ui.base_tab import BaseTab
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QHBoxLayout, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QSpinBox, QComboBox,QListWidget,QSizePolicy,QSplitter,QStyle,QDateEdit,QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QDoubleValidator
from aiagentfinder.utils.AnitmatedToggle import AnimatedToggle

from aiagentfinder.controllers.PortfolioPicker import PortfolioPickerController


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
        self.csv_browser = QPushButton("BROWSE")

        html_label = QLabel("HTML File Directory:")
        self.html_dir = QLineEdit()
        self.html_browser = QPushButton("BROWSE")

        set_label = QLabel("Set File directory:")
        self.set_dir = QLineEdit()
        self.set_browser = QPushButton("BROWSE")

        # Top layout
        top_grid = QGridLayout()
        top_grid.addWidget(csv_label, 0, 1)
        top_grid.addWidget(self.csv_dir, 1, 1)
        top_grid.addWidget(self.csv_browser, 1, 2)
        top_grid.addWidget(html_label,  0, 3)
        top_grid.addWidget(self.html_dir, 1, 3)
        top_grid.addWidget(self.html_browser, 1, 4)
        top_grid.addWidget(set_label, 0, 5)
        top_grid.addWidget(self.set_dir, 1, 5)
        top_grid.addWidget(self.set_browser, 1, 6)
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
        self.build_btn = QPushButton("BUILD PORTFOLIOS")

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
        api_grid.addWidget(self.build_btn, 1, 4)
        api_grid.setColumnStretch(1,5)
        api_grid.setColumnStretch(4,5)


        # ----------------------------- TEXT AREAS -----------------------------
        portfolios_label = QLabel("Portfolios Created:")
        portfolios_label.setMargin(0)
        portfolios_label.setContentsMargins(0, 10, 0, 10)
        portfolios_label.setStyleSheet("padding: 0px;")
        portfolios_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        portfolios_label.setFixedHeight(20)

        self.portfolios_created = QListWidget()
        self.portfolios_created.setMaximumHeight(200)
        self.portfolios_created.setContentsMargins(10, 0, 0, 10)
        self.portfolios_created.setStyleSheet("QListWidget { padding: 0px; }")
        self.portfolios_created.setFrameShape(QListWidget.NoFrame)

        setfiles_label = QLabel("Set Files Used:")
        setfiles_label.setMargin(0)
        setfiles_label.setContentsMargins(0, 10, 0, 10)
        setfiles_label.setStyleSheet("padding: 0px;")
        setfiles_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        setfiles_label.setFixedHeight(20)

        self.set_files_used = QListWidget()
        self.set_files_used.setMaximumHeight(200)
        self.set_files_used.setContentsMargins(0, 0,10, 10)
        self.set_files_used.setStyleSheet("QListWidget { padding: 0px; }")
        self.set_files_used.setFrameShape(QListWidget.NoFrame)

        # Layout
        text_grid = QGridLayout()
        text_grid.addWidget(portfolios_label, 0, 0)
        text_grid.addWidget(setfiles_label, 0, 1)
        text_grid.addWidget(self.portfolios_created, 1, 0)
        text_grid.addWidget(self.set_files_used, 1, 1)

        text_grid.setSpacing(0)
        text_grid.setContentsMargins(0, 0, 0, 0)
        text_grid.setVerticalSpacing(0)
        text_grid.setHorizontalSpacing(0)

        main_layout.addLayout(text_grid)

        # ----------------------------- MONTHLY + DRAW -----------------------------
        # monthly_label = QLabel("Monthly Portfolio Stats:")
        portfolio_label = QLabel("Monthly Portfolio Stats:")
        self.portfolio_stats = QTableWidget()
        self.portfolio_stats.setMaximumHeight(70)

        draw_label = QLabel("Global Drawdown Value:")

        self.draw_input = QLineEdit()
        self.draw_input.setText("1000")  # default value

        # Validator to only allow numbers (float)
        validator = QDoubleValidator()
        validator.setBottom(0)  # optional: minimum value 0
        self.draw_input.setValidator(validator)

        self.analyze_btn = QPushButton("ANALYZE")

        top_draw_grid = QGridLayout()
        top_draw_grid.addWidget(portfolio_label, 0, 0)
        top_draw_grid.addWidget(draw_label, 0, 1)
        top_draw_grid.addWidget(self.draw_input, 0, 2)
        top_draw_grid.addWidget(self.analyze_btn, 0, 3)
        top_draw_grid.addWidget(self.portfolio_stats, 1, 0, 1, 4)
        
        top_draw_grid.setColumnStretch(0, 4)
        top_draw_grid.setColumnStretch(2, 4)
        top_draw_grid.setColumnStretch(1, 1)

        # ----------------------------- DRAWDOWN OVERLAP -----------------------------

        drawdown_label = QLabel("Drawdown Overlap Analysis:")
        self.drawdown_analysis = QTableWidget()

        # ----------------------------- BOTTOM BUTTONS -----------------------------
        self.export_btn = QPushButton("EXPORT PROFILE")
        self.show_graph_btn = QPushButton("SHOW GRAPH")

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.export_btn)
        bottom_layout.addWidget(self.show_graph_btn)

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

        self.controller = PortfolioPickerController(self)


    # def resizeEvent(self, event):
    #     height = self.height()
    #     if height > 864:    
    #        self.monthly_stats.setMaximumHeight(120)
        
        # super().resizeEvent(event)


    
