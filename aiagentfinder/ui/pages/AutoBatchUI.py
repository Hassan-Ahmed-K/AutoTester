# aiagentfinder/ui/pages/auto_batch_ui.py

from PyQt5.QtWidgets import (
    QLabel, QPushButton, QLineEdit, QListWidget,
    QFileDialog, QGridLayout, QVBoxLayout, QHBoxLayout, QComboBox,
    QSpinBox, QDoubleSpinBox, QDateEdit, QSizePolicy
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QPalette, QColor

from aiagentfinder.ui.base_tab import BaseTab
from aiagentfinder.controller import AutoBatchController




class AutoBatchUI(BaseTab):
    """UI for the AutoBatch tab, inherits from BaseTab."""

    def __init__(self, parent=None):
        super().__init__("Auto Batch", parent)

    def init_ui(self):
        
        """Override BaseTab's init_ui with AutoBatch-specific layout."""


        self.setStyleSheet("""
            AutoBatchUI {
                background-color: #1e1e1e;
            }

            /* Base widget style */
            QWidget {
                background-color: #1e1e1e;
                color: #e0dcdc;
                font-family: Inter;
                font-size: 10pt;
            }

            /* File inputs and normal inputs */
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                border: 2px solid #555555;       /* nice gray border */
                border-radius: 5px;              /* rounded corners */
                padding: 6px;                     /* internal padding */
                background-color: #2b2b2b;
                color: #ffffff;
            }

            QLineEdit#queueList, QListWidget {
                border: 1px solid #808791;
                background-color: #2b2b2b;
                color: #ffffff;
            }

            /* Buttons */
            QPushButton {
                background-color: #808791;
                border: 2px solid #ffffff;
                border-radius: 5px;
                color: #ffffff;
                padding: 6px 12px;
            }

            QPushButton:hover {
                background-color: #a0a8b0;
                color: black;
                border: 2px solid #ffcc00;
            }

            /* Header title */
            QLabel#headerTitle {
                font-size: 30px;
                padding: 4px;
            }
        """)

        

        # ================= Header =================
        header_layout = QHBoxLayout()
        header_label = QLabel("AutoTestQ")
        header_label.setObjectName("headerTitle")
        header_label.setAlignment(Qt.AlignCenter)  
        header_layout.addWidget(header_label)
        # header_layout.setContentsMargins(0, 0, 0, 20)  

        # ================= MT5 Block =================
        mt5_block_layout = QVBoxLayout()
        mt5_block_layout.setSpacing(10)  # space between MT5 rows
        mt5_block_layout.setContentsMargins(0, 10, 0, 10)

        # MT5 Directory
        mt5_layout = QHBoxLayout()
        mt5_layout.setSpacing(10)
        mt5_layout.addWidget(QLabel("MT5 Directory:"))
        self.mt5_dir_input = QLineEdit()
        self.mt5_dir_btn = QPushButton("Browse")
        self.mt5_dir_btn.setMinimumWidth(150) 
        mt5_layout.addWidget(self.mt5_dir_input)
        mt5_layout.addWidget(self.mt5_dir_btn)
        mt5_block_layout.addLayout(mt5_layout)

        # Data Folder
        data_layout = QHBoxLayout()
        data_layout.setSpacing(10)
        data_layout.addWidget(QLabel("Data Folder:"))
        self.data_input = QLineEdit()
        self.data_btn = QPushButton("Browse")
        self.data_btn.setMinimumWidth(150) 
        data_layout.addWidget(self.data_input)
        data_layout.addWidget(self.data_btn)
        mt5_block_layout.addLayout(data_layout)

        # Report Folder
        report_layout = QHBoxLayout()
        report_layout.setSpacing(10)
        report_layout.addWidget(QLabel("Report Folder:"))
        self.report_input = QLineEdit("Agent Finder Results")
        self.report_btn = QPushButton("Browse")
        self.report_btn.setMinimumWidth(150) 
        report_layout.addWidget(self.report_input)
        report_layout.addWidget(self.report_btn)
        mt5_block_layout.addLayout(report_layout)

        # ================= Left Panel =================
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.addWidget(QLabel("Pairs to Test:"))

        self.queue_list = QListWidget()
        self.queue_list.setObjectName("queueList")
        self.queue_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.queue_list.setMinimumHeight(250)
        self.queue_list.setMinimumWidth(250)
        left_layout.addWidget(self.queue_list)

        # Queue controls
        queue_controls = QGridLayout()
        queue_controls.setHorizontalSpacing(10)
        queue_controls.setVerticalSpacing(10)

        # Define buttons
        self.move_up_btn = QPushButton("MOVE ▲")
        self.move_down_btn = QPushButton("MOVE ▼")
        self.add_btn = QPushButton("ADD")
        self.dup_btn = QPushButton("DUPE")
        self.del_btn = QPushButton("DEL")
        self.save_btn = QPushButton("SAVE")
        self.load_btn = QPushButton("LOAD")
        self.export_btn = QPushButton("EXPORT TEMPLATE")
        self.non_corr_btn = QPushButton("CREATE NON CORRELATED TEST LIST")
        self.corr_btn = QPushButton("SHOW CORRELATION MATRIX")

        # Arrange buttons in a 6-column grid
        queue_controls.addWidget(self.move_up_btn, 0, 0, 1, 3) 
        queue_controls.addWidget(self.move_down_btn, 0, 3, 1, 3)  

        queue_controls.addWidget(self.add_btn, 1, 0, 1, 2)  
        queue_controls.addWidget(self.dup_btn, 1, 2, 1, 2)      
        queue_controls.addWidget(self.del_btn, 1, 4, 1, 2)     

        queue_controls.addWidget(self.save_btn, 2, 0, 1, 3)     
        queue_controls.addWidget(self.load_btn, 2, 3, 1, 3)      

        queue_controls.addWidget(self.export_btn, 3, 0, 1, 3)   
        queue_controls.addWidget(self.non_corr_btn, 3, 3, 1, 3)   
        queue_controls.addWidget(self.corr_btn, 5, 0, 1, 6)      

        left_layout.addLayout(queue_controls)

        # ================= Right Panel =================
        right_layout = QGridLayout()
        right_layout.setHorizontalSpacing(10)
        right_layout.setVerticalSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)


        self.testfile_input = QLineEdit()
        self.expert_input = QLineEdit()
        self.expert_button = QPushButton("Browse")
        self.expert_button.setMinimumWidth(150) 
        self.param_input = QLineEdit()
        self.param_button = QPushButton("Browse")
        self.param_button.setMinimumWidth(150) 
        self.symbol_prefix = QLineEdit()
        self.symbol_suffix = QLineEdit()
        self.symbol_input = QLineEdit()
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["M1", "M5", "M15", "H1", "H4", "D1"])
        self.date_from = QDateEdit(QDate.currentDate())
        self.date_to = QDateEdit(QDate.currentDate())
        self.forward_combo = QComboBox()
        self.forward_combo.addItems(["1/4", "1/2", "Custom"])
        self.delay_input = QSpinBox()
        self.delay_input.setValue(100)
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "Every tick",
            "Every tick based on real ticks",
            "1 minute OHLC",
            "Open prices only",
            "Math calculation"
        ])
        self.deposit_input = QDoubleSpinBox()
        self.deposit_input.setValue(100000)
        self.currency_input = QLineEdit("USD")
        self.leverage_input = QLineEdit("")
        self.optim_combo = QComboBox()
        self.optim_combo.addItems([
            "Disabled",
            "Fast genetic based algorithm",
            "Slow complete algorithm",
            "All symbols selected in MarketWatch"
        ])
        self.criterion_input = QComboBox()
        self.criterion_input.addItems([
            "Balance Max",
            "Profit Factor Max",
            "Expected Payoff Max",
            "Drawdown Max",
            "Recovery Factor Max",
            "Sharpe Ratio Max",
            "Custom max",
            "Complex Criterion max"
        ])

        # Row 0: Test File
        right_layout.addWidget(QLabel("Test File Name:"), 0, 0)
        right_layout.addWidget(self.testfile_input, 0, 1, 1, 5)  # stretched full row

        # Row 1: Expert File
        right_layout.addWidget(QLabel("Expert File:"), 1, 0)
        right_layout.addWidget(self.expert_input, 1, 1, 1, 4)   # input takes 4 columns
        right_layout.addWidget(self.expert_button, 1, 5)          # button in last column

        # Row 2: Param File
        right_layout.addWidget(QLabel("Param File:"), 2, 0)
        right_layout.addWidget(self.param_input, 2, 1, 1, 4)
        right_layout.addWidget(self.param_button, 2, 5)

        # Row 3: Symbol & Timeframe
        right_layout.addWidget(QLabel("Symbol:"), 3, 0)
        right_layout.addWidget(self.symbol_input, 3, 1, 1, 2)
        right_layout.addWidget(QLabel("Timeframe:"), 3, 3)
        right_layout.addWidget(self.timeframe_combo, 3, 4, 1, 2)

        # Row 4: Symbol Prefix & Suffix
        right_layout.addWidget(QLabel("Symbol Prefix:"), 4, 0)
        right_layout.addWidget(self.symbol_prefix, 4, 1, 1, 2)
        right_layout.addWidget(QLabel("Symbol Suffix:"), 4, 3)
        right_layout.addWidget(self.symbol_suffix, 4, 4, 1, 2)

        # Row 5: Date From & To
        right_layout.addWidget(QLabel("Date From:"), 5, 0)
        right_layout.addWidget(self.date_from, 5, 1, 1, 2)
        right_layout.addWidget(QLabel("Date To:"), 5, 3)
        right_layout.addWidget(self.date_to, 5, 4, 1, 2)

        # Row 6: Forward & Delay
        right_layout.addWidget(QLabel("Forward Period:"), 6, 0)
        right_layout.addWidget(self.forward_combo, 6, 1, 1, 2)
        right_layout.addWidget(QLabel("Delay (ms):"), 6, 3)
        right_layout.addWidget(self.delay_input, 6, 4, 1, 2)

        # Row 7: Modeling
        right_layout.addWidget(QLabel("Modeling:"), 7, 0)
        right_layout.addWidget(self.model_combo, 7, 1, 1, 5)  # stretch full row

        # Row 8: Deposit & Currency
        right_layout.addWidget(QLabel("Deposit:"), 8, 0)
        right_layout.addWidget(self.deposit_input, 8, 1, 1, 2)
        right_layout.addWidget(QLabel("Currency:"), 8, 3)
        right_layout.addWidget(self.currency_input, 8, 4, 1, 2)

        # Row 9: Leverage
        right_layout.addWidget(QLabel("Leverage:"), 9, 0)
        right_layout.addWidget(self.leverage_input, 9, 1, 1, 5)  # stretch full row

        # Row 10: Optimization
        right_layout.addWidget(QLabel("Optimization:"), 10, 0)
        right_layout.addWidget(self.optim_combo, 10, 1, 1, 5)

        # Row 11: Optimization Criterion
        right_layout.addWidget(QLabel("Optimization Criterion:"), 11, 0)
        right_layout.addWidget(self.criterion_input, 11, 1, 1, 5)


        # ================= Bottom =================
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(10, 30, 10, 10)
        bottom_layout.setSpacing(15)
        bottom_layout.setAlignment(Qt.AlignCenter)  # type: ignore
        self.start_btn = QPushButton("START")
        self.start_btn.setMinimumWidth(250) 
        self.schedule_date = QDateEdit(QDate.currentDate())
        self.schedule_date.setMinimumWidth(200) 
        bottom_layout.addWidget(self.start_btn)
        bottom_layout.addWidget(QLabel("Schedule Testing?"))
        
        bottom_layout.addWidget(self.schedule_date)

        

        # ================= Combine All =================
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 3)

        # ===== Add layouts to BaseTab's layout =====
        self.layout.addLayout(header_layout)
        self.layout.addLayout(mt5_block_layout)
        self.layout.addLayout(main_layout)
        self.layout.addLayout(bottom_layout)


        # ===== Controller =====
        self.controller = AutoBatchController(self)