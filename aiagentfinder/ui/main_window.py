# aiagentfinder/ui/main_window.py

from PyQt5.QtWidgets import QMainWindow, QTabWidget , QScrollArea, QSizePolicy,QWidget,QHBoxLayout,QListWidget,QListWidgetItem,QStackedWidget,QVBoxLayout,QPushButton,QSplitter
from PyQt5.QtGui import QIcon
from aiagentfinder.ui.pages.AutoBatchUI import AutoBatchUI
from aiagentfinder.ui.pages.SetGeneratorUI import SetGenerator
from aiagentfinder.ui.pages.SetProcessor import SetProcessorUI
from aiagentfinder.ui.pages.HtmlHunter import HtmlHunterUI
from aiagentfinder.ui.pages.SetCompare import SetCompareUI
from aiagentfinder.ui.pages.PortfolioPicker import PortfolioPickerUI
from aiagentfinder.ui.pages.HomeUI import HomeUI
from aiagentfinder.ui.pages.SetFinder import SetFinderUI
from PyQt5.QtCore import Qt, QPropertyAnimation
import keyring,json,time,os
from PyQt5.QtCore import QSize,QTimer
from aiagentfinder.utils.logger import Logger
from dotenv import load_dotenv
import pandas as pd


import inspect

load_dotenv()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        
        self.report_name = None  # Used for saving reports (Value Set in SetFinder and Used in Set Generator )
        self.report_df = pd.DataFrame()  # Used for saving reports (Value Set in SetFinder and Used in Set Generator )
        self.file_path = None



        # self.setMinimumSize(1300, 650)
        self.setWindowTitle("AI Agent Finder")
        self.setStyleSheet("background-color:#1e1e1e;")
        self.SERVICE_NAME = os.getenv("SERVICE_NAME")
        self.CACHE_KEY = os.getenv("CACHE_KEY")
        self.authenticated = False
        self.check_cache()  # Check cache on startup

         # Main container and layout
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sidebar_expanded = False  
        self.toggle_btn = QPushButton()
        self.toggle_btn.setIcon(QIcon(r"aiagentfinder\icons\menu-4-24.png"))  # path to your icon
        self.toggle_btn.setIconSize(QSize(20, 20))  # adjust size
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background:#3c3c3c; color:white; border:none;
                padding:8px 12px; border-radius:6px;
                font-size:11px;
                margin-right:0px;
            }
            QPushButton:hover {
                background:#505050;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        
    
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(40)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_layout.addWidget(self.toggle_btn)

        # Nav List
        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                color: #dcdcdc;
                border: none;
                font-size: 11px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 6px 8px 5px;
                border-radius: 6px;
                margin-bottom: 4px;   
            }
            QListWidget::item:hover {
                background: #787a7d;
                color: white;
            }
            QListWidget::item:selected {
                background: #787a7d;
                color: white;
            }
             QToolTip {
                background-color:#2b2b2b;
                color: #dcdcdc;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 10px;
            }
        """)

        # Home
        home_item = QListWidgetItem(QIcon(r"aiagentfinder\icons\home-7-24.png"), "Home")
        home_item.setToolTip("Home")
        self.nav_list.addItem(home_item)

        # Auto Batch
        batch_item = QListWidgetItem(QIcon(r"aiagentfinder\icons\search-13-24.png"), "Auto Batch")
        batch_item.setToolTip("Auto Batch")
        self.nav_list.addItem(batch_item)

        # Set Finder
        finder_item = QListWidgetItem(QIcon(r"aiagentfinder\icons\checkmark-24.png"), "Set Finder")
        finder_item.setToolTip("Set Finder")
        self.nav_list.addItem(finder_item)

        # Set Generator
        generator_item = QListWidgetItem(QIcon(r"aiagentfinder\icons\pages-1-24.png"), "Set Generator")
        generator_item.setToolTip("Set Generator")
        self.nav_list.addItem(generator_item)

        processor_item = QListWidgetItem(QIcon(r"aiagentfinder\icons\check.png"), "Set Processor")
        processor_item.setToolTip("Processor")
        self.nav_list.addItem(processor_item)

        hunter_item = QListWidgetItem(QIcon(r"aiagentfinder\icons\x-mark-3-24.png"), "Html Hunter")
        hunter_item.setToolTip("Html Hunter")
        self.nav_list.addItem(hunter_item)

        compare_item = QListWidgetItem(QIcon(r"aiagentfinder\icons\hyperlink_8577775.png"), "SetCompare")
        compare_item.setToolTip("Set Compare")
        self.nav_list.addItem(compare_item)

        portfolio_item = QListWidgetItem(QIcon(r"aiagentfinder\icons\wallet_3496745.png"), "Portfolio Picker")
        portfolio_item.setToolTip("Portfolio Picker")
        self.nav_list.addItem(portfolio_item)


        self.nav_list.setIconSize(QSize(20,20))
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)    
        # self.nav_list.setWordWrap(False) 
        self.sidebar_layout.addWidget(self.nav_list)

        self.home_page = HomeUI(self)
        self.setFinder_page =  SetFinderUI(self)
        self.autoBatch_page = AutoBatchUI(self)

        # Stacked Pages
        self.stack = QStackedWidget()

        self.stack.addWidget(self.home_page)  
        self.stack.addWidget(self.autoBatch_page)
        self.stack.addWidget(self.setFinder_page)
        self.stack.addWidget(SetGenerator())
        self.stack.addWidget(SetProcessorUI(self))
        self.stack.addWidget(HtmlHunterUI())
        self.stack.addWidget(SetCompareUI())
        self.stack.addWidget(PortfolioPickerUI())
        

        
        self.nav_list.currentRowChanged.connect(self.switch_page)
        self.nav_list.setCurrentRow(0)

        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(self.stack, 1)

        main_layout.addWidget(content, 1)
        self.setCentralWidget(container)


    # def toggle_sidebar(self):
    #     if self.sidebar.width() == 40:      
    #      self.sidebar.setFixedWidth(200)    
        
    #     else:                                  
    #         self.sidebar.setFixedWidth(40)
    def toggle_sidebar(self):
        # Sidebar expand/collapse with animation
        width = 200 if not self.sidebar_expanded else 40
        self.animate_sidebar(width)

        # Change icon + text
        if self.sidebar_expanded:
            # Collapsing
            self.toggle_btn.setIcon(QIcon(r"aiagentfinder\icons\menu-4-24.png"))
            self.toggle_btn.setText("")  # only icon
        else:
            # Expanding
            self.toggle_btn.setIcon(QIcon(r"aiagentfinder\icons\arrow-88-16.png"))
            self.toggle_btn.setText(" Hide Menu")  # icon + text

        self.sidebar_expanded = not self.sidebar_expanded

    def animate_sidebar(self, target_width):
        self.animation = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.animation.setDuration(250)
        self.animation.setStartValue(self.sidebar.width())
        self.animation.setEndValue(target_width)
        self.animation.start()

    def load_cache(self):
        if not self.SERVICE_NAME or not self.CACHE_KEY:
            print("⚠️ Missing SERVICE_NAME or CACHE_KEY in environment variables.")
            return None

        try:
            data_str = keyring.get_password(self.SERVICE_NAME, self.CACHE_KEY)
            if data_str:
                return json.loads(data_str)
        except Exception as e:
            print(f"⚠️ Keyring read error: {e}")
        return None

    
    
    # def switch_page(self, index):
    #     Logger.debug(f"Attempting to switch to page index: {index}, Authenticated: {self.authenticated}")
    #     if not self.authenticated and index != 0:
    #         Logger.warning("Unauthorized access attempt to restricted page")
    #         self.nav_list.setCurrentRow(0)
    #     else:
    #         Logger.debug(f"Switching to stack page {index}")
    #         self.stack.setCurrentIndex(index)

    def switch_page(self, index):
        Logger.debug(f"Attempting to switch to page index: {index}, Authenticated: {self.authenticated}")
        
        if not self.authenticated and index != 0:
            Logger.warning("Unauthorized access attempt to restricted page")
            self.nav_list.setCurrentRow(0)
            return

        Logger.debug(f"Switching to stack page {index}")
        self.stack.setCurrentIndex(index)

        # === Handle Page Open Events ===
        current_widget = self.stack.widget(index)

        print(f"Switched to page index: {index}, Widget: {type(current_widget).__name__}")

        # Example: when SetFinder page opens, check report_name
        if isinstance(current_widget, SetGenerator):
                current_widget.controller.update_pairs_box(self.report_name)
                current_widget.controller.show_dataframe_in_table(self.report_df)


    def check_cache(self):
        data = self.load_cache()
        print(data)
        if data and data.get("authenticated") and time.time() - data["validation_time"] < 3600:
            self.authenticated = True
            Logger.info("✅ Valid cache found, user authenticated")
          
        else:
            self.authenticated = False
            Logger.info("❌ No valid cache found, user not authenticated")


