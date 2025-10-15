from aiagentfinder.ui.base_tab import BaseTab
from aiagentfinder.controllers.SetFinder import SetFinderController
from PyQt5.QtWidgets import (
    QLabel, QPushButton, QLineEdit, QVBoxLayout,
    QHBoxLayout, QComboBox, QDateEdit, QDoubleSpinBox,
    QTextEdit, QCheckBox, QStyle, QWidget
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QSizePolicy


class SetFinderUI(BaseTab):
    def __init__(self, parent=None):
        super().__init__("Set Finder", parent)

    def init_ui(self):
        self.setStyleSheet(""" 
            SetFinderUI {
                background-color: #1e1e1e;
            }

            QWidget {
                background-color: #1e1e1e;
                 color: #ffffff;
                font-family: Inter;
                font-size: 12px;
            }

            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                border: 2px solid #555555;
                border-radius: 5px;
                padding: 2px 4px;
                font-size: 10px;
                background-color: #2b2b2b;
                color: #ffffff;
                height: 14px;
            }

            QPushButton {
                background-color: #808791;
                border: 1px solid #ffffff;
                border-radius: 4px;
                color: #ffffff;
                padding: 2px 6px;
                font-size: 10px;
                min-height: 22px;
            }

            QPushButton:hover {
                background-color: #a0a8b0;
                color: black;
                border: 1px solid #ffcc00;
            }

            QLabel#headerTitle {
                font-size: 32px;
                padding: 5px;
            }

            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                border: 1px solid #555555;
                selection-background-color: #ffcc00;
                selection-color: black;
            }

            QTextEdit {
                background-color: #2b2b2b;
                border: 2px solid #555555;
                border-radius: 5px;
                color: #ffffff;
                font-size: 11px;
                padding: 6px;

            }
             QLabel {
               color: #ffffff;
             }
        """)

        # ========== MAIN LAYOUT ==========
        main_layout = self.layout
        main_layout.setAlignment(Qt.AlignTop)

        # ====== HEADER ======
        header_label = QLabel("SetFinder")
        header_label.setObjectName("headerTitle")
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)

        # ====== htm DIRECTORY ======
        htm_dir_label = QLabel("Select html File Directory:")
        # htm_dir_label.setStyleSheet("font-weight: bold; color: #ffcc00;")
        main_layout.addWidget(htm_dir_label)

        htm_dir_row = QHBoxLayout()
        self.htm_dir_input = QLineEdit()
        self.htm_dir_input.setPlaceholderText("Path to MT5 html directory...")

        self.htm_dir_btn = QPushButton("Browse")
        icon = self.htm_dir_btn.style().standardIcon(QStyle.SP_FileDialogNewFolder)
        self.htm_dir_btn.setIcon(icon)
        self.htm_dir_btn.setMinimumWidth(100)
        # self.htm_dir_btn.clicked.connect(self.browse_htm_directory)

        htm_dir_row.addWidget(self.htm_dir_input)
        htm_dir_row.addWidget(self.htm_dir_btn)
        main_layout.addLayout(htm_dir_row)
        main_layout.addSpacing(20)

            # ---- FILTER INPUT ROW ----
        self.filter_row = QHBoxLayout()
        self.filter_row.setSpacing(20)

        # ---- Input widgets ----
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())

        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())

        self.account_dropdown = QComboBox()
        self.account_dropdown.addItems(["No", "1/4", "1/3", "1/2", "Custom"])

        self.balance_input = QLineEdit()
        self.balance_input.setPlaceholderText("Enter account balance...")

        self.trade_input = QDoubleSpinBox()
        self.trade_input.setRange(0, 100000)
        self.trade_input.setDecimals(0)

        self.risk_trade_input = QLineEdit()
        self.risk_trade_input.setPlaceholderText("Enter Risk Trade value...")

        self.max_consec_loss_input = QLineEdit()
        self.max_consec_loss_input.setPlaceholderText("Enter Est. Max Consec Loss...")

        # ---- Label + Input Layouts ----
        start_date_layout = QVBoxLayout()
        start_date_layout.setSpacing(0)
        start_date_layout.setContentsMargins(0, 0, 0, 0)
        start_label = QLabel("Start Date (DD/MM/YYYY)")
        # start_label.setStyleSheet("font-weight: bold; color: #ffcc00; margin-bottom: 2px;")
        start_date_layout.addWidget(start_label)
        start_date_layout.addWidget(self.start_date_input)

        end_date_layout = QVBoxLayout()
        end_date_layout.setSpacing(0)
        end_date_layout.setContentsMargins(0, 0, 0, 0)
        end_label = QLabel("End Date (DD/MM/YYYY)")
        # end_label.setStyleSheet("font-weight: bold; color: #ffcc00; margin-bottom: 2px;")
        end_date_layout.addWidget(end_label)
        end_date_layout.addWidget(self.end_date_input)

        forward_layout = QVBoxLayout()
        forward_layout.setSpacing(0)
        forward_layout.setContentsMargins(0, 0, 0, 0)
        forward_label = QLabel("Forward Period")
        # forward_label.setStyleSheet("font-weight: bold; color: #ffcc00; margin-bottom: 2px;")
        forward_layout.addWidget(forward_label)
        forward_layout.addWidget(self.account_dropdown)

        balance_layout = QVBoxLayout()
        balance_layout.setSpacing(0)
        balance_layout.setContentsMargins(0, 0, 0, 0)
        balance_label = QLabel("Account Balance")
        # balance_label.setStyleSheet("font-weight: bold; color: #ffcc00; margin-bottom: 2px;")
        balance_layout.addWidget(balance_label)
        balance_layout.addWidget(self.balance_input)

        # ---- Dynamic Container (horizontal group) ----
        self.dynamic_container = QHBoxLayout()

        # --- Target DD ---
        self.target_dd_widget = QWidget()
        target_dd_layout = QVBoxLayout(self.target_dd_widget)
        target_dd_layout.setSpacing(0)
        target_dd_layout.setContentsMargins(0, 0, 0, 0)
        target_dd_label = QLabel("Target DD")
        # target_dd_label.setStyleSheet("font-weight: bold; color: #ffcc00; margin-bottom: 2px;")
        target_dd_layout.addWidget(target_dd_label)
        target_dd_layout.addWidget(self.trade_input)

        # --- Risk Trade ---
        self.risk_trade_widget = QWidget()
        risk_trade_layout = QVBoxLayout(self.risk_trade_widget)
        risk_trade_layout.setSpacing(0)
        risk_trade_layout.setContentsMargins(0, 0, 0, 0)
        risk_trade_label = QLabel("Risk Trade")
        # risk_trade_label.setStyleSheet("font-weight: bold; color: #ffcc00; margin-bottom: 2px;")
        risk_trade_layout.addWidget(risk_trade_label)
        risk_trade_layout.addWidget(self.risk_trade_input)

        # --- Est. Max Consec Loss ---
        self.max_consec_loss_widget = QWidget()
        max_consec_loss_layout = QVBoxLayout(self.max_consec_loss_widget)
        max_consec_loss_layout.setSpacing(0)
        max_consec_loss_layout.setContentsMargins(0, 0, 0, 0)
        max_consec_loss_label = QLabel("Est. Max Consec Loss")
        # max_consec_loss_label.setStyleSheet("font-weight: bold; color: #ffcc00; margin-bottom: 2px;")
        max_consec_loss_layout.addWidget(max_consec_loss_label)
        max_consec_loss_layout.addWidget(self.max_consec_loss_input)


        # --- Add to main container ---
        self.dynamic_container.addWidget(self.target_dd_widget, 1)
        self.dynamic_container.addWidget(self.risk_trade_widget, 1)
        self.dynamic_container.addWidget(self.max_consec_loss_widget, 1)

        # --- Hide initially ---
        self.risk_trade_widget.hide()
        self.max_consec_loss_widget.hide()

        # ---- Add layouts to row ----
        self.filter_row.addLayout(start_date_layout, 1)
        self.filter_row.addLayout(end_date_layout, 1)
        self.filter_row.addLayout(forward_layout, 1)
        self.filter_row.addLayout(balance_layout, 1)
        self.filter_row.addLayout(self.dynamic_container, 1)

        main_layout.addLayout(self.filter_row)
        main_layout.addSpacing(10)

        # ===== TOGGLE BUTTON =====
        # toggle_row = QHBoxLayout()
        # toggle_row.setContentsMargins(0, 0, 0, 0)
        # toggle_row.setSpacing(10)

        # self.toggle_btn = QCheckBox("Use Risk/Consec Loss Instead of Target DD")
        # self.toggle_btn.setStyleSheet("font-weight: bold; color: #00ccff;")
        # # self.toggle_btn.stateChanged.connect(self.toggle_inputs)
        # toggle_row.addWidget(self.toggle_btn)
        # main_layout.addLayout(toggle_row)

        # ====== TOGGLE BUTTON ROW ======
        toggle_row = QHBoxLayout()
        toggle_row.setContentsMargins(0, 0, 0, 0)
        toggle_row.setSpacing(10)

        self.message_label = QLabel("Message Log")
        # self.message_label.setStyleSheet("font-weight: bold; color: #ffcc00;")

        right_toggle_layout = QHBoxLayout()
        right_toggle_layout.setSpacing(5)

        self.toggle_label = QLabel("Filter For 1 Trade Approach:")
        # self.toggle_label.setStyleSheet("font-weight: bold; color: #ffcc00;")

        self.toggle_btn = QCheckBox()
        self.toggle_btn.setChecked(False)
        self.toggle_btn.setStyleSheet("""
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
            }
        """)

        # self.toggle_btn.stateChanged.connect(self.on_toggle_trade_filter)

        right_toggle_layout.addWidget(self.toggle_label)
        right_toggle_layout.addWidget(self.toggle_btn)

        toggle_row.addWidget(self.message_label)
        toggle_row.addStretch()
        toggle_row.addLayout(right_toggle_layout)
        main_layout.addLayout(toggle_row)

        # ====== LARGE TEXT BOX ======
        self.log_text = QTextEdit()
        self.log_text.setPlaceholderText("Logs or output will appear here...")
        self.log_text.setMinimumHeight(250)
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.log_text)

        # ====== START BUTTON ======
        start_button_row = QHBoxLayout()
        start_button_row.setAlignment(Qt.AlignCenter)
        start_button_row.setContentsMargins(0, 10, 0, 0)

        self.start_button = QPushButton("Start")
        self.start_button.setMinimumWidth(200)
   
        start_button_row.addWidget(self.start_button)

        main_layout.addLayout(start_button_row)


        self.controller = SetFinderController(self)


