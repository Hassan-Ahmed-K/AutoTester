from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QListWidget,
    QFileDialog, QGridLayout, QVBoxLayout, QHBoxLayout, QComboBox, 
    QSpinBox, QDoubleSpinBox, QDateEdit
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QDate , Qt


class AutoBatchUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Agent Finder - AutoBatch")

        self.setGeometry(100, 100, 1200, 700)

        
        self.setStyleSheet("""
                /* Base widget style */
                QWidget {
                    background-color: #1e1e1e;
                    color: #e0dcdc;
                    font-family: Inter;
                    font-size: 10pt;
                }

                /* Shared inputs */
                QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QListWidget {
                    border: 1px solid #2b2b2b;
                    padding: 4px;
                }

                /* Special case for QListWidget */
                QListWidget {
                    border: 1px solid #808791;
                    color: #1e1e1e;   /* override text color */
                }

                /* Buttons */
                QPushButton {
                    background-color: #808791;
                    border: 1px solid #1e1e1e;
                    color: #1e1e1e;
                    padding: 4px;
                }

                QPushButton:hover {
                    background-color: #808791;
                    color: black;
                }

                /* Header title */
                QLabel#headerTitle {
                    font-size: 60px;
                    padding: 4px;
                }
                """
                )
        
        # ================= Header PANEL =================

        header_layout = QHBoxLayout()
        header_label = QLabel("AutoBatch")
        header_label.setObjectName("headerTitle")
        header_label.setAlignment(Qt.AlignCenter) #type:ignore
        header_layout.addWidget(header_label)

        # ================= mt5 PANEL =================
       

        mt5_block_layout = QVBoxLayout()

        # MT5 Directory
        mt5_layout = QHBoxLayout()
        mt5_layout.addWidget(QLabel("MT5 Directory:"))
        self.mt5_dir_input = QLineEdit()
        self.mt5_dir_btn = QPushButton("Browse")
        mt5_layout.addWidget(self.mt5_dir_input)
        mt5_layout.addWidget(self.mt5_dir_btn)
        mt5_block_layout.addLayout(mt5_layout)

        # Data Folder
        data_layout = QHBoxLayout()
        data_layout.addWidget(QLabel("Data Folder:"))
        self.data_input = QLineEdit()
        self.data_btn = QPushButton("Browse")
        data_layout.addWidget(self.data_input)
        data_layout.addWidget(self.data_btn)
        mt5_block_layout.addLayout(data_layout)

        # Report Folder
        report_layout = QHBoxLayout()
        report_layout.addWidget(QLabel("Report Folder:"))
        self.report_input = QLineEdit("Agent Finder Results")
        self.report_btn = QPushButton("Browse")
        report_layout.addWidget(self.report_input)
        report_layout.addWidget(self.report_btn)
        mt5_block_layout.addLayout(report_layout)

        main_layout = QHBoxLayout()

        # ================= LEFT PANEL =================
        left_layout = QVBoxLayout()

        left_layout.addWidget(QLabel("Pairs to Test:"))
        self.queue_list = QListWidget()
        left_layout.addWidget(self.queue_list)

        # Queue controls
        queue_controls = QGridLayout()
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

        queue_controls.addWidget(self.move_up_btn, 0, 0)
        queue_controls.addWidget(self.move_down_btn, 0, 1)
        queue_controls.addWidget(self.add_btn, 1, 0)
        queue_controls.addWidget(self.dup_btn, 1, 1)
        queue_controls.addWidget(self.del_btn, 1, 2)
        queue_controls.addWidget(self.save_btn, 2, 0)
        queue_controls.addWidget(self.load_btn, 2, 1)
        queue_controls.addWidget(self.export_btn, 3, 0, 1, 3)
        queue_controls.addWidget(self.non_corr_btn, 4, 0, 1, 3)
        queue_controls.addWidget(self.corr_btn, 5, 0, 1, 3)

        left_layout.addLayout(queue_controls)

        # ================= RIGHT PANEL =================
        right_layout = QGridLayout()

        self.testfile_input = QLineEdit()
        self.expert_input = QLineEdit()
        self.param_input = QLineEdit()
        self.symbol_input = QLineEdit("EURUSD")
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["M1", "M5", "M15", "H1", "H4", "D1"])

        self.date_from = QDateEdit(QDate.currentDate())
        self.date_to = QDateEdit(QDate.currentDate())
        self.forward_combo = QComboBox(); self.forward_combo.addItems(["1/4", "1/2", "Custom"])
        self.delay_input = QSpinBox(); self.delay_input.setValue(100)
        self.model_combo = QComboBox(); self.model_combo.addItems([
            "Every tick based on real ticks", "1 minute OHLC", "Open prices only"
        ])
        self.deposit_input = QDoubleSpinBox(); self.deposit_input.setValue(100000)
        self.currency_input = QLineEdit("USD")
        self.leverage_input = QSpinBox(); self.leverage_input.setValue(100)
        self.optim_combo = QComboBox(); self.optim_combo.addItems([
            "Fast genetic based algorithm", "All symbols", "Disabled"
        ])
        self.criterion_input = QLineEdit("Custom Max")

        right_layout.addWidget(QLabel("Test File Name:"), 0, 0); right_layout.addWidget(self.testfile_input, 0, 1)
        right_layout.addWidget(QLabel("Expert File:"), 1, 0); right_layout.addWidget(self.expert_input, 1, 1)
        right_layout.addWidget(QLabel("Param File:"), 2, 0); right_layout.addWidget(self.param_input, 2, 1)
        right_layout.addWidget(QLabel("Symbol:"), 3, 0); right_layout.addWidget(self.symbol_input, 3, 1)
        right_layout.addWidget(QLabel("Timeframe:"), 4, 0); right_layout.addWidget(self.timeframe_combo, 4, 1)
        right_layout.addWidget(QLabel("Date From:"), 5, 0); right_layout.addWidget(self.date_from, 5, 1)
        right_layout.addWidget(QLabel("Date To:"), 6, 0); right_layout.addWidget(self.date_to, 6, 1)
        right_layout.addWidget(QLabel("Forward Period:"), 7, 0); right_layout.addWidget(self.forward_combo, 7, 1)
        right_layout.addWidget(QLabel("Delay (ms):"), 8, 0); right_layout.addWidget(self.delay_input, 8, 1)
        right_layout.addWidget(QLabel("Modeling:"), 9, 0); right_layout.addWidget(self.model_combo, 9, 1)
        right_layout.addWidget(QLabel("Deposit:"), 10, 0); right_layout.addWidget(self.deposit_input, 10, 1)
        right_layout.addWidget(QLabel("Currency:"), 11, 0); right_layout.addWidget(self.currency_input, 11, 1)
        right_layout.addWidget(QLabel("Leverage:"), 12, 0); right_layout.addWidget(self.leverage_input, 12, 1)
        right_layout.addWidget(QLabel("Optimization:"), 13, 0); right_layout.addWidget(self.optim_combo, 13, 1)
        right_layout.addWidget(QLabel("Criterion:"), 14, 0); right_layout.addWidget(self.criterion_input, 14, 1)

        # ================= BOTTOM =================
        bottom_layout = QHBoxLayout()
        bottom_layout.setAlignment(Qt.AlignCenter)
        self.start_btn = QPushButton("START")
        

        # self.start_btn.setStyleSheet("background-color: #00ff00; color: black; font-weight: bold; font-size: 12pt;")
        self.schedule_date = QDateEdit(QDate.currentDate())

        bottom_layout.addWidget(self.start_btn)
        bottom_layout.addWidget(QLabel("Schedule Testing?"))
        bottom_layout.addWidget(self.schedule_date)

        # ================= COMBINE =================
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

        container = QVBoxLayout()
        container.addLayout(header_layout)      # add header first
        container.addLayout(mt5_block_layout)
        container.addLayout(main_layout)        # then main body (left + right)
        container.addLayout(bottom_layout)      # then bottom
        self.setLayout(container)

