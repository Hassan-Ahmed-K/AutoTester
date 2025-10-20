# from aiagentfinder.ui.base_tab import BaseTab
# from PyQt5.QtWidgets import (
#     QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
#     QHBoxLayout, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
#     QHeaderView, QCheckBox, QSpinBox, QComboBox, QListWidget, QSizePolicy, QSplitter
# )
# from PyQt5.QtCore import Qt, QSize
# from PyQt5.QtGui import QFont
# from aiagentfinder.controllers.SetGenerator import SetGeneratorController
# from aiagentfinder.utils.AnitmatedToggle import AnimatedToggle


# class SetGenerator(BaseTab):

#     def __init__(self, parent=None):
#         super().__init__("Set Generator", parent)
#         self.experts = {}

#     def init_ui(self):
#         # self.setStyleSheet("""
#         #     SetGenerator {
#         #         background-color: #1e1e1e;
#         #     }
#         #     QWidget {
#         #         background-color: #1e1e1e;
#         #         color: #dcdcdc;
#         #         font-family: Inter, Arial, sans-serif;
#         #         font-size: 12px;
#         #     }
#         #     QLabel {
#         #         color: #dcdcdc;
#         #         font-size: 12px;
#         #     }
#         #     QLabel#title {
#         #         font-size: 28px;
#         #         font-weight: bold;
#         #         color: #ffffff;
#         #     }
#         #     QLabel#subtitle {
#         #         font-size: 12px;
#         #         color: #a0a0a0;
#         #     }
#         #     QWidget#card {
#         #         background-color: #2b2b2b;
#         #         color: #000000;
#         #         border: 1px solid #3c3c3c;
#         #         border-radius: 6px;
#         #         padding: 6px;
#         #     }
#         #     QPushButton {
#         #         background-color: #3c3c3c;
#         #         border: 1px solid #555555;
#         #         border-radius: 4px;
#         #         padding: 4px 8px;
#         #         font-size: 12px;
#         #         color: #ffffff;
#         #         height: 10px;
#         #     }
#         #     QPushButton:hover {
#         #         background-color: #555555;
#         #     }
#         #     QLineEdit {
#         #         background-color: #2b2b2b;
#         #         border: 1px solid #555555;
#         #         border-radius: 4px;
#         #         padding: 4px 6px;
#         #         color: #ffffff;
#         #         font-size: 12px;
#         #         height: 10px;
#         #         width: 20px;
#         #     }
#         #     QTextEdit {
#         #         background-color: #2b2b2b;
#         #         border: 1px solid #555555;
#         #         border-radius: 4px;
#         #         color: #ffffff;
#         #         font-family: Consolas;
#         #         font-size: 12px;
#         #     }
#         #     QTableWidget {
#         #         background-color: #2b2b2b;
#         #         color: #dcdcdc;
#         #         gridline-color: #444;
#         #         font-size: 12px;
#         #     }
#         #     QHeaderView::section {
#         #         background-color: #333;
#         #         color: #dcdcdc;
#         #         padding: 2px;
#         #         font-size: 12px;
#         #     }
#         # """)
#         main_layout = self.main_layout 
#         main_layout.setAlignment(Qt.AlignTop)
#         # ---------- Header ----------

#         header = QVBoxLayout()
#         header.setContentsMargins(0, 0, 0, 0)
#         title = QLabel("SetGenerator")
#         title.setStyleSheet("font-size: 40px;")
#         title.setAlignment(Qt.AlignCenter)
#         title.setObjectName("title")
#         subtitle = QLabel("Results below are ranked by a proprietary POW Scoring system...")
#         subtitle.setAlignment(Qt.AlignCenter)
#         subtitle.setObjectName("subtitle")
#         subtitle.setWordWrap(True)
#         header.addWidget(title)
#         header.addWidget(subtitle)
#         main_layout.addLayout(header)


#         self.pairs_box = QListWidget()
#         self.show_all = AnimatedToggle(width=60, height=30, pulse=False)
#         self.api_key = QLineEdit()
#         self.select_files_btn = QPushButton("SELECT OPTIMISATION FILES")
#         self.opt_files = QListWidget()

#         self.opt_files.setFixedHeight(60)
#         self.pairs_box.setFixedHeight(120)

#         # # ---------- SIZE POLICIES ----------
#         self.pairs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
#         self.opt_files.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
#         self.api_key.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

