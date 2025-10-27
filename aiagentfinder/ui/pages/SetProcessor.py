from aiagentfinder.ui.base_tab import BaseTab
from PyQt5.QtWidgets import ( QLabel, QLineEdit, QPushButton, QTextEdit,
    QHBoxLayout, QVBoxLayout, QGridLayout,QCheckBox, QSpinBox, QComboBox,QListWidget,QSizePolicy,QSplitter,QStyle,QDateEdit,QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont 
from aiagentfinder.utils.AnitmatedToggle import AnimatedToggle


class SetProcessorUI(BaseTab):
    
    def __init__(self, parent=None):
        super().__init__("Set Processor", parent)
        self.experts = {}
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

        set_files = QLabel("Select Directory Containing Set Files:")
        input_set_files = QLineEdit()
        browse_set_files = QPushButton("Browse")

        toggle_graph = QCheckBox("Graph")
        toggle_overview = QCheckBox("Overview")
        toggle_csv = QCheckBox("CSV")
        toggle_semi_auto = QCheckBox("Semi-Auto")

        first_file_layout.addWidget(set_files, 0, 0, 1, 3)
        first_file_layout.addWidget(input_set_files, 1, 0, 1, 10)
        first_file_layout.addWidget(browse_set_files, 1, 10, 1, 2)
        first_file_layout.addWidget(QLabel("Outputs:"), 1, 12, 1, 1)
        first_file_layout.addWidget(toggle_graph, 1, 13)
        first_file_layout.addWidget(toggle_csv, 1, 14)
        first_file_layout.addWidget(toggle_overview, 1, 15)
        first_file_layout.addWidget(toggle_semi_auto, 1, 16)
        first_file_layout.setColumnStretch(1, 11)
        first_file_layout.setColumnStretch(10, 2)

        # ---------- MT5 + EXPERT LAYOUT ----------
        second_form_layout = QGridLayout()
        second_form_layout.setHorizontalSpacing(5)
        second_form_layout.setVerticalSpacing(5)

        second_form_layout.addWidget(QLabel("MT5 Directory:"), 1, 0)
        mt5_input = QLineEdit()
        mt5_btn = QPushButton("Browse")
        second_form_layout.addWidget(mt5_input, 1, 1, 1, 9)
        second_form_layout.addWidget(mt5_btn, 1, 10)

        second_form_layout.addWidget(QLabel("Expert File:"), 1, 11)
        expert_input = QComboBox()
        refresh_btn = QPushButton()
        refresh_btn.setIcon(refresh_btn.style().standardIcon(QStyle.SP_BrowserReload))
        expert_button = QPushButton("")
        expert_button.setIcon(expert_button.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        retry_input = QLineEdit()

        second_form_layout.addWidget(expert_input, 1, 12)
        second_form_layout.addWidget(refresh_btn, 1, 13)
        second_form_layout.addWidget(expert_button, 1, 14)
        second_form_layout.addWidget(QLabel("Retry Attempts:"), 1, 15)
        second_form_layout.addWidget(retry_input, 1, 16)
        second_form_layout.setColumnStretch(1, 6)
        second_form_layout.setColumnStretch(10, 2)
        second_form_layout.setColumnStretch(12, 3)
        second_form_layout.setColumnStretch(16, 2)

        # ---------- PAIR + DATA FOLDER ----------
        third_form_layout = QGridLayout()
        pair_prefix_input = QLineEdit()
        pair_suffix_input = QLineEdit()
        data_folder_input = QLineEdit()
        detected_toggle = AnimatedToggle()

        third_form_layout.addWidget(QLabel("Pair Prefix:"), 3, 0)
        third_form_layout.addWidget(pair_prefix_input, 3, 1)
        third_form_layout.addWidget(QLabel("Pair Suffix:"), 3, 2)
        third_form_layout.addWidget(pair_suffix_input, 3, 3)
        third_form_layout.addWidget(QLabel("Data Folder:"), 3, 4)
        third_form_layout.addWidget(data_folder_input, 3, 5, 1, 8)
        third_form_layout.addWidget(QLabel("Detected:"), 3, 14)
        third_form_layout.addWidget(detected_toggle, 3, 15)
        third_form_layout.addWidget(QLabel("Portable"), 3, 16)
        third_form_layout.setColumnStretch(5, 8)

        # ---------- DATE + DEPOSIT + TIMEFRAME ----------
        fourth_form_layout = QGridLayout()
        date_combo = QComboBox()
        date_combo.addItems([
            "Entire history",
            "Last month",
            "Last 3 months",
            "Last 6 months",
            "Last year",
            "Custom period"
        ])

        date_from = QDateEdit(QDate.currentDate())
        date_from.setCalendarPopup(True)
        date_from.setDisplayFormat("yyyy-MM-dd")
        date_to = QDateEdit(QDate.currentDate())
        date_to.setCalendarPopup(True)
        date_to.setDisplayFormat("yyyy-MM-dd")

        deposit_input = QLineEdit()
        currency_input = QLineEdit()
        leverage_input = QDoubleSpinBox()
        leverage_input.setRange(0, 10000)
        leverage_input.setSingleStep(10)
        timeframe_combo = QComboBox()
        timeframe_combo.addItems([
            "M1", "M2", "M3", "M5", "M15", "M30", "H1", "H4", "H6", "H12", "Daily", "Weekly", "Monthly"
        ])

        fourth_form_layout.addWidget(QLabel("Date (DD/MM/YYYY):"), 4, 0)
        fourth_form_layout.addWidget(date_combo, 4, 1, 1, 2)
        fourth_form_layout.addWidget(date_from, 4, 3, 1, 2)
        fourth_form_layout.addWidget(date_to, 4, 5, 1, 2)
        fourth_form_layout.addWidget(QLabel("Deposit:"), 4, 7)
        fourth_form_layout.addWidget(deposit_input, 4, 8, 1, 2)
        fourth_form_layout.addWidget(QLabel("Currency:"), 4, 10)
        fourth_form_layout.addWidget(currency_input, 4, 11)
        fourth_form_layout.addWidget(QLabel("Leverage:"), 4, 12)
        fourth_form_layout.addWidget(leverage_input, 4, 13)
        fourth_form_layout.addWidget(QLabel("Timeframe:"), 4, 14)
        fourth_form_layout.addWidget(timeframe_combo, 4, 16)
        fourth_form_layout.setColumnStretch(1, 2)
        fourth_form_layout.setColumnStretch(3, 2)
        fourth_form_layout.setColumnStretch(5, 2)
        fourth_form_layout.setColumnStretch(8, 2)
        fourth_form_layout.setColumnStretch(11, 2)
        fourth_form_layout.setColumnStretch(13, 2)
        # fourth_form_layout.setColumnStretch(16, 2)

        # Add all form layouts
        full_form_layout.addLayout(first_file_layout)
        full_form_layout.addSpacing(20)
        full_form_layout.addLayout(second_form_layout)
        full_form_layout.addLayout(third_form_layout)
        full_form_layout.addLayout(fourth_form_layout)

        main_layout.addLayout(full_form_layout)

        # ---------- COPY BUTTONS ----------
        copy_layout = QHBoxLayout()
        copy_data_button = QPushButton("COPY DATA FROM SELECTED AUTOTESTER ENTRY")
        copy_dates_button = QPushButton("COPY DATES FROM SETFINDER")
        copy_layout.addWidget(copy_data_button)
        copy_layout.addWidget(copy_dates_button)
        main_layout.addLayout(copy_layout)

        # ---------- LOG AREA ----------
        log_layout = QVBoxLayout()
        log_label = QLabel("SINGLE SET TEST STATUS")
        log_label.setStyleSheet("font-size: 20px;")
        log_message = QTextEdit()
        log_layout.addWidget(log_label, alignment=Qt.AlignCenter)
        log_layout.addWidget(log_message)
        main_layout.addLayout(log_layout)

        # ---------- SCHEDULE ----------
        schedule_layout = QHBoxLayout()
        schedule_label = QLabel("Schedule Testing?")
        schedule_toggle = QCheckBox()
        schedule_datetime = QDateEdit(QDate.currentDate())
        schedule_datetime.setCalendarPopup(True)
        schedule_datetime.setDisplayFormat("yyyy-MM-dd")
        start_button = QPushButton("START")
        start_button.setMinimumWidth(200)
        resume_button = QPushButton("RESUME TESTS")
        resume_button.setMinimumWidth(200)

        schedule_layout.addWidget(schedule_label)
        schedule_layout.addWidget(schedule_toggle)
        schedule_layout.addWidget(schedule_datetime)
        schedule_layout.addWidget(start_button)
        schedule_layout.addWidget(resume_button)

        container_layout = QHBoxLayout()
        container_layout.addStretch()
        container_layout.addLayout(schedule_layout)
        container_layout.addStretch()
        main_layout.addLayout(container_layout)