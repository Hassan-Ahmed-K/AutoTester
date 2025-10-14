# from aiagentfinder.ui.base_tab import BaseTab
# from PyQt5.QtWidgets import (
#     QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
#     QHBoxLayout, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
#     QHeaderView, QCheckBox, QSpinBox, QComboBox,QListWidget
# )
# from PyQt5.QtCore import Qt, QSize
# from PyQt5.QtGui import QFont
# from aiagentfinder.controllers.setGenerator import SetGeneratorController
# from aiagentfinder.utils.AnimatedToggle import AnimatedToggle
# class SetGenerator(BaseTab):
    
#     def __init__(self, parent=None):
#         super().__init__("Home Page", parent)
#         self.experts = {}
#     def init_ui(self):
#         self.setStyleSheet("""
#                SetGenerator {
#             background-color: #1e1e1e;
#         }
#         QWidget {
#             background-color: #1e1e1e;
#             color: #dcdcdc;
#             font-family: Inter, Arial, sans-serif;
#             font-size: 13px;
#         }
#         QLabel {
#             color: #dcdcdc;
#             font-size: 12px;
#         }
#         QLabel#title {
#             font-size: 28px;
#             font-weight: bold;
#             color: #ffffff;
#         }
#         QLabel#subtitle {
#             font-size: 12px;
#             color: #a0a0a0;
#         }
#         QWidget#card {
#             background-color: #2b2b2b;
#             color: #000000;
#             border: 1px solid #3c3c3c;
#             border-radius: 6px;
#             padding: 6px;
#         }
#         QPushButton {
#             background-color: #3c3c3c;
#             border: 1px solid #555555;
#             border-radius: 4px;
#             padding: 4px 8px;
#             font-size: 12px;
#             color: #ffffff;
#         }
#         QPushButton:hover {
#             background-color: #555555;
#         }
#         QLineEdit {
#             background-color: #2b2b2b;
#             border: 1px solid #555555;
#             border-radius: 4px;
#             padding: 4px 6px;
#             color: #ffffff;
#             font-size: 12px;
#             height: 20px;
#         }
#         QTextEdit {
#             background-color: #2b2b2b;
#             border: 1px solid #555555;
#             border-radius: 4px;
#             color: #ffffff;
#             font-family: Consolas;
#             font-size: 12px;
#         }
#         QTableWidget {
#             background-color: #2b2b2b;
#             color: #dcdcdc;
#             gridline-color: #444;
#             font-size: 12px;
#         }
#         QHeaderView::section {
#             background-color: #333;
#             color: #dcdcdc;
#             padding: 2px;
#             font-size: 12px;
#         }
#     """)

#         root = QVBoxLayout(self)
#         root.setContentsMargins(14, 14, 14, 14)
#         root.setSpacing(12)

#         # ---------- Header ----------
#         header = QVBoxLayout()
#         title = QLabel("SetGenerator")
#         title.setAlignment(Qt.AlignCenter)
#         title.setObjectName("title")
#         subtitle = QLabel("Results below are ranked by a proprietary POW Scoring system...")
#         subtitle.setAlignment(Qt.AlignCenter)
#         subtitle.setObjectName("subtitle")
#         subtitle.setWordWrap(True)
#         header.addWidget(title)
#         header.addWidget(subtitle)
#         root.addLayout(header)



#         # --- Widgets ---
#         self.pairs_box = QListWidget()
#         self.show_all = AnimatedToggle()
#         self.api_key = QLineEdit("")
#         self.select_files_btn = QPushButton("SELECT OPTIMISATION FILES")
#         self.opt_files = QListWidget()
#         self.pairs_box.setMaximumHeight(100)
#         self.opt_files.setMaximumHeight(70)
#         # ---------- RIGHT SIDE (Pairs Section) ----------
#         left_layout = QVBoxLayout()
#         pairs_header = QHBoxLayout()
#         pairs_header.addWidget(QLabel("Pairs/Tests Detected:"))
#         pairs_header.addStretch()
#         pairs_header.addWidget(QLabel("Show All:"))
#         pairs_header.addWidget(self.show_all)
#         left_layout.addLayout(pairs_header)
#         left_layout.addWidget(self.pairs_box)