#         # ---------- LEFT SECTION ----------
#         pairs_header = QHBoxLayout()
#         # pairs_header.setSpacing(1)
#         pairs_header.addWidget(QLabel("Pairs/Tests Detected:"))
#         pairs_header.addStretch()
#         pairs_header.addWidget(QLabel("Show All:"))
#         pairs_header.addWidget(self.show_all)

#         left_layout = QVBoxLayout()
#         left_layout.setContentsMargins(0, 5, 0, 14)
#         # left_layout.setSpacing(1)
#         left_layout.addLayout(pairs_header)
#         left_layout.addWidget(self.pairs_box)
#         left_layout.addStretch()

#         left_widget = QWidget()
#         left_widget.setLayout(left_layout)

#         # ---------- RIGHT SECTION ----------
#         api_layout = QVBoxLayout()
#         # api_layout.setContentsMargins(0, 0, 0, 0)
#         api_layout.addWidget(QLabel("API Key:"))


#         api_layout.setSpacing(3) 

#         opt_header = QHBoxLayout()
#         # opt_header.setContentsMargins(0, 0, 0, 0)
#         opt_header.addWidget(QLabel("Opt Files Used:"))
#         opt_header.addStretch()
#         opt_header.addWidget(self.select_files_btn)
#         # opt_header.setSpacing(0)

#         right_layout = QVBoxLayout()
#         right_layout.setContentsMargins(0, 5, 0, 14)
#         # right_layout.setSpacing(5)
#         right_layout.addLayout(api_layout)
#         right_layout.addWidget(self.api_key)
#         right_layout.addLayout(opt_header)
#         right_layout.addWidget(self.opt_files)
#         # right_layout.addStretch()

#         right_widget = QWidget()
#         right_widget.setLayout(right_layout)

#         # ---------- SPLITTER ----------
#         splitter = QSplitter(Qt.Horizontal)
#         splitter.addWidget(left_widget)
#         splitter.addWidget(right_widget)
#         splitter.setStretchFactor(0, 1)
#         splitter.setStretchFactor(1, 1)
#         splitter.setSizes([400, 400])

#         headerlayout = QVBoxLayout()
#         headerlayout.setContentsMargins(0, 0, 0, 0)
#         headerlayout.addWidget(splitter,stretch=2)
#         main_layout.addLayout(headerlayout)

#         # ---------- FILTERS ----------
#         filters = QHBoxLayout()
#         filters.setSpacing(5)

#         # Create a grid layout to align labels and inputs vertically
#         filter_grid = QGridLayout()
#         filter_grid.setHorizontalSpacing(10)
#         filter_grid.setVerticalSpacing(5)

#         # Define the filter fields
#         fields = [
#             ("Min % Diff", "min_diff", "Min % Diff"),
#             ("Max Sets", "max_sets", "Max Sets"),
#             ("Min Profit", "min_profit", "Min Profit"),
#             ("Min Profit as %", "min_profit_pct", "Min Profit as %"),
#         ]

#         # Add labels and inputs in aligned columns
#         for col, (label_text, attr_name, placeholder) in enumerate(fields):
#             label = QLabel(label_text)
#             line_edit = QLineEdit()
#             line_edit.setPlaceholderText(placeholder)
#             setattr(self, attr_name, line_edit)

#             filter_grid.addWidget(label, 0, col, alignment=Qt.AlignLeft)
#             filter_grid.addWidget(line_edit, 1, col)

#         # Add buttons in the last column (aligned under “Actions”)
#         # actions_label = QLabel("Actions")
#         self.sift_btn = QPushButton("SIFT SETS")
#         self.sift_btn.setStyleSheet("width: 100px")
#         self.auto_sift_btn = QPushButton("AUTO SIFT")
#         self.auto_sift_btn.setStyleSheet("width: 100px")



#         # Add to grid layout (same alignment as others)
#         # filter_grid.addWidget(actions_label, 0, len(fields), alignment=Qt.AlignLeft)

#         btn_box = QHBoxLayout()
#         btn_box.setSpacing(8)
#         btn_box.addWidget(self.sift_btn)
#         btn_box.addWidget(self.auto_sift_btn)
#         btn_widget = QWidget()
#         btn_widget.setLayout(btn_box)
#         filter_grid.addWidget(btn_widget, 1, len(fields), alignment=Qt.AlignLeft)

