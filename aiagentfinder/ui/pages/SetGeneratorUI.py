from aiagentfinder.ui.base_tab import BaseTab
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QHBoxLayout, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QSpinBox, QComboBox, QListWidget, QSizePolicy, QSplitter
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from aiagentfinder.controllers.SetGenerator import SetGeneratorController
from aiagentfinder.utils.AnitmatedToggle import AnimatedToggle


class SetGenerator(BaseTab):

    def __init__(self, parent=None):
        super().__init__("Set Generator", parent)
        self.experts = {}

    def init_ui(self):
        self.setStyleSheet("""
            SetGenerator {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #dcdcdc;
                font-family: Inter, Arial, sans-serif;
                font-size: 12px;
            }
            QLabel {
                color: #dcdcdc;
                font-size: 12px;
            }
            QLabel#title {
                font-size: 28px;
                font-weight: bold;
                color: #ffffff;
            }
            QLabel#subtitle {
                font-size: 12px;
                color: #a0a0a0;
            }
            QWidget#card {
                background-color: #2b2b2b;
                color: #000000;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                color: #ffffff;
                height: 10px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QLineEdit {
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px 6px;
                color: #ffffff;
                font-size: 12px;
                height: 10px;
                width: 20px;
            }
            QTextEdit {
                background-color: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
                font-family: Consolas;
                font-size: 12px;
            }
            QTableWidget {
                background-color: #2b2b2b;
                color: #dcdcdc;
                gridline-color: #444;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #333;
                color: #dcdcdc;
                padding: 2px;
                font-size: 12px;
            }
        """)

        # ---------- Header ----------
        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        title = QLabel("SetGenerator")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")
        subtitle = QLabel("Results below are ranked by a proprietary POW Scoring system...")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        header.addWidget(title)
        header.addWidget(subtitle)
        self.layout.addLayout(header)

        self.pairs_box = QListWidget()
        self.show_all = AnimatedToggle(width=60, height=30, pulse=False)
        self.api_key = QLineEdit()
        self.select_files_btn = QPushButton("SELECT OPTIMISATION FILES")
        self.opt_files = QListWidget()

        self.pairs_box.setMaximumHeight(120)
        self.opt_files.setMaximumHeight(65)

        self.pairs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.opt_files.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.opt_files.setSelectionMode(QListWidget.ExtendedSelection)
        self.pairs_box.setSelectionMode(QListWidget.ExtendedSelection)
        self.opt_files.setFocusPolicy(Qt.StrongFocus) 
        self.pairs_box.setFocusPolicy(Qt.StrongFocus)
        self.opt_files.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #3399FF;  /* highlight color */
                color: white;
            }
        """)

        self.pairs_box.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #3399FF;
                color: white;
            }
        """)

        self.api_key.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # ---------- LEFT SECTION ----------
        pairs_header = QHBoxLayout()
        pairs_header.addWidget(QLabel("Pairs/Tests Detected:"))
        pairs_header.addStretch()
        pairs_header.addWidget(QLabel("Show All:"))
        pairs_header.addWidget(self.show_all)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 15, 0, 10)
        left_layout.setSpacing(8)
        left_layout.addLayout(pairs_header)
        left_layout.addWidget(self.pairs_box)
        left_layout.addStretch()

        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        # ---------- RIGHT SECTION ----------
        api_layout = QVBoxLayout()
        api_layout.setContentsMargins(0, 10, 0, 0)
        api_layout.addWidget(QLabel("API Key:"))
        api_layout.addWidget(self.api_key)

        opt_header = QHBoxLayout()
        opt_header.setContentsMargins(0, 0, 0, 0)
        opt_header.addWidget(QLabel("Opt Files Used:"))
        opt_header.addStretch()
        opt_header.addWidget(self.select_files_btn)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 12, 0, 5)
        right_layout.setSpacing(10)
        right_layout.addLayout(api_layout)
        right_layout.addLayout(opt_header)
        right_layout.addWidget(self.opt_files)
        right_layout.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # ---------- SPLITTER ----------
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 500])

        headerlayout = QVBoxLayout()
        headerlayout.setContentsMargins(0, 0, 0, 0)
        headerlayout.addWidget(splitter)
        self.layout.addLayout(headerlayout)

        # ---------- FILTERS ----------
        filters = QHBoxLayout()

        left_layout = QHBoxLayout()
        for label_text, attr_name, placeholder in [
            ("Min % Diff", "min_diff", "Min % Diff"),
            ("Max Sets", "max_sets", "Max Sets"),
            ("Min Profit", "min_profit", "Min Profit"),
            ("Min Profit as %", "min_profit_pct", "Min Profit as %"),
        ]:
            box = QVBoxLayout()
            box.addWidget(QLabel(label_text))
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(placeholder)
            setattr(self, attr_name, line_edit)
            box.addWidget(line_edit)
            left_layout.addLayout(box)

        filters.addLayout(left_layout)

        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 20, 0, 0)
        self.sift_btn = QPushButton("SIFT SETS")
        self.auto_sift_btn = QPushButton("AUTO SIFT")
        right_layout.addWidget(self.sift_btn)
        right_layout.addWidget(self.auto_sift_btn)
        filters.addLayout(right_layout)
        self.layout.addLayout(filters)

        # ---------- CONTROLS ABOVE TABLE ----------
        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.toggle_result = AnimatedToggle()
        self.toggle_selected = AnimatedToggle()
        self.toggle_top_10 = AnimatedToggle()
        self.toggle_top_100 = AnimatedToggle()
        self.deselect_btn = QPushButton("DESELECT")

        left_layout = QHBoxLayout()
        left_layout.addWidget(QLabel("Finder Result"))
        left_layout.addWidget(self.toggle_result)
        left_layout.addWidget(QLabel("Rank By Profit"))
        left_layout.addStretch()

        right_layout = QHBoxLayout()
        right_layout.addStretch()
        right_layout.addWidget(self.deselect_btn)
        right_layout.addWidget(self.toggle_selected)
        right_layout.addWidget(QLabel("Hide unselected items"))
        right_layout.addWidget(self.toggle_top_10)
        right_layout.addWidget(QLabel("Top 10"))
        right_layout.addWidget(self.toggle_top_100)
        right_layout.addWidget(QLabel("Top 100"))

        controls.addLayout(left_layout)
        controls.addLayout(right_layout)
        self.layout.addLayout(controls)

        # ---------- TABLE ----------
        self.table = QTableWidget(0, 10)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setMinimumHeight(50)
        # self.table.setMaximumHeight(300)  # Grows with window, max 200px

        headers = [
            "Pass No", "Bk Recovery", "Fwd Recovery", "Est Bk Weekly Profit",
            "Est Fwd Weekly Profit", "Bk Trades", "Fwd Trades",
            "Multiplier", "Total Profit", "POW Score"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table, stretch=1)

                # Select entire row
        # self.table.setSelectionBehavior(QTableWidget.SelectRows)

        # # Allow multiple row selection (optional)
        # self.table.setSelectionMode(QTableWidget.ExtendedSelection)

        # # Optional: prevent cell-level editing
        # self.table.setEditTriggers(QTableWidget.NoEditTriggers)


        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)  # Disable default selection
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)


        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #3399FF;
                color: white;
            }
        """)

        # ---------- BOTTOM SECTION ----------
        table_controls = QHBoxLayout()
        table_controls.setContentsMargins(0, 0, 0, 0)


        

        # Left inputs
        table_left = QHBoxLayout()
        for label_text, attr_name in [
            ("Pass Number:", "pass_number"),
            ("Global DD", "global_dd"),
            ("Individual DD", "individual_dd"),
        ]:
            layout = QVBoxLayout()
            layout.addWidget(QLabel(label_text))
            line_edit = QLineEdit()
            setattr(self, attr_name, line_edit)
            layout.addWidget(line_edit)
            table_left.addLayout(layout)

        # Middle toggles
        table_middle = QHBoxLayout()
        for label_text, attr_name in [
            ("Generate Magic", "toggle_Generate_magic"),
            ("Multiplier", "toggle_Multiplier"),
        ]:
            layout = QVBoxLayout()
            layout.addWidget(QLabel(label_text), alignment=Qt.AlignCenter)
            toggle = AnimatedToggle(width=60, height=40, pulse=False)
            setattr(self, attr_name, toggle)
            layout.addWidget(toggle, alignment=Qt.AlignCenter)
            table_middle.addLayout(layout)

        # Right button
        table_right = QHBoxLayout()
        table_right.setContentsMargins(0, 10, 0, 0)
        table_right.setAlignment(Qt.AlignRight)
        self.generate_set_btn = QPushButton("GENERATE SET")
        self.generate_set_btn.setFixedWidth(140)
        self.generate_set_btn.setStyleSheet("font-weight: bold; padding: 6px;")
        table_right.addWidget(self.generate_set_btn)

        table_controls.addLayout(table_left, 6)
        table_controls.addStretch(1)
        table_controls.addLayout(table_middle, 3)
        table_controls.addStretch(1)
        table_controls.addLayout(table_right, 1)
        self.layout.addLayout(table_controls)

        # ---------- MESSAGE LOG ----------
        bottom_message_layout = QVBoxLayout()
        bottom_message_layout.setContentsMargins(0, 0, 0, 0)
        bottom_message_layout.setSpacing(2)  # ⬅️ Minimal space between label and box
        bottom_message_layout.setAlignment(Qt.AlignTop)

        msg_label = QLabel("Message Log:")
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        msg_label.setStyleSheet("font-weight: bold; color: #cccccc;")
        bottom_message_layout.addWidget(msg_label, alignment=Qt.AlignTop)

        self.bottom_message = QTextEdit()
        self.bottom_message.setReadOnly(True)
        self.bottom_message.setMinimumHeight(70)
        self.bottom_message.setMaximumHeight(200)  # ⬅️ Grow dynamically but limited
        self.bottom_message.setMinimumWidth(100)   # ⬅️ Minimum width added
        self.bottom_message.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bottom_message_layout.addWidget(self.bottom_message, alignment=Qt.AlignTop)

        # Wrap into container (optional styling consistency)
        bottom_container = QWidget()
        bottom_container.setLayout(bottom_message_layout)
        bottom_container.setContentsMargins(0, 0, 0, 0)

        # Add to main layout
        self.layout.addSpacing(5)
        self.layout.addWidget(bottom_container, stretch=1)

        # Controller
        self.controller = SetGeneratorController(self)