#         # ---------- LEFT SIDE (API + Opt Files) ----------
#         right_layout = QVBoxLayout()
#         api_layout = QVBoxLayout()
#         api_layout.addWidget(QLabel("API Key:"))
#         api_layout.addWidget(self.api_key)
#         right_layout.addLayout(api_layout)

#         opt_layout = QHBoxLayout()
#         opt_layout.addWidget(QLabel("Opt Files Used:"))
#         opt_layout.addWidget(self.select_files_btn)
#         right_layout.addLayout(opt_layout)
#         right_layout.addWidget(self.opt_files)

#         # ---------- Combine Both 50/50 ----------
#         main_layout = QHBoxLayout()
#         main_layout.addLayout(left_layout, 1)   # 50%
#         main_layout.addLayout(right_layout, 1)  # 50%

#         # Add final layout to root
#         root.addLayout(main_layout)

#         # FILTERS
#         filters = QHBoxLayout()

#         for txt in ["Min % Diff", "Max Sets", "Min Profit", "Min Profit as %"]:
#             vbox = QVBoxLayout()
#             label = QLabel(txt)
#             box = QLineEdit()
#             box.setPlaceholderText(txt)
#             vbox.addWidget(label)
#             filters.addLayout(vbox)
#             vbox.addWidget(box)

#         # Add buttons at the end
#         filters.addWidget(QPushButton("SIFT SETS"))
#         filters.addWidget(QPushButton("AUTO SIFT"))

#         root.addLayout(filters)
#         # # ---------- Filters ----------
#         # filters = QHBoxLayout()
#         # filters.setSpacing(8)
#         # self.min_diff = QLineEdit(); self.min_diff.setPlaceholderText("Min % Diff"); self.min_diff.setFixedWidth(100)
#         # self.max_sets = QLineEdit(); self.max_sets.setPlaceholderText("Max Sets"); self.max_sets.setFixedWidth(100)
#         # self.min_profit = QLineEdit(); self.min_profit.setPlaceholderText("Min Profit"); self.min_profit.setFixedWidth(100)
#         # self.min_profit_pct = QLineEdit(); self.min_profit_pct.setFixedWidth(80)

#         # filters.addWidget(self.min_diff)
#         # filters.addWidget(self.max_sets)
#         # filters.addWidget(self.min_profit)
#         # filters.addStretch()
#         # filters.addWidget(QLabel("Min Profit as %"))
#         # filters.addWidget(self.min_profit_pct)
#         # root.addLayout(filters)

#         # ---------- Table Section ----------

#         # # Controls above table
#         controls = QHBoxLayout()
#         controls.setSpacing(8)
#         self.toggle_result = AnimatedToggle()
#         self.toggle_top_10 = AnimatedToggle()
#         self.toggle_top_100 = AnimatedToggle()
#         self.deselect_btn = QPushButton("DESELECT")
#         # --- Left side ---
#         left_layout = QHBoxLayout()
#         left_layout.addWidget(QLabel("Finder Result"))
#         left_layout.addWidget(self.toggle_result)
#         left_layout.addWidget(QLabel("Rank By Profit"))
#         left_layout.addStretch()  # pushes left group to the left

#         # --- Right side ---
#         right_layout = QHBoxLayout()
#         right_layout.addStretch()  # pushes right group to the right
#         right_layout.addWidget(self.deselect_btn)
#         right_layout.addWidget(QLabel("Hide unselected items"))
#         right_layout.addWidget(self.toggle_top_10)
#         right_layout.addWidget(QLabel("Top 10"))
#         right_layout.addWidget(self.toggle_top_100)
#         right_layout.addWidget(QLabel("Top 100"))

#         # --- Combine both ---
#         controls.addLayout(left_layout)
#         controls.addLayout(right_layout)

#         root.addLayout(controls)
        