#         filters.addLayout(filter_grid)
#         main_layout.addLayout(filters)


#         # ---------- CONTROLS ABOVE TABLE ----------
#         controls = QHBoxLayout()
#         controls.setContentsMargins(0, 0, 0, 0)
#         controls.setSpacing(3)
#         self.toggle_result = AnimatedToggle()
#         self.toggle_selected = AnimatedToggle()
#         self.toggle_top_10 = AnimatedToggle()
#         self.toggle_top_100 = AnimatedToggle()
#         self.deselect_btn = QPushButton("DESELECT")

#         left_layout = QHBoxLayout()
#         left_layout.addWidget(QLabel("Finder Result"))
#         left_layout.addWidget(self.toggle_result)
#         left_layout.addWidget(QLabel("Rank By Profit"))
#         left_layout.addStretch()

#         right_layout = QHBoxLayout()
#         right_layout.addStretch()
#         right_layout.addWidget(self.deselect_btn)
#         right_layout.addWidget(self.toggle_selected)
#         right_layout.addWidget(QLabel("Hide unselected items"))
#         right_layout.addWidget(self.toggle_top_10)
#         right_layout.addWidget(QLabel("Top 10"))
#         right_layout.addWidget(self.toggle_top_100)
#         right_layout.addWidget(QLabel("Top 100"))

#         controls.addLayout(left_layout)
#         controls.addLayout(right_layout)
#         main_layout.addLayout(controls)

#         # ---------- TABLE ----------
#         self.table = QTableWidget(0, 10)
#         self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         self.table.setMinimumHeight(50)
#         # self.table.setMaximumHeight(300)  # Grows with window, max 200px

#         headers = [
#             "Pass No", "Bk Recovery", "Fwd Recovery", "Est Bk Weekly Profit",
#             "Est Fwd Weekly Profit", "Bk Trades", "Fwd Trades",
#             "Multiplier", "Total Profit", "POW Score"
#         ]
#         self.table.setHorizontalHeaderLabels(headers)
#         self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

#                 # Select entire row
#         # self.table.setSelectionBehavior(QTableWidget.SelectRows)

#         # # Allow multiple row selection (optional)
#         # self.table.setSelectionMode(QTableWidget.ExtendedSelection)

#         # # Optional: prevent cell-level editing
#         # self.table.setEditTriggers(QTableWidget.NoEditTriggers)


#         self.table.setSelectionBehavior(QTableWidget.SelectRows)
#         self.table.setSelectionMode(QTableWidget.ExtendedSelection)  # Disable default selection
#         self.table.setEditTriggers(QTableWidget.NoEditTriggers)


#         self.table.setStyleSheet("""
#             QTableWidget::item:selected {
#                 background-color: #3399FF;
#                 color: white;
#             }
#         """)
#         self.table.setMaximumHeight(120)
#         self.table.setContentsMargins(0, 0, 0, 0)
#         self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         main_layout.addWidget(self.table, stretch=3)
        
#         # ---------- BOTTOM SECTION ----------
#         table_controls = QHBoxLayout()

#         # Left inputs
#         table_left = QHBoxLayout()
#         table_left.setContentsMargins(0, 0, 0, 0)
#         for label_text, attr_name in [
#             ("Pass Number:", "pass_number"),
#             ("Global DD", "global_dd"),
#             ("Individual DD", "individual_dd"),
#         ]:
#             layout = QVBoxLayout()
#             layout.setContentsMargins(0, 0, 0, 0)
#             layout.addWidget(QLabel(label_text))
#             line_edit = QLineEdit()
#             setattr(self, attr_name, line_edit)
#             layout.addWidget(line_edit)
#             table_left.addLayout(layout)

#         # Middle toggles
#         table_middle = QHBoxLayout()
#         table_middle.setSpacing(5)
#         for label_text, attr_name in [
#             ("Generate Magic", "toggle_Generate_magic"),
#             ("Multiplier", "toggle_Multiplier"),
#         ]:
#             layout = QVBoxLayout()
#             layout.setSpacing(2)
#             layout.setContentsMargins(0, 0, 0, 0)
#             layout.addWidget(QLabel(label_text), alignment=Qt.AlignCenter)
#             toggle = AnimatedToggle(width=60, height=40, pulse=False)
#             setattr(self, attr_name, toggle)
#             layout.addWidget(toggle, alignment=Qt.AlignCenter)
#             table_middle.addLayout(layout)

