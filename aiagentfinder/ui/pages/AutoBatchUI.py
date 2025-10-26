# aiagentfinder/ui/pages/auto_batch_ui.py

from PyQt5.QtWidgets import (
    QLabel, QPushButton, QLineEdit, QListWidget,
    QFileDialog, QGridLayout, QVBoxLayout, QHBoxLayout, QComboBox,
    QSpinBox, QDoubleSpinBox, QDateEdit, QSizePolicy, QStyle, QCalendarWidget

)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QPalette, QColor

from aiagentfinder.ui.base_tab import BaseTab
from aiagentfinder.controllers.AutoBatch import AutoBatchController

class AutoBatchUI(BaseTab):
    """UI for the AutoBatch tab, inherits from BaseTab."""

    def __init__(self, parent=None):
        super().__init__("Auto Batch", parent)
        self.experts = {}

    def init_ui(self):
        
        """Override BaseTab's init_ui with AutoBatch-specific layout."""


        # self.setStyleSheet("""
        #     AutoBatchUI {
        #         background-color: #1e1e1e;
        #     }

        #     /* Base widget style */
        #     QWidget {
        #         background-color: #1e1e1e;
        #         color: #e0dcdc;
        #         font-family: Inter;
        #         font-size: 12px;
        #         line-height: 14px;

        #     }

        #     /* File inputs and normal inputs */
        #     QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
        #         border: 2px solid #555555;       /* nice gray border */
        #         border-radius: 5px;              /* rounded corners */
        #         padding: 1px 2px;     /* 🔽 reduced padding */
        #         font-size: 10px;      /* 🔽 smaller text */
        #         font-weight: bold;
        #         min-height: 20px;     /* 🔽 keeps them compact */
        #         background-color: #2b2b2b;
        #         color: #ffffff;
        #     }

        #     QLineEdit#queueList, QListWidget {
        #         border: 1px solid #808791;
        #         background-color: #2b2b2b;
        #         color: #ffffff;
        #     }

        #     /* Buttons */
        #     QPushButton {
        #        background-color: #808791;
        #         border: 1px solid #ffffff;
        #         border-radius: 4px;
        #         color: #ffffff;
                
        #         padding: 2px 6px;     /* 🔽 smaller padding */
        #         font-size: 10px;      /* 🔽 smaller text */
        #         min-height: 20px;     /* ensures consistent smaller height */
        #     }

        #     QPushButton:hover {
        #         background-color: #a0a8b0;
        #         color: black;
        #         border: 1px solid #ffcc00;
        #     }

        #     /* Header title */
        #     QLabel#headerTitle {
        #         font-size: 32px;
        #         padding: px;
        #     }
                           
        #     QComboBox QAbstractItemView {
        #        background-color: #2b2b2b;
        #        border: 1px solid #555555;
        #        selection-background-color: #ffcc00;
        #        selection-color: black;
        #    }
                           


        #     QListWidget{
        #             font-size : 12px       
        #             }
           

        #     /* ================= Calendar Styling ================= */
        #     QCalendarWidget QWidget { 
        #         background-color: #2b2b2b; 
        #         alternate-background-color: #1e1e1e;
        #     }

        #     QCalendarWidget QAbstractItemView:enabled {
        #         font-size: 12px;
        #         color: #e0dcdc;
        #         background-color: #2b2b2b;
        #         selection-background-color: #ffcc00;
        #         selection-color: black;
        #         gridline-color: #555555;
        #     }

        #     QCalendarWidget QToolButton {
                
        #         color: white;
        #         font-size: 8px;
        #         icon-size: 12px;
        #         background-color: #444444;
        #         /* border-radius: 5px; */
        #     }

            

        #     QCalendarWidget QMenu {
        #         background-color: #2b2b2b;
        #         color: #ffffff;
        #         border: 1px solid #555555;
        #     }

        #     QCalendarWidget QSpinBox { 
        #         width: 70px; 
        #         font-size: 12px; 
        #         color: #ffffff;
        #         background-color: #2b2b2b;
        #         border: 1px solid #555555;
        #     }

        #     QCalendarWidget QSpinBox::up-button {
        #         subcontrol-origin: border;
        #         subcontrol-position: top right;
        #     }

        #     QCalendarWidget QSpinBox::down-button {
        #         subcontrol-origin: border;
        #         subcontrol-position: bottom right;
        #     }
        # """)

        # height: 24px;
        #         width: 100px;
        self.deposit_info = {
        "balance": 0,
        "equity": 0,
        "margin": 0,
        "currency": "USD",
        "leverage": 0
    }

        # ================= Header =================
        header_layout = QHBoxLayout()
        header_label = QLabel("AutoTestQ")
        header_label.setObjectName("headerTitle")
        header_label.setStyleSheet("font-size: 40px;")
        header_label.setAlignment(Qt.AlignCenter)  
        header_layout.addWidget(header_label)
        header_layout.setContentsMargins(0, 5, 0, 5)  

        # ================= MT5 Block =================
        mt5_block_layout = QVBoxLayout()
        # mt5_block_layout.setSpacing(10)  # space between MT5 rows
        # mt5_block_layout.setContentsMargins(0, 0, 0,10)

        # MT5 Directory
        mt5_layout = QHBoxLayout()
        # mt5_layout.setSpacing(10)
        mt5_layout.addWidget(QLabel("MT5 Directory:"))
        self.mt5_dir_input = QLineEdit()
        self.mt5_dir_btn = QPushButton("Browse")

        icon = self.mt5_dir_btn.style().standardIcon(QStyle.SP_FileDialogNewFolder)  # type: ignore
        self.mt5_dir_btn.setIcon(icon)
        self.mt5_dir_btn.setMinimumWidth(100) 
        mt5_layout.addWidget(self.mt5_dir_input)
        mt5_layout.addWidget(self.mt5_dir_btn)
        mt5_block_layout.addLayout(mt5_layout)

        # Data Folder
        data_layout = QHBoxLayout()
        # data_layout.setSpacing(10)
        data_layout.addWidget(QLabel("Data Folder:"))
        self.data_input = QLineEdit()
        self.data_btn = QPushButton("Browse")

        icon = self.data_btn.style().standardIcon(QStyle.SP_FileDialogNewFolder)  # type: ignore
        self.data_btn.setIcon(icon)
        self.data_btn.setMinimumWidth(100) 

        data_layout.addWidget(self.data_input)
        data_layout.addWidget(self.data_btn)
        mt5_block_layout.addLayout(data_layout)

        # Report Folder
        report_layout = QHBoxLayout()
        # report_layout.setSpacing(10)
        report_layout.addWidget(QLabel("Report Folder:"))
        self.report_input = QLineEdit("Agent Finder Results")
        self.report_btn = QPushButton("Browse")
        icon = self.report_btn.style().standardIcon(QStyle.SP_FileDialogNewFolder)  # type: ignore
        self.report_btn.setIcon(icon)
        self.report_btn.setMinimumWidth(100) 

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

        # self.queue_list.setMinimumHeight(190)
        # self.queue_list.setMinimumWidth(250)

        left_layout.addWidget(self.queue_list)

        # Queue controls
        queue_controls = QGridLayout()
        # queue_controls.setSpacing(5)
        queue_controls.setHorizontalSpacing(8)
        queue_controls.setVerticalSpacing(8)

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
        
        left_layout.addLayout(queue_controls)  # Add the queue controls layout to the left layout (with stretch=1))

        # ================= Right Panel =================
        right_layout = QGridLayout()
        right_layout.setHorizontalSpacing(10)
        right_layout.setVerticalSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)


        self.testfile_input = QLineEdit()
        self.expert_input = QComboBox()
        self.expert_input.setMinimumWidth(350)  # Set the minimum width()
        self.expert_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.expert_input.addItems(["Please Attach Data File"])
        self.expert_button = QPushButton("Browse")
        icon = self.expert_button.style().standardIcon(QStyle.SP_FileDialogNewFolder)  # type: ignore
        self.expert_button.setIcon(icon)

        self.exper_copy_to_all = QPushButton("Copy To All")
        icon = self.exper_copy_to_all.style().standardIcon(QStyle.SP_FileDialogNewFolder)
        self.exper_copy_to_all.setIcon(icon)

        self.refresh_btn = QPushButton("Refresh")
        refresh_icon = self.refresh_btn.style().standardIcon(QStyle.SP_BrowserReload)
        self.refresh_btn.setIcon(refresh_icon)

        # self.refresh_btn.setMinimumWidth(100) 
        self.param_input = QLineEdit()
        self.param_button = QPushButton("Browse")
        icon = self.param_button.style().standardIcon(QStyle.SP_FileDialogNewFolder)  # type: ignore
        self.param_button.setIcon(icon)
        # self.param_button.setMinimumWidth(100) 
        self.symbol_input = QLineEdit()
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["M1","M2", "M3", "M4", "M5", "M6", "M10", "M12", "M15", "M20", "M30", "H1", "H2", "H3", "H4", "H6", "H8", "H12", "Daily", "Weekly", "Monthly"])
        self.symbol_prefix = QLineEdit()
        self.symbol_suffix = QLineEdit()
        
        # self.date_from = QDateEdit(QDate.currentDate())
        # self.date_to = QDateEdit(QDate.currentDate())

        self.date_combo = QComboBox()
        self.date_combo.addItems([
            "Entire history",
            "Last month",
            "Last 3 months",
            "Last 6 months",
            "Last year",
            "Custom period"
        ])

        # Date From
        self.date_from = QDateEdit(QDate.currentDate())
        self.date_from.setCalendarPopup(True) 
        self.date_from.setDisplayFormat("yyyy-MM-dd") 

        # Date To
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")

        self.date_from.setEnabled(False)
        self.date_to.setEnabled(False)



        self.forward_combo = QComboBox()
        self.forward_combo.addItems(["No", "1/4", "1/3", "1/2", "Custom"]) 

        self.forward_date = QDateEdit(QDate.currentDate())
        self.forward_date.setCalendarPopup(True)
        self.forward_date.setDisplayFormat("yyyy-MM-dd")

        self.forward_copy_down = QPushButton("Copy Down")
        icon = self.forward_copy_down.style().standardIcon(QStyle.SP_ArrowDown)  # type: ignore
        self.forward_copy_down.setIcon(icon)
        # self.forward_copy_down.setMinimumWidth(150) 

        
        self.delay_combo = QComboBox()
        self.delay_combo.addItems([
            "Zero latency, ideal execution",
            "1 ms", "5 ms", "10 ms", "20 ms",
            "50 ms", "100 ms", "500 ms", "1000 ms",
            "Random delay", "Custom Delay"
        ])
        self.delay_input = QSpinBox()
        self.delay_input.setRange(0, 100000)    
        self.delay_input.setSingleStep(10) 

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "Every tick",
            "Every tick based on real ticks",
            "1 minute OHLC",
            "Open prices only",
            "Math calculation"
        ])


        self.model_copy_to_all = QPushButton("Copy To All")
        icon = self.model_copy_to_all.style().standardIcon(QStyle.SP_FileDialogNewFolder)
        self.model_copy_to_all.setIcon(icon)

        self.deposit_input = QLineEdit()
        self.deposit_input.setText(str(self.deposit_info["balance"]))

        self.currency_input = QLineEdit()
        self.currency_input.setText(self.deposit_info["currency"])

        self.leverage_input = QDoubleSpinBox()
        self.leverage_input.setRange(0, 10000)    
        self.leverage_input.setSingleStep(10) 
        self.leverage_input.setValue(self.deposit_info["leverage"]) 

        self.optim_combo = QComboBox()
        self.optim_combo.addItems([
            "Disabled",
            "Fast genetic based algorithm",
            "Slow complete algorithm",
            "All symbols selected in MarketWatch"
        ])

        self.optim_copy_to_all = QPushButton("Copy To All")
        icon = self.optim_copy_to_all.style().standardIcon(QStyle.SP_FileDialogNewFolder)
        self.optim_copy_to_all.setIcon(icon)

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
        self.criterion_copy_to_all = QPushButton("Copy To All")
        icon = self.criterion_copy_to_all.style().standardIcon(QStyle.SP_FileDialogNewFolder)
        self.criterion_copy_to_all.setIcon(icon)

        # Row 0: Test File
        right_layout.addWidget(QLabel("Test File Name:"), 0, 0)
        right_layout.addWidget(self.testfile_input, 0, 1, 1, 5)  # spans all remaining cols

        # Row 1: Expert File
        right_layout.addWidget(QLabel("Expert File:"), 1, 0)
        right_layout.addWidget(self.expert_input, 1, 1, 1, 2)      # takes 2 cols
        right_layout.addWidget(self.refresh_btn, 1, 3 )             # col 3
        right_layout.addWidget(self.expert_button, 1, 4)           # col 4
        right_layout.addWidget(self.exper_copy_to_all, 1, 5 )       # col 5

        # Row 2: Param File
        right_layout.addWidget(QLabel("Param File:"), 2, 0)
        right_layout.addWidget(self.param_input, 2, 1, 1, 3)       # spans cols 1–3
        right_layout.addWidget(self.param_button, 2, 4, 1, 2)      # spans cols 4–5


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

        right_layout.addWidget(QLabel("Date (DD/MM/YYYY):"), 5, 0)
        right_layout.addWidget(self.date_combo, 5, 1, 1, 2)
        right_layout.addWidget(self.date_from, 5, 3)
        right_layout.addWidget(self.date_to, 5, 4, 1, 2)

        # Row 6: Forward Period
        right_layout.addWidget(QLabel("Forward Period:"), 6, 0)
        right_layout.addWidget(self.forward_combo, 6, 1, 1, 2)
        right_layout.addWidget(self.forward_date, 6, 3)
        right_layout.addWidget(self.forward_copy_down, 6, 4, 1, 2)

        # Row 7: Delay
        right_layout.addWidget(QLabel("Delay (ms):"), 7, 0)
        right_layout.addWidget(self.delay_combo, 7, 1, 1, 3)
        right_layout.addWidget(self.delay_input, 7, 4, 1, 2)

        # Row 8: Modeling
        right_layout.addWidget(QLabel("Modeling:"), 8, 0)
        right_layout.addWidget(self.model_combo, 8, 1, 1, 3)
        right_layout.addWidget(self.model_copy_to_all, 8, 4, 1, 2)

        # Row 9: Deposit, Currency, Leverage
        right_layout.addWidget(QLabel("Deposit:"), 9, 0)
        right_layout.addWidget(self.deposit_input, 9, 1)

        right_layout.addWidget(QLabel("Currency:"), 9, 2)
        right_layout.addWidget(self.currency_input, 9, 3)

        right_layout.addWidget(QLabel("Leverage:"), 9, 4)
        right_layout.addWidget(self.leverage_input, 9, 5)

        # Row 10: Optimization
        right_layout.addWidget(QLabel("Optimization:"), 11, 0)
        right_layout.addWidget(self.optim_combo, 11, 1, 1, 3)
        right_layout.addWidget(self.optim_copy_to_all, 11, 4, 1, 2)

        # Row 11: Optimization Criterion
        right_layout.addWidget(QLabel("Optimization Criterion:"), 12, 0)
        right_layout.addWidget(self.criterion_input, 12, 1, 1, 3)
        right_layout.addWidget(self.criterion_copy_to_all, 12, 4, 1, 2)


        
        # ================= Bottom =================
        bottom_layout = QHBoxLayout()
        # bottom_layout.setContentsMargins(10, 10, 10, 5)
        bottom_layout.setSpacing(15)
        bottom_layout.setAlignment(Qt.AlignCenter)  # type: ignore
        self.start_btn = QPushButton("START")
        self.start_btn.setMinimumWidth(250) 
        self.schedule_date = QDateEdit(QDate.currentDate())

        self.schedule_date.setCalendarPopup(True)

        # self.schedule_date.setMinimumWidth(200) 
        bottom_layout.addWidget(self.start_btn)
        bottom_layout.addWidget(QLabel("Schedule Testing?"))
        
        bottom_layout.addWidget(self.schedule_date)

        

        # ================= Combine All =================
        main_layout = QHBoxLayout()

        # main_layout.setSpacing(25)
        

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 3)

        # ===== Add layouts to BaseTab's layout =====
        self.main_layout.addLayout(header_layout)
        self.main_layout.addLayout(mt5_block_layout)
        self.main_layout.addLayout(main_layout)
        self.main_layout.addLayout(bottom_layout)


        # ===== Controller =====

        self.controller = AutoBatchController(self)
        self.controller.toggle_date_fields(self.date_combo.currentText())
        self.controller.adjust_forward_date(self.forward_combo.currentText())
        self.controller.update_delay_input(self.delay_combo.currentText())