#         self.table = QTableWidget(4, 10)
#         headers = [
#             "Pass No", "Bk Recovery", "Fwd Recovery", "Est Bk Weekly Profit",
#             "Est Fwd Weekly Profit", "Bk Trades", "Fwd Trades",
#             "Multiplier", "Total Profit", "POW Score"
#         ]
#         self.table.setHorizontalHeaderLabels(headers)
#         self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
#         # self.populate_table_with_sample()
#         root.addWidget(self.table)

#         # ---------- Bottom Section ----------
#         bottom = QHBoxLayout()
#         bottom.setSpacing(10)

#         table_controls = QHBoxLayout()


#         table_left= QHBoxLayout()
#         table_left.addWidget(QLabel("Pass Number:"))
#         self.pass_number = QLineEdit()
#         table_left.addWidget(self.pass_number)
#         table_left.addWidget(QLabel("Global DD"))
#         self.global_dd = QLineEdit()
#         table_left.addWidget(self.global_dd)
#         table_left.addWidget(QLabel("Individual DD"))
#         self.individual_dd = QLineEdit()
#         table_left.addWidget(self.individual_dd)
#         table_left.addStretch()

#         table_right = QHBoxLayout()
#         self.toggle_Generate_magic = AnimatedToggle()
#         self.toggle_Multiplier= AnimatedToggle()
#         self.generate_set_btn = QPushButton("GENERATE SET")
#         table_right.addWidget(QLabel("Generate Magic"))
#         table_right.addWidget(self.toggle_Generate_magic)
#         table_right.addWidget(QLabel("Multiplier"))
#         table_right.addWidget(self.toggle_Multiplier)
#         table_right.addWidget(self.generate_set_btn)
#         table_right.addStretch()

#         table_controls.addLayout(table_left)
#         table_controls.addLayout(table_right)
#         root.addLayout(table_controls)

#         bottom_message_layout= QVBoxLayout()
#         bottom_message_layout.addWidget(QLabel("Message Log:"))
#         self.bottom_message = QTextEdit()
#         self.bottom_message.setReadOnly(True)  # prevent user editing if it’s just for logs
#         self.bottom_message.setMinimumHeight(120)  # make it larger
#         bottom_message_layout.addWidget(self.bottom_message)
#         bottom.addLayout(bottom_message_layout)
#         root.addLayout(bottom)
        
#         self.layout.addLayout(root)
#         # Controller
#         self.controller = SetGeneratorController(self)
       