#         # Right button
#         table_right = QHBoxLayout()
#         table_right.setContentsMargins(0, 0, 0, 0)
#         table_right.setAlignment(Qt.AlignRight)
#         self.generate_set_btn = QPushButton("GENERATE SET")
#         self.generate_set_btn.setFixedWidth(140)
#         self.generate_set_btn.setStyleSheet("font-weight: bold; padding: 6px;")
#         table_right.addWidget(self.generate_set_btn)

#         table_controls.addLayout(table_left, 6)
#         table_controls.addStretch(1)
#         table_controls.addLayout(table_middle, 3)
#         table_controls.addStretch(1)
#         table_controls.addLayout(table_right, 1)
#         main_layout.addLayout(table_controls)

#         # ---------- MESSAGE LOG ----------
#         bottom_message_layout = QVBoxLayout()
#         bottom_message_layout.setContentsMargins(0, 0, 0, 0)
#         bottom_message_layout.setSpacing(2)  # ⬅️ Minimal space between label and box
#         bottom_message_layout.setAlignment(Qt.AlignTop)

#         msg_label = QLabel("Message Log:")
#         msg_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
#         msg_label.setStyleSheet("font-weight: bold; color: #cccccc;")
#         bottom_message_layout.addWidget(msg_label, alignment=Qt.AlignTop)

#         self.bottom_message = QTextEdit()
#         self.bottom_message.setReadOnly(True)
#         self.bottom_message.setMinimumHeight(70)
#         self.bottom_message.setMaximumHeight(100)  # ⬅️ Grow dynamically but limited
#         self.bottom_message.setMinimumWidth(100)   # ⬅️ Minimum width added
#         self.bottom_message.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
#         bottom_message_layout.addWidget(self.bottom_message, alignment=Qt.AlignTop)

#         # Wrap into container (optional styling consistency)
#         bottom_container = QWidget()
#         bottom_container.setLayout(bottom_message_layout)
#         bottom_container.setContentsMargins(0, 0, 0, 0)
#         self.bottom_message.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

#         # Add to main layout
#         # main_layout.addSpacing(5)
#         main_layout.addWidget(bottom_container,stretch=1)

