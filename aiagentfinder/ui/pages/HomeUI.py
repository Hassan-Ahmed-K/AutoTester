
from aiagentfinder.ui.base_tab import BaseTab
from PyQt5.QtWidgets import (
    QLabel, QPushButton, QLineEdit,
     QVBoxLayout, QHBoxLayout,QWidget
)
from PyQt5.QtCore import QDate, Qt
from aiagentfinder.controllers.home import HomeController
class HomeUI(BaseTab):
    
    def __init__(self, parent=None):
        super().__init__("Home Page", parent)
        # self.experts = {}
    def init_ui(self):


        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        # main_layout.setContentsMargins(0,0,0,0)
        main_layout.setAlignment(Qt.AlignCenter)

        # ---------- Header ----------
        header_layout = QHBoxLayout()
        header_label = QLabel("AI Agent Finder")
        header_label.setObjectName("headerLabel") 
        header_label.setStyleSheet("font-size: 40px;") 
        header_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(header_label)
        main_layout.addLayout(header_layout)

        self.notice_label = QLabel(
            "In order to gain access to the app features you need to have an active "
            "and valid POW Membership.<br><br>"
            "Please enter your POW Portal credentials below, upon a successful login "
            "the app features will be unlocked.<br><br>"
            "You will need to have Chrome or Firefox installed for the authentication "
            "to complete successfully.<br><br>"
            '<span style="color:grey;">Login token still valid, application remains unlocked</span>'
        )
        self.notice_label.setWordWrap(True)
        self.notice_label.setStyleSheet("font-size: 15px;")
        self.notice_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.notice_label)


        # ---------- Login Title ----------
        self.login_widget = QWidget()
        login_layout = QVBoxLayout(self.login_widget)
        login_layout.setSpacing(20)
        login_layout.setContentsMargins(0,0,0,0)
        login_layout.setAlignment(Qt.AlignCenter)

        login_label = QLabel("Login")
        login_label.setStyleSheet("font-size: 30px;")
        login_label.setAlignment(Qt.AlignCenter)
        login_layout.addWidget(login_label)

        self.email = QLineEdit()
        self.email.setPlaceholderText("Enter Email")
        self.email.setStyleSheet("font-size: 15px; min-height:20px;")
        self.email.setFixedHeight(50)
        self.email.setFixedWidth(300)
        login_layout.addWidget(self.email, alignment=Qt.AlignCenter)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setStyleSheet("font-size: 15px; min-height:20px;")
        self.password.setFixedHeight(50)
        self.password.setFixedWidth(300)
        login_layout.addWidget(self.password, alignment=Qt.AlignCenter)

        self.signin_btn = QPushButton("Sign In")
        self.signin_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66BB6A;
                border: 1px solid #ffcc00;
            }
        """)
        self.signin_btn.setFixedHeight(40)
        self.signin_btn.setFixedWidth(300)
        login_layout.addWidget(self.signin_btn, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.login_widget)

        self.logout=QWidget()
        self.logout_layout=QHBoxLayout(self.logout)
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66BB6A;
                border: 1px solid #ffcc00;
            }
        """)
    
        self.logout_btn.setFixedHeight(40)
        self.logout_btn.setFixedWidth(300)
        self.logout_layout.addWidget(self.logout_btn)
        main_layout.addWidget(self.logout)


        # Apply final layout
        self.main_layout.addLayout(main_layout)

     
        self.controller = HomeController(self)
    