from aiagentfinder.ui.base_tab import BaseTab
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit,
    QHBoxLayout, QVBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QSpinBox, QComboBox,QListWidget,QSizePolicy,QSplitter
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from aiagentfinder.controllers.SetGenerator import SetGeneratorController
from aiagentfinder.utils.AnitmatedToggle import AnimatedToggle
class SetGenerator(BaseTab):
    
    def __init__(self, parent=None):
        super().__init__("Home Page", parent)
        self.experts = {}
    def init_ui(self):
        self.setStyleSheet("""
            SetGenerator {
            background-color: #1e1e1e;
        }
        QWidget {
            background-color: #1e1e1e;
            color: #e0dcdc;;
            font-family: Inter, Arial, sans-serif;
            font-size: 12px;
        }
        QPushButton:hover {
                background-color: #a0a8b0;
                color: black;
                border: 1px solid #ffcc00;
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
            height: 10px
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
            width:20px
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
        QLabel#label {
            margin-bottom: 0%;
        }
        QLineEdit#api_key {
        margin-bottom: 0%;
    }
    """)

        # self.layout.setContentsMargins(10, 10, 10, 10)
        

        # ---------- Header ----------
        header = QVBoxLayout()
        header.setContentsMargins(0,0,0,0)
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

        # # Add final layout to root
        # self.layout.addLayout(main_layout)
        self.pairs_box = QListWidget()
        self.show_all = AnimatedToggle(width=60, height=30, pulse=False)
        self.api_key = QLineEdit()
        self.select_files_btn = QPushButton("SELECT OPTIMISATION FILES")
        self.opt_files = QListWidget()
        
        self.pairs_box.setMaximumHeight(120)
        self.opt_files.setMaximumHeight(65)
         
        # ---------- SIZE POLICIES ----------
        self.pairs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.opt_files.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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

        # ---------- MAIN LAYOUT ----------
        headerlayout = QVBoxLayout()
        headerlayout.setContentsMargins(0, 0, 0, 0)
        headerlayout.addWidget(splitter)

        self.layout.addLayout(headerlayout)

        filters = QHBoxLayout()

        # Left group (filter inputs)
        left_layout = QHBoxLayout()

        # --- Min % Diff ---
        min_diff_box = QVBoxLayout()
        min_diff_box.addWidget(QLabel("Min % Diff"))
        self.min_diff = QLineEdit()
        self.min_diff.setPlaceholderText("Min % Diff")
        min_diff_box.addWidget(self.min_diff)
        left_layout.addLayout(min_diff_box)

        # --- Max Sets ---
        max_sets_box = QVBoxLayout()
        max_sets_box.addWidget(QLabel("Max Sets"))
        self.max_sets = QLineEdit()
        self.max_sets.setPlaceholderText("Max Sets")
        max_sets_box.addWidget(self.max_sets)
        left_layout.addLayout(max_sets_box)

        # --- Min Profit ---
        min_profit_box = QVBoxLayout()
        min_profit_box.addWidget(QLabel("Min Profit"))
        self.min_profit = QLineEdit()
        self.min_profit.setPlaceholderText("Min Profit")
        min_profit_box.addWidget(self.min_profit)
        left_layout.addLayout(min_profit_box)

        # --- Min Profit as % ---
        min_profit_pct_box = QVBoxLayout()
        min_profit_pct_box.addWidget(QLabel("Min Profit as %"))
        self.min_profit_pct = QLineEdit()
        self.min_profit_pct.setPlaceholderText("Min Profit as %")
        min_profit_pct_box.addWidget(self.min_profit_pct)
        left_layout.addLayout(min_profit_pct_box)

        # Add left group to filters
        filters.addLayout(left_layout)

        # Right group (buttons)
        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 20, 0, 0)
        self.sift_btn = QPushButton("SIFT SETS")
        self.auto_sift_btn = QPushButton("AUTO SIFT")
        right_layout.addWidget(self.sift_btn)
        right_layout.addWidget(self.auto_sift_btn)

        # Add right group to filters
        filters.addLayout(right_layout)

        # Add filters to main layout
        self.layout.addLayout(filters)


        # # Controls above table
        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.toggle_result = AnimatedToggle()
        self.toggle_top_10 = AnimatedToggle()
        self.toggle_top_100 = AnimatedToggle()
        self.deselect_btn = QPushButton("DESELECT")
        # --- Left side ---
        left_layout = QHBoxLayout()
        left_layout.addWidget(QLabel("Finder Result"))
        left_layout.addWidget(self.toggle_result)
        left_layout.addWidget(QLabel("Rank By Profit"))
        left_layout.addStretch()  # pushes left group to the left

        # --- Right side ---
        right_layout = QHBoxLayout()
        right_layout.addStretch()  # pushes right group to the right
        right_layout.addWidget(self.deselect_btn)
        right_layout.addWidget(QLabel("Hide unselected items"))
        right_layout.addWidget(self.toggle_top_10)
        right_layout.addWidget(QLabel("Top 10"))
        right_layout.addWidget(self.toggle_top_100)
        right_layout.addWidget(QLabel("Top 100"))

        # --- Combine both ---
        controls.addLayout(left_layout)
        controls.addLayout(right_layout)

        self.layout.addLayout(controls)
        
        self.table = QTableWidget(0,10)
        self.table.setFixedHeight(120)
        headers = [
            "Pass No", "Bk Recovery", "Fwd Recovery", "Est Bk Weekly Profit",
            "Est Fwd Weekly Profit", "Bk Trades", "Fwd Trades",
            "Multiplier", "Total Profit", "POW Score"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.populate_table_with_sample()
        self.layout.addWidget(self.table)

        # ---------- Bottom Section --------
        
        # --- Table Controls Section ---
        table_controls = QHBoxLayout()
        table_controls.setContentsMargins(0,0,0,0)

        # ---------- LEFT SECTION (3 INPUTS) ----------
        table_left = QHBoxLayout()
        table_left.setContentsMargins(0,0,0,10)
        table_left.setAlignment(Qt.AlignLeft)
        # table_left.setSpacing(15)

        # Pass Number
        pass_number_layout = QVBoxLayout()
        pass_number_label = QLabel("Pass Number:")
        self.pass_number = QLineEdit()
        # self.pass_number.setFixedWidth(120)
        pass_number_layout.addWidget(pass_number_label)
        pass_number_layout.addWidget(self.pass_number)
        table_left.addLayout(pass_number_layout)

        # Global DD
        global_dd_layout = QVBoxLayout()
        global_dd_label = QLabel("Global DD")
        self.global_dd = QLineEdit()
        # self.global_dd.setFixedWidth(150)
        global_dd_layout.addWidget(global_dd_label)
        global_dd_layout.addWidget(self.global_dd)
        table_left.addLayout(global_dd_layout)

        # Individual DD
        individual_dd_layout = QVBoxLayout()
        individual_dd_label = QLabel("Individual DD")
        self.individual_dd = QLineEdit()
        # self.individual_dd.setFixedWidth(150)
        individual_dd_layout.addWidget(individual_dd_label)
        individual_dd_layout.addWidget(self.individual_dd)
        table_left.addLayout(individual_dd_layout)


        # ---------- MIDDLE SECTION (TOGGLES) ----------
        table_middle = QHBoxLayout()
        # Generate Magic Toggle
        generate_magic_layout = QVBoxLayout()
        generate_magic_label = QLabel("Generate Magic")
        self.toggle_Generate_magic = AnimatedToggle(width=60, height=40,pulse=False)
        generate_magic_layout.addWidget(generate_magic_label, alignment=Qt.AlignCenter)
        generate_magic_layout.addWidget(self.toggle_Generate_magic, alignment=Qt.AlignCenter)
        table_middle.addLayout(generate_magic_layout)

        # Multiplier Toggle
        multiplier_layout = QVBoxLayout()
        multiplier_label = QLabel("Multiplier")
        self.toggle_Multiplier = AnimatedToggle(width=60, height=40,pulse=False)
        multiplier_layout.addWidget(multiplier_label, alignment=Qt.AlignCenter)
        multiplier_layout.addWidget(self.toggle_Multiplier, alignment=Qt.AlignCenter)
        table_middle.addLayout(multiplier_layout)


        # ---------- RIGHT SECTION (BUTTON) ----------
        table_right = QHBoxLayout()
        table_right.setContentsMargins(0,10,0,0)
        table_right.setAlignment(Qt.AlignRight)
        self.generate_set_btn = QPushButton("GENERATE SET")
        self.generate_set_btn.setFixedWidth(140)
        self.generate_set_btn.setStyleSheet("font-weight: bold; padding: 6px;")
        table_right.addWidget(self.generate_set_btn)


        # ---------- COMBINE SECTIONS ----------
        table_controls.addLayout(table_left, 6)
        table_controls.addStretch(1)
        table_controls.addLayout(table_middle, 3)
        table_controls.addStretch(1)
        table_controls.addLayout(table_right, 1)

        # ---------- ADD TO MAIN LAYOUT ----------
        self.layout.addLayout(table_controls)

        # # ---------- Bottom Message Section ----------
        bottom_message_layout = QVBoxLayout()
        bottom_message_layout.addWidget(QLabel("Message Log:"))

        self.bottom_message = QTextEdit()
        self.bottom_message.setReadOnly(True)       # Prevent user editing if it’s just for logs
        self.bottom_message.setMinimumHeight(70)    # Reasonable height
        self.bottom_message.setMaximumHeight(100)   # Keeps it compact
        bottom_message_layout.addWidget(self.bottom_message)

        # Add log section to bottom
        # bottom.addLayout(bottom_message_layout)

        # Add entire bottom section to main layout
        self.layout.addLayout(bottom_message_layout)

        # self.layout.addLayout(root)
        # Controller
        self.controller = SetGeneratorController(self)
    