#         # ---------- CONTROLLER ----------
#         self.controller = SetGeneratorController(self)

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
        self.pairs_box.setMaximumHeight(120)
        # self.pairs_box.setFixedHeight(110)

        self.show_all = AnimatedToggle(width=60, height=30, pulse=False)
        pairs_header = QHBoxLayout()
        pairs_header.addWidget(QLabel("Pairs/Tests Detected:"))
        pairs_header.addStretch()
        pairs_header.addWidget(QLabel("Show All:"))
        pairs_header.addWidget(self.show_all)

        left_layout = QVBoxLayout()
        left_layout.addLayout(pairs_header)
        left_layout.addWidget(self.pairs_box)
        self.left_widget = QWidget()
        self.left_widget.setLayout(left_layout)
        self.left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # right area
        self.api_key = QLineEdit()
        self.select_files_btn = QPushButton("SELECT OPTIMISATION FILES")
        self.opt_files = QListWidget()
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

        # ----- CONTROLS -----
        self.controls_widget = QWidget()
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(3)
        self.toggle_result = AnimatedToggle()
        self.toggle_selected = AnimatedToggle()
        self.toggle_top_10 = AnimatedToggle()
        self.toggle_top_100 = AnimatedToggle()
        self.deselect_btn = QPushButton("DESELECT")

        left_ctrl = QHBoxLayout()
        left_ctrl.addWidget(QLabel("Finder Result"))
        left_ctrl.addWidget(self.toggle_result)
        left_ctrl.addWidget(QLabel("Rank By Profit"))
        left_ctrl.addStretch()

        right_ctrl = QHBoxLayout()
        right_ctrl.addStretch()
        right_ctrl.addWidget(self.deselect_btn)
        right_ctrl.addWidget(self.toggle_selected)
        right_ctrl.addWidget(QLabel("Hide unselected items"))
        right_ctrl.addWidget(self.toggle_top_10)
        right_ctrl.addWidget(QLabel("Top 10"))
        right_ctrl.addWidget(self.toggle_top_100)
        right_ctrl.addWidget(QLabel("Top 100"))

        controls_layout.addLayout(left_ctrl)
        controls_layout.addLayout(right_ctrl)
        self.controls_widget.setMinimumHeight(0)
        self.controls_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.controls_widget, stretch=0)

        # ----- TABLE -----
        self.table_widget = QWidget()
        table_layout = QVBoxLayout(self.table_widget)
        table_layout.setAlignment(Qt.AlignTop)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "Pass No", "Bk Recovery", "Fwd Recovery", "Est Bk Weekly Profit",
            "Est Fwd Weekly Profit", "Bk Trades", "Fwd Trades",
            "Multiplier", "Total Profit", "POW Score"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # allow shrink
        # self.table.setMinimumHeight(0)
        # self.table.setFixedHeight(120)
        self.table.setMaximumHeight(120)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        table_layout.addWidget(self.table)

        self.table_widget.setMinimumHeight(0)
        self.table_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        self.generate_set_btn = QPushButton("GENERATE SET")
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
        # self.bottom_message.setFixedHeight(100)
        self.bottom_message.setMaximumHeight(100)
        self.bottom_message.setReadOnly(True)
        self.bottom_message.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        msg_layout.addWidget(msg_label)
        msg_layout.addWidget(self.bottom_message)
        self.msg_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.msg_widget, stretch=1)

        # controller
        self.controller = SetGeneratorController(self)

        # layout=self.main_layout
        # layout.setContentsMargins(0, 0, 0, 0)
    
        #  # ---------- Header ----------
        # header = QVBoxLayout()
        # header.setContentsMargins(0, 0, 0, 0)
        # title = QLabel("SetGenerator")
        # title.setAlignment(Qt.AlignCenter)
        # title.setObjectName("title")
        # subtitle = QLabel("Results below are ranked by a proprietary POW Scoring system...")
        # subtitle.setAlignment(Qt.AlignCenter)
        # subtitle.setObjectName("subtitle")
        # subtitle.setWordWrap(True)
        # header.addWidget(title)
        # header.addWidget(subtitle)
        # layout.addLayout(header)

        # self.pairs_box = QListWidget()
        # self.show_all = AnimatedToggle(width=60, height=30, pulse=False)
        # self.api_key = QLineEdit()
        # self.select_files_btn = QPushButton("SELECT OPTIMISATION FILES")
        # self.opt_files = QListWidget()

        # self.pairs_box.setMaximumHeight(120)
        # self.opt_files.setMaximumHeight(65)

        # self.pairs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.opt_files.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # self.opt_files.setSelectionMode(QListWidget.ExtendedSelection)
        # self.pairs_box.setSelectionMode(QListWidget.ExtendedSelection)
        # self.opt_files.setFocusPolicy(Qt.StrongFocus) 
        # self.pairs_box.setFocusPolicy(Qt.StrongFocus)
        # self.opt_files.setStyleSheet("""
        #     QListWidget::item:selected {
        #         background-color: #3399FF;  /* highlight color */
        #         color: white;
        #     }
        # """)

        # self.pairs_box.setStyleSheet("""
        #     QListWidget::item:selected {
        #         background-color: #3399FF;
        #         color: white;
        #     }
        # """)

        # self.api_key.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # # ---------- LEFT SECTION ----------
        # pairs_header = QHBoxLayout()
        # pairs_header.addWidget(QLabel("Pairs/Tests Detected:"))
        # pairs_header.addStretch()
        # pairs_header.addWidget(QLabel("Show All:"))
        # pairs_header.addWidget(self.show_all)

        # left_layout = QVBoxLayout()
        # left_layout.setContentsMargins(0, 15, 0, 10)
        # left_layout.setSpacing(8)
        # left_layout.addLayout(pairs_header)
        # left_layout.addWidget(self.pairs_box)
        # left_layout.addStretch()

        # left_widget = QWidget()
        # left_widget.setLayout(left_layout)

        # # ---------- RIGHT SECTION ----------
        # api_layout = QVBoxLayout()
        # api_layout.setContentsMargins(0, 10, 0, 0)
        # api_layout.addWidget(QLabel("API Key:"))
        # api_layout.addWidget(self.api_key)

        # opt_header = QHBoxLayout()
        # opt_header.setContentsMargins(0, 0, 0, 0)
        # opt_header.addWidget(QLabel("Opt Files Used:"))
        # opt_header.addStretch()
        # opt_header.addWidget(self.select_files_btn)

        # right_layout = QVBoxLayout()
        # right_layout.setContentsMargins(0, 12, 0, 5)
        # right_layout.setSpacing(10)
        # right_layout.addLayout(api_layout)
        # right_layout.addLayout(opt_header)
        # right_layout.addWidget(self.opt_files)
        # right_layout.addStretch()

        # right_widget = QWidget()
        # right_widget.setLayout(right_layout)

        # # ---------- SPLITTER ----------
        # splitter = QSplitter(Qt.Horizontal)
        # splitter.addWidget(left_widget)
        # splitter.addWidget(right_widget)
        # splitter.setStretchFactor(0, 1)
        # splitter.setStretchFactor(1, 1)
        # splitter.setSizes([500, 500])

        # headerlayout = QVBoxLayout()
        # headerlayout.setContentsMargins(0, 0, 0, 0)
        # headerlayout.addWidget(splitter)
        # layout.addLayout(headerlayout)

        # # ---------- FILTERS ----------
        # filters = QHBoxLayout()

        # left_layout = QHBoxLayout()
        # for label_text, attr_name, placeholder in [
        #     ("Min % Diff", "min_diff", "Min % Diff"),
        #     ("Max Sets", "max_sets", "Max Sets"),
        #     ("Min Profit", "min_profit", "Min Profit"),
        #     ("Min Profit as %", "min_profit_pct", "Min Profit as %"),
        # ]:
        #     box = QVBoxLayout()
        #     box.addWidget(QLabel(label_text))
        #     line_edit = QLineEdit()
        #     line_edit.setPlaceholderText(placeholder)
        #     setattr(self, attr_name, line_edit)
        #     box.addWidget(line_edit)
        #     left_layout.addLayout(box)

        # filters.addLayout(left_layout)

        # right_layout = QHBoxLayout()
        # right_layout.setContentsMargins(0, 20, 0, 0)
        # self.sift_btn = QPushButton("SIFT SETS")
        # self.auto_sift_btn = QPushButton("AUTO SIFT")
        # right_layout.addWidget(self.sift_btn)
        # right_layout.addWidget(self.auto_sift_btn)
        # filters.addLayout(right_layout)
        # layout.addLayout(filters)

        # # ---------- CONTROLS ABOVE TABLE ----------
        # controls = QHBoxLayout()
        # controls.setSpacing(8)
        # self.toggle_result = AnimatedToggle()
        # self.toggle_selected = AnimatedToggle()
        # self.toggle_top_10 = AnimatedToggle()
        # self.toggle_top_100 = AnimatedToggle()
        # self.deselect_btn = QPushButton("DESELECT")

        # left_layout = QHBoxLayout()
        # left_layout.addWidget(QLabel("Finder Result"))
        # left_layout.addWidget(self.toggle_result)
        # left_layout.addWidget(QLabel("Rank By Profit"))
        # left_layout.addStretch()

        # right_layout = QHBoxLayout()
        # right_layout.addStretch()
        # right_layout.addWidget(self.deselect_btn)
        # right_layout.addWidget(self.toggle_selected)
        # right_layout.addWidget(QLabel("Hide unselected items"))
        # right_layout.addWidget(self.toggle_top_10)
        # right_layout.addWidget(QLabel("Top 10"))
        # right_layout.addWidget(self.toggle_top_100)
        # right_layout.addWidget(QLabel("Top 100"))

        # controls.addLayout(left_layout)
        # controls.addLayout(right_layout)
        # layout.addLayout(controls)

        # # ---------- TABLE ----------
        # self.table = QTableWidget(0, 10)
        # self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.table.setMinimumHeight(50)
        # # self.table.setMaximumHeight(300)  # Grows with window, max 200px

        # headers = [
        #     "Pass No", "Bk Recovery", "Fwd Recovery", "Est Bk Weekly Profit",
        #     "Est Fwd Weekly Profit", "Bk Trades", "Fwd Trades",
        #     "Multiplier", "Total Profit", "POW Score"
        # ]
        # self.table.setHorizontalHeaderLabels(headers)
        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # layout.addWidget(self.table, stretch=1)

        #         # Select entire row
        # # self.table.setSelectionBehavior(QTableWidget.SelectRows)

        # # # Allow multiple row selection (optional)
        # # self.table.setSelectionMode(QTableWidget.ExtendedSelection)

        # # # Optional: prevent cell-level editing
        # # self.table.setEditTriggers(QTableWidget.NoEditTriggers)


        # self.table.setSelectionBehavior(QTableWidget.SelectRows)
        # self.table.setSelectionMode(QTableWidget.ExtendedSelection)  # Disable default selection
        # self.table.setEditTriggers(QTableWidget.NoEditTriggers)


        # self.table.setStyleSheet("""
        #     QTableWidget::item:selected {
        #         background-color: #3399FF;
        #         color: white;
        #     }
        # """)

        # # ---------- BOTTOM SECTION ----------
        # table_controls = QHBoxLayout()
        # table_controls.setContentsMargins(0, 0, 0, 0)


        

        # # Left inputs
        # table_left = QHBoxLayout()
        # for label_text, attr_name in [
        #     ("Pass Number:", "pass_number"),
        #     ("Global DD", "global_dd"),
        #     ("Individual DD", "individual_dd"),
        # ]:
        #     layout = QVBoxLayout()
        #     layout.addWidget(QLabel(label_text))
        #     line_edit = QLineEdit()
        #     setattr(self, attr_name, line_edit)
        #     layout.addWidget(line_edit)
        #     table_left.addLayout(layout)

        # # Middle toggles
        # table_middle = QHBoxLayout()
        # for label_text, attr_name in [
        #     ("Generate Magic", "toggle_Generate_magic"),
        #     ("Multiplier", "toggle_Multiplier"),
        # ]:
        #     layout = QVBoxLayout()
        #     layout.addWidget(QLabel(label_text), alignment=Qt.AlignCenter)
        #     toggle = AnimatedToggle(width=60, height=40, pulse=False)
        #     setattr(self, attr_name, toggle)
        #     layout.addWidget(toggle, alignment=Qt.AlignCenter)
        #     table_middle.addLayout(layout)

        # # Right button
        # table_right = QHBoxLayout()
        # table_right.setContentsMargins(0, 10, 0, 0)
        # table_right.setAlignment(Qt.AlignRight)
        # self.generate_set_btn = QPushButton("GENERATE SET")
        # self.generate_set_btn.setFixedWidth(140)
        # self.generate_set_btn.setStyleSheet("font-weight: bold; padding: 6px;")
        # table_right.addWidget(self.generate_set_btn)

        # table_controls.addLayout(table_left, 6)
        # table_controls.addStretch(1)
        # table_controls.addLayout(table_middle, 3)
        # table_controls.addStretch(1)
        # table_controls.addLayout(table_right, 1)
        # layout.addLayout(table_controls)

        # # ---------- MESSAGE LOG ----------
        # bottom_message_layout = QVBoxLayout()
        # bottom_message_layout.setContentsMargins(0, 0, 0, 0)
        # bottom_message_layout.setSpacing(2)  # ⬅️ Minimal space between label and box
        # bottom_message_layout.setAlignment(Qt.AlignTop)

        # msg_label = QLabel("Message Log:")
        # msg_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # msg_label.setStyleSheet("font-weight: bold; color: #cccccc;")
        # bottom_message_layout.addWidget(msg_label, alignment=Qt.AlignTop)

        # self.bottom_message = QTextEdit()
        # self.bottom_message.setReadOnly(True)
        # self.bottom_message.setMinimumHeight(70)
        # self.bottom_message.setMaximumHeight(200)  # ⬅️ Grow dynamically but limited
        # self.bottom_message.setMinimumWidth(100)   # ⬅️ Minimum width added
        # self.bottom_message.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # bottom_message_layout.addWidget(self.bottom_message, alignment=Qt.AlignTop)

        # # Wrap into container (optional styling consistency)
        # bottom_container = QWidget()
        # bottom_container.setLayout(bottom_message_layout)
        # bottom_container.setContentsMargins(0, 0, 0, 0)

        # # Add to main layout
        # layout.addSpacing(5)
        # layout.addWidget(bottom_container, stretch=1)

        

        # Controller
        self.controller = SetGeneratorController(self)

