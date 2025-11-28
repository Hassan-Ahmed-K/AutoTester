from aiagentfinder.ui.base_tab import BaseTab
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QHBoxLayout, QVBoxLayout, QGridLayout, QTableWidget, QHeaderView,
    QListWidget, QSizePolicy, QSplitter
)
from PyQt5.QtCore import Qt
from aiagentfinder.controllers.SetGenerator import SetGeneratorController
from aiagentfinder.utils.AnitmatedToggle import AnimatedToggle


class SetGenerator(BaseTab):
    def __init__(self, parent=None):
        super().__init__("Set Generator", parent)
        self.experts = {}

    def init_ui(self):
        # make main layout accessible via self.main_layout from BaseTab
        main_layout = self.main_layout
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(6)

        # ----- HEADER (widget container) -----
        self.header_widget = QWidget()
        header_layout = QVBoxLayout(self.header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.title = QLabel("SetGenerator")
        self.title.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.title.setAlignment(Qt.AlignCenter)
        self.subtitle = QLabel("Results below are ranked by a proprietary POW Scoring system...")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setWordWrap(True)
        header_layout.addWidget(self.title)
        header_layout.addWidget(self.subtitle)
        # ensure header can shrink
        self.header_widget.setMinimumHeight(0)
        self.header_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        main_layout.addWidget(self.header_widget, stretch=0)

        # ----- UPPER SPLITTER (pairs + opt files) -----
        self.upper_widget = QWidget()
        upper_layout = QVBoxLayout(self.upper_widget)
        upper_layout.setContentsMargins(0, 0, 0, 0)

        # left list
        self.pairs_box = QListWidget()
        self.pairs_box.setSelectionMode(QListWidget.SingleSelection)
        self.pairs_box.setFocusPolicy(Qt.StrongFocus)
        self.pairs_box.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #adacac;  /* highlight color */
                color: white;
            }
        """)
        self.pairs_box.setMaximumHeight(122)
        # self.pairs_box.setFixedHeight(110)

        self.show_all = AnimatedToggle(width=60, height=30, pulse=False)
        pairs_header = QHBoxLayout()
        pairs_header.addWidget(QLabel("Pairs/Tests Detected:"))
        pairs_header.addStretch()
        pairs_header.addWidget(QLabel("Show All:"))
        pairs_header.addWidget(self.show_all)

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addLayout(pairs_header)
        left_layout.addWidget(self.pairs_box)
        self.left_widget = QWidget()
        self.left_widget.setLayout(left_layout)
        self.left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # right area
        self.api_key = QLineEdit()
        self.select_files_btn = QPushButton("SELECT OPTIMISATION FILES")
        self.select_files_btn.setStyleSheet("height:10px;")
        self.opt_files = QListWidget()
        self.opt_files.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #adacac;  
                color: white;
            }
        """)
        self.opt_files.setSelectionMode(QListWidget.ExtendedSelection)
        self.opt_files.setFocusPolicy(Qt.StrongFocus)
        self.opt_files.setMaximumHeight(60)
        # self.opt_files.setFixedHeight(50)
        self.opt_files.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        api_layout = QVBoxLayout()
        api_layout.addWidget(QLabel("API Key:"))
        api_layout.addWidget(self.api_key)
        opt_header = QHBoxLayout()
        opt_header.addWidget(QLabel("Opt Files Used:"))
        opt_header.addStretch()
        opt_header.addWidget(self.select_files_btn)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addLayout(api_layout)
        right_layout.addLayout(opt_header)
        right_layout.addWidget(self.opt_files)
        self.right_widget = QWidget()
        self.right_widget.setLayout(right_layout)
        self.right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # splitter (collapsible children allowed)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setChildrenCollapsible(True)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        upper_layout.addWidget(self.splitter)
        main_layout.addWidget(self.upper_widget, stretch=2)

        # ----- FILTERS (grid) -----
        self.filter_widget = QWidget()
        filter_layout = QGridLayout(self.filter_widget)
        filter_layout.setHorizontalSpacing(8)
        filter_layout.setVerticalSpacing(8)

        fields = [
            ("Min % Diff", "min_diff", "Min % Diff"),
            ("Max Sets", "max_sets", "Max Sets"),
            ("Min Profit", "min_profit", "Min Profit"),
            ("Min Profit as %", "min_profit_pct", "Min Profit as %"),
        ]
        for col, (label_text, attr_name, placeholder) in enumerate(fields):
            label = QLabel(label_text)
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(placeholder)
            setattr(self, attr_name, line_edit)
            line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            setattr(self, attr_name, line_edit)
            filter_layout.addWidget(label, 0, col)
            filter_layout.addWidget(line_edit, 1, col)

        self.sift_btn = QPushButton("SIFT SETS")
        
        self.auto_sift_btn = QPushButton("AUTO SIFT")
        btn_box = QHBoxLayout()
        btn_box.addWidget(self.sift_btn)
        btn_box.addWidget(self.auto_sift_btn)
        filter_layout.addLayout(btn_box, 1, len(fields))
        self.filter_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.filter_widget, stretch=0)

        # # ----- CONTROLS -----
        # self.controls_widget = QWidget()
        # controls_layout = QHBoxLayout(self.controls_widget)
        # controls_layout.setContentsMargins(0, 0, 0, 0)
        # controls_layout.setSpacing(3)
        # self.toggle_result = AnimatedToggle(width=40, height=25, pulse=False)
        # self.toggle_selected = AnimatedToggle(width=40, height=25, pulse=False)
        # self.toggle_top_10 = AnimatedToggle(width=40, height=25, pulse=False)
        # self.toggle_top_100 = AnimatedToggle(width=40, height=25, pulse=False)
        # self.deselect_btn = QPushButton("DESELECT")

        # left_ctrl = QHBoxLayout()
        # left_ctrl.addWidget(QLabel("Finder Result"))
        # left_ctrl.addWidget(self.toggle_result,alignment=Qt.AlignCenter)
        # left_ctrl.addWidget(QLabel("Rank By Profit"))
        # left_ctrl.addStretch()

        # right_ctrl = QHBoxLayout()
        # right_ctrl.addStretch()
        # right_ctrl.addWidget(self.deselect_btn)
        # right_ctrl.addWidget(self.toggle_selected)
        # right_ctrl.addWidget(QLabel("Hide unselected items"))
        # right_ctrl.addWidget(self.toggle_top_10,alignment=Qt.AlignCenter)
        # right_ctrl.addWidget(QLabel("Top 10"))
        # right_ctrl.addWidget(self.toggle_top_100,alignment=Qt.AlignCenter)
        # right_ctrl.addWidget(QLabel("Top 100"))

        # controls_layout.addLayout(left_ctrl)
        # controls_layout.addLayout(right_ctrl)
        # self.controls_widget.setMinimumHeight(0)
        # self.controls_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # main_layout.addWidget(self.controls_widget, stretch=0)

                # ----- CONTROLS -----
        self.controls_widget = QWidget()
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        # Toggles
        self.toggle_result = AnimatedToggle(width=40, height=25, pulse=False)
        self.toggle_selected = AnimatedToggle(width=40, height=25, pulse=False)
        self.toggle_top_10 = AnimatedToggle(width=40, height=25, pulse=False)
        self.toggle_top_100 = AnimatedToggle(width=40, height=25, pulse=False)
        self.deselect_btn = QPushButton("DESELECT")

        # ----- LEFT CONTROL -----
        left_ctrl = QHBoxLayout()
        left_ctrl.addWidget(QLabel("Finder Result"), alignment=Qt.AlignVCenter)
        left_ctrl.addWidget(self.toggle_result, alignment=Qt.AlignVCenter)
        left_ctrl.addWidget(QLabel("Rank By Profit"), alignment=Qt.AlignVCenter)
        left_ctrl.addStretch()

        # ----- RIGHT CONTROL -----
        right_ctrl = QHBoxLayout()
        right_ctrl.addStretch()
        right_ctrl.addWidget(self.deselect_btn, alignment=Qt.AlignVCenter)
        right_ctrl.addWidget(self.toggle_selected, alignment=Qt.AlignVCenter)
        right_ctrl.addWidget(QLabel("Hide unselected items"), alignment=Qt.AlignVCenter)
        right_ctrl.addWidget(self.toggle_top_10, alignment=Qt.AlignVCenter)
        right_ctrl.addWidget(QLabel("Top 10"), alignment=Qt.AlignVCenter)
        right_ctrl.addWidget(self.toggle_top_100, alignment=Qt.AlignVCenter)
        right_ctrl.addWidget(QLabel("Top 100"), alignment=Qt.AlignVCenter)

        # Combine left and right
        controls_layout.addLayout(left_ctrl)
        controls_layout.addLayout(right_ctrl)

        # Finalize
        self.controls_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.controls_widget, stretch=0)


        # ----- TABLE -----
        self.table_widget = QWidget()
        table_layout = QVBoxLayout(self.table_widget)
        table_layout.setAlignment(Qt.AlignTop)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 10)
        
        headers = [
            "Pass No", "Bk Recovery", "Fwd Recovery", "Est Bk Weekly Profit",
            "Est Fwd Weekly Profit", "Bk Trades", "Fwd Trades",
            "Multiplier", "Total Profit", "Custom Score"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #dcdcdc;
                gridline-color: #444;
                font-size: 12px;

            }
            QTableWidget::item:selected {
                background-color: #adacac;
                color: white;
            }
        """)

        # allow shrink
        # self.table.setMinimumHeight(0)
        # self.table.setFixedHeight(120)
        # self.table.setMaximumHeight(120)
        # self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        table_layout.addWidget(self.table)

        # self.table_widget.setMinimumHeight(0)
        # self.table_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.table_widget, stretch=4)

        # ----- BOTTOM CONTROLS -----
        self.bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(self.bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

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

        table_middle = QHBoxLayout()
        # table_middle.setContentsMargins(5,0,0,0)
        table_middle.setSpacing(5)
        for label_text, attr_name in [
            ("Generate Magic", "toggle_Generate_magic"),
            ("Multiplier", "toggle_Multiplier"),
        ]:
            layout = QVBoxLayout()
            layout.addWidget(QLabel(label_text), alignment=Qt.AlignCenter)
            toggle = AnimatedToggle(width=60, height=30, pulse=False)
            setattr(self, attr_name, toggle)
            layout.addWidget(toggle, alignment=Qt.AlignCenter)
            table_middle.addLayout(layout)

        table_right = QHBoxLayout()
        table_right.setContentsMargins(0,15,0,0)
        self.generate_set_btn = QPushButton("GENERATE SET")
        self.generate_set_btn.setStyleSheet("background-color:  #4CAF50; color: white;")
        self.generate_set_btn.setFixedWidth(140)
        table_right.addWidget(self.generate_set_btn)
       
        bottom_layout.addLayout(table_left, 6)
        bottom_layout.addStretch(1)
        bottom_layout.addLayout(table_middle, 3)
        bottom_layout.addStretch(1)
        bottom_layout.addLayout(table_right, 1)
        self.bottom_widget.setMinimumHeight(0)
        self.bottom_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.bottom_widget, stretch=0)
 


        # ----- MESSAGE LOG -----
        self.msg_widget = QWidget()
        msg_layout = QVBoxLayout(self.msg_widget)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_label = QLabel("Message Log:")
        msg_label.setStyleSheet("font-weight: bold;")
        self.bottom_message = QTextEdit()
        self.bottom_message.setStyleSheet("font-weight: bold; color: #cccccc;")
        # self.bottom_message.setFixedHeight(100)
        # self.bottom_message.setMaximumHeight(100)
        self.bottom_message.setReadOnly(True)
        self.bottom_message.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        msg_layout.addWidget(msg_label)
        msg_layout.addSpacing(5)
        msg_layout.addWidget(self.bottom_message)
        self.msg_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.msg_widget, stretch=1)

        self.controller = SetGeneratorController(self)


    def resizeEvent(self, event):
        height = self.height()
        if height > 864:    
            self.pairs_box.setMaximumHeight(131)
            self.opt_files.setMaximumHeight(67)
            self.bottom_message.setMinimumHeight(200)
            self.bottom_message.setMaximumHeight(300)
            self.table.setMinimumHeight(200)
            self.table.setMaximumHeight(350)
            self.left_widget.setContentsMargins(0, 5, 0, 0)


        elif height < 768:     
            self.bottom_message.setMaximumHeight(100)
            self.table.setMaximumHeight(140)
        
        super().resizeEvent(event)

       

