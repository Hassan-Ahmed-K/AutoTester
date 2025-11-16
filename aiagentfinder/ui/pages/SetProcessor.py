from aiagentfinder.ui.base_tab import BaseTab
from PyQt5.QtWidgets import ( QLabel, QLineEdit, QPushButton, QTableView,QTableWidget,
    QHBoxLayout, QVBoxLayout, QGridLayout,QCheckBox, QSpinBox, QComboBox,QListWidget,QSizePolicy,QSplitter,QStyle,QDateEdit,QDoubleSpinBox,QHeaderView,QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont 
from aiagentfinder.utils.AnitmatedToggle import AnimatedToggle
from aiagentfinder.controllers.SetProcessor import SetProcessorController

class SetProcessorUI(BaseTab):
    
    def __init__(self, parent=None):
        super().__init__("Set Processor", parent)
        # self.experts = {}
    def init_ui(self):
        
        main_layout = self.main_layout
        main_layout.setSpacing(5)
  
        header = QVBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        title = QLabel("SetProcessor")
        title.setStyleSheet("font-size: 40px;")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")

        subtitle = QLabel(
            "In this section you can process individual set files. "
            "Your set file name <b>MUST</b> contain the full symbol name such as EURUSD in order for this to work. "
            "You are able to output various data and these files will be stored in the same directory "
            "that you have selected as your set file root. Additional folders will be created within that directory "
            "which will hold your chosen outputs."
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setObjectName("subtitle")

        header.addWidget(title)
        header.addWidget(subtitle)
        main_layout.addLayout(header)

        # ---------- FULL FORM LAYOUT ----------
        full_form_layout = QVBoxLayout()

        # ---------- FILE LAYOUT ----------
        first_file_layout = QGridLayout()
        first_file_layout.setHorizontalSpacing(5)
        first_file_layout.setVerticalSpacing(1)

        self.set_files = QLabel("Select Directory Containing Set Files:")
        self.input_set_files = QLineEdit()
        self.browse_set_files = QPushButton("Browse")

        self.toggle_graph = QCheckBox("Graph")
        self.toggle_graph.setChecked(True)
        self.toggle_overview = QCheckBox("Overview")
        self.toggle_csv = QCheckBox("CSV")
        self.toggle_semi_auto = QCheckBox("Semi-Auto")

        first_file_layout.addWidget(self.set_files, 0, 0, 1, 3)
        first_file_layout.addWidget(self.input_set_files, 1, 0, 1, 10)
        first_file_layout.addWidget(self.browse_set_files, 1, 10, 1, 2)
        first_file_layout.addWidget(QLabel("Outputs:"), 1, 12, 1, 1)
        first_file_layout.addWidget(self.toggle_graph, 1, 13)
        first_file_layout.addWidget(self.toggle_csv, 1, 14)
        first_file_layout.addWidget(self.toggle_overview, 1, 15)
        first_file_layout.addWidget(self.toggle_semi_auto, 1, 16)
        first_file_layout.setColumnStretch(1, 11)
        first_file_layout.setColumnStretch(10, 2)

        # ---------- MT5 + EXPERT LAYOUT ----------
        second_form_layout = QGridLayout()
        second_form_layout.setHorizontalSpacing(5)
        second_form_layout.setVerticalSpacing(5)

        second_form_layout.addWidget(QLabel("MT5 Directory:"), 1, 0)
        self.mt5_input = QLineEdit()
        self.mt5_btn = QPushButton("Browse")
        second_form_layout.addWidget(self.mt5_input, 1, 1, 1, 9)
        second_form_layout.addWidget(self.mt5_btn, 1, 10)

        second_form_layout.addWidget(QLabel("Expert File:"), 1, 11)
        self.expert_input = QComboBox()
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(self.refresh_btn.style().standardIcon(QStyle.SP_BrowserReload))
        self.expert_button = QPushButton("")
        self.expert_button.setIcon(self.expert_button.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        self.retry_input = QLineEdit()
        self.retry_input.setText("10")

        second_form_layout.addWidget(self.expert_input, 1, 12)
        second_form_layout.addWidget(self.refresh_btn, 1, 13)
        second_form_layout.addWidget(self.expert_button, 1, 14)
        second_form_layout.addWidget(QLabel("Retry Attempts:"), 1, 15)
        second_form_layout.addWidget(self.retry_input, 1, 16)
        second_form_layout.setColumnStretch(1, 6)
        second_form_layout.setColumnStretch(10, 2)
        second_form_layout.setColumnStretch(12, 3)
        second_form_layout.setColumnStretch(16, 2)

        # ---------- PAIR + DATA FOLDER ----------
        third_form_layout = QGridLayout()
        self.pair_prefix_input = QLineEdit()
        self.pair_suffix_input = QLineEdit()
        self.data_folder_input = QLineEdit()
        self.detected_toggle = AnimatedToggle()

        third_form_layout.addWidget(QLabel("Pair Prefix:"), 3, 0)
        third_form_layout.addWidget(self.pair_prefix_input, 3, 1)
        third_form_layout.addWidget(QLabel("Pair Suffix:"), 3, 2)
        third_form_layout.addWidget(self.pair_suffix_input, 3, 3)
        third_form_layout.addWidget(QLabel("Data Folder:"), 3, 4)
        third_form_layout.addWidget(self.data_folder_input, 3, 5, 1, 8)
        third_form_layout.addWidget(QLabel("Detected:"), 3, 14)
        third_form_layout.addWidget(self.detected_toggle, 3, 15)
        third_form_layout.addWidget(QLabel("Portable"), 3, 16)
        third_form_layout.setColumnStretch(5, 8)

        # ---------- DATE + DEPOSIT + TIMEFRAME ----------
        fourth_form_layout = QGridLayout()
        self.date_combo = QComboBox()
        self.date_combo.addItems([
            "Entire history",
            "Last month",
            "Last 3 months",
            "Last 6 months",
            "Last year",
            "Custom period"
        ])

        self.date_from = QDateEdit(QDate.currentDate())
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")

        self.deposit_input = QLineEdit()
        self.currency_input = QLineEdit()
        self.leverage_input = QDoubleSpinBox()
        self.leverage_input.setRange(0, 10000)
        self.leverage_input.setSingleStep(10)
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems([
            "M1", "M2", "M3", "M5", "M15", "M30", "H1", "H4", "H6", "H12", "Daily", "Weekly", "Monthly"
        ])

        fourth_form_layout.addWidget(QLabel("Date (DD/MM/YYYY):"), 4, 0)
        fourth_form_layout.addWidget(self.date_combo, 4, 1, 1, 2)
        fourth_form_layout.addWidget(self.date_from, 4, 3, 1, 2)
        fourth_form_layout.addWidget(self.date_to, 4, 5, 1, 2)
        fourth_form_layout.addWidget(QLabel("Deposit:"), 4, 7)
        fourth_form_layout.addWidget(self.deposit_input, 4, 8, 1, 2)
        fourth_form_layout.addWidget(QLabel("CCY:"), 4, 10)
        fourth_form_layout.addWidget(self.currency_input, 4, 11)
        fourth_form_layout.addWidget(QLabel("Leverage 1:"), 4, 12)
        fourth_form_layout.addWidget(self.leverage_input, 4, 13)
        fourth_form_layout.addWidget(QLabel("Timeframe:"), 4, 14)
        fourth_form_layout.addWidget(self.timeframe_combo, 4, 16)
        fourth_form_layout.setColumnStretch(1, 2)
        fourth_form_layout.setColumnStretch(3, 2)
        fourth_form_layout.setColumnStretch(5, 2)
        fourth_form_layout.setColumnStretch(8, 2)
        fourth_form_layout.setColumnStretch(11, 2)
        fourth_form_layout.setColumnStretch(13, 2)
        # fourth_form_layout.setColumnStretch(16, 2)


        status_layout=QHBoxLayout()
        self.status_label = QLabel()
        # self.testing_button = QPushButton("TESTING")
        status_layout.addWidget(self.status_label,alignment=Qt.AlignCenter)
        # status_layout.addWidget(self.testing_button,alignment=Qt.AlignCenter)

        # Add all form layouts
        full_form_layout.addLayout(first_file_layout)
        full_form_layout.addLayout(status_layout)
        full_form_layout.addLayout(second_form_layout)
        full_form_layout.addSpacing(5)
        full_form_layout.addLayout(third_form_layout)
        full_form_layout.addSpacing(5)
        full_form_layout.addLayout(fourth_form_layout)

        main_layout.addLayout(full_form_layout)

        # ---------- COPY BUTTONS ----------
        copy_layout = QHBoxLayout()
        copy_layout.addSpacing(5)
        self.copy_data_button = QPushButton("COPY DATA FROM SELECTED AUTOTESTER ENTRY")
        self.copy_dates_button = QPushButton("COPY DATES FROM SETFINDER")
        copy_layout.addWidget(self.copy_data_button)
        copy_layout.addWidget(self.copy_dates_button)
        main_layout.addLayout(copy_layout)
        
        # ---------- LOG AREA ----------
        log_layout = QVBoxLayout()
        log_label = QLabel("SINGLE SET TEST STATUS")
        # self.status_label = QLabel()
        log_label.setStyleSheet("font-size: 20px;")
        self.set_table = QTableWidget()
        self.set_table.setColumnCount(5)
        self.set_table.setHorizontalHeaderLabels(["Set File", "Status", "CSV", "Graph", "Overview"])
        self.set_table.horizontalHeader().setStretchLastSection(True)
        self.set_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.set_table.verticalHeader().setVisible(False)
        self.set_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.set_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.set_table.setSelectionMode(QAbstractItemView.SingleSelection)
        log_layout.addWidget(log_label, alignment=Qt.AlignCenter)
        # log_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        log_layout.addWidget(self.set_table)
        main_layout.addLayout(log_layout)

        # ---------- SCHEDULE ----------
        schedule_layout = QHBoxLayout()
        schedule_label = QLabel("Schedule Testing?")
        self.schedule_toggle = QCheckBox()
        self.schedule_datetime = QDateEdit(QDate.currentDate())
        self.schedule_datetime.setCalendarPopup(True)
        self.schedule_datetime.setDisplayFormat("yyyy-MM-dd")

        self.start_button = QPushButton("START")
        self.start_button.setMinimumWidth(200)

        self.stop_button = QPushButton("STOP")
        self.stop_button.setMinimumWidth(200)

        self.resume_button = QPushButton("RESUME TESTS")
        self.resume_button.setMinimumWidth(200)

        self.kill_button = QPushButton("KILL TASK")
        self.kill_button.setMinimumWidth(200)
       
        self.kill_button.hide()
        self.resume_button.hide()
        self.stop_button.hide()

        schedule_layout.addWidget(schedule_label)
        schedule_layout.addWidget(self.schedule_toggle)
        schedule_layout.addWidget(self.schedule_datetime)
        schedule_layout.addWidget(self.start_button)
        schedule_layout.addWidget(self.stop_button)
        schedule_layout.addWidget(self.resume_button)
        schedule_layout.addWidget(self.kill_button)

        container_layout = QHBoxLayout()
        container_layout.addStretch()
        container_layout.addLayout(schedule_layout)
        container_layout.addStretch()
        main_layout.addLayout(container_layout)

        self.controller = SetProcessorController(self)
        self.controller.toggle_date_fields(self.date_combo.currentText())



