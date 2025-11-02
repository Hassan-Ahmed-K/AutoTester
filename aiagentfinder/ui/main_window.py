# aiagentfinder/ui/main_window.py

from PyQt5.QtWidgets import QMainWindow, QTabWidget , QScrollArea, QSizePolicy,QWidget,QHBoxLayout,QListWidget,QListWidgetItem,QStackedWidget,QVBoxLayout,QPushButton,QSplitter
from PyQt5.QtGui import QIcon
from aiagentfinder.ui.pages.AutoBatchUI import AutoBatchUI
from aiagentfinder.ui.pages.SetGeneratorUI import SetGenerator
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

        self.report_dfs = {}
        self.report_files = []
        self.report_properties = {}
        self.selected_report_index = 0



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
        """)

        self.nav_list.addItem(QListWidgetItem(QIcon(r"aiagentfinder\icons\home-7-24.png"), "Home"))
        self.nav_list.addItem(QListWidgetItem(QIcon(r"aiagentfinder\icons\search-13-24.png"), "Auto Batch"))
        self.nav_list.addItem(QListWidgetItem(QIcon(r"aiagentfinder\icons\check.png"), "Set Finder"))
        self.nav_list.addItem(QListWidgetItem(QIcon(r"aiagentfinder\icons\pages-1-24.png"), "Set Generator"))
        

        self.nav_list.setIconSize(QSize(20,20))
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) 
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)    
        # self.nav_list.setWordWrap(False) 
        self.sidebar_layout.addWidget(self.nav_list)

        self.home_page = HomeUI(self)
        self.setFinder_page =  SetFinderUI(self)


        # Stacked Pages
        self.stack = QStackedWidget()

        self.stack.addWidget(self.home_page)  
        self.stack.addWidget(AutoBatchUI())
        self.stack.addWidget(self.setFinder_page)
        self.stack.addWidget(SetGenerator(self))
        
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

        try:

            if isinstance(current_widget, SetFinderUI):
                Logger.info("Set Finder page opened, updating report data if available")


                if not getattr(self, "report_properties", None) or not isinstance(self.report_properties, dict):
                    Logger.warning("No report dataframes found (self.report_dfs is None or invalid)")
                    return


                current_widget.controller.load_report_properties()
            # Handle SetGenerator page
            if isinstance(current_widget, SetGenerator):
                Logger.info("Set Generator page opened, updating report data if available")

                if not getattr(self, "report_files", None):
                    Logger.warning("No report files found (self.report_files is None or empty)")
                    return

                if not isinstance(self.report_files, list) or len(self.report_files) == 0:
                    Logger.warning("Report files list is empty or invalid")
                    return

                if not getattr(self, "report_dfs", None) or not isinstance(self.report_dfs, dict):
                    Logger.warning("No report dataframes found (self.report_dfs is None or invalid)")
                    return

                Logger.info(f"Available report files: {self.report_files}")
                Logger.info(f"Available report dataframe keys: {list(self.report_dfs.keys())}")

                report_file = os.path.basename(self.report_files[self.selected_report_index])
                Logger.info(f"First report filename: {report_file}")

                current_widget.controller.update_pairs_box(self.report_files)

            
                # current_widget.controller.show_dataframe_in_table(
                #     self.report_dfs.get(report_file, pd.DataFrame())
                # )

        except Exception as e:
            Logger.error(f"Error occurred while switching page to index {index}: {e}", exc_info=True)



    def check_cache(self):
        data = self.load_cache()
        print(data)
        if data and data.get("authenticated") and time.time() - data["validation_time"] < 3600:
            self.authenticated = True
            Logger.info("✅ Valid cache found, user authenticated")
          
        else:
            self.authenticated = False
            Logger.info("❌ No valid cache found, user not authenticated")


