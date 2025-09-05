from PyQt5.QtWidgets import QMessageBox, QFileDialog,QComboBox
from aiagentfinder.utils import MT5Manager , Logger
from aiagentfinder.queue_manager import QueueManager
import difflib



# import MetaTrader5 as mt5
import os, glob , datetime



class AutoBatchController:
    def __init__(self, ui):
        self.ui = ui
        self.mt5 = MT5Manager()
        self.symbols= []
        self.queue = QueueManager(ui) 

        # --- Connect UI buttons ---
        self.ui.mt5_dir_btn.clicked.connect(self.browse_mt5_dir)
        self.ui.data_btn.clicked.connect(self.browse_data_folder)
        self.ui.report_btn.clicked.connect(self.browse_report_folder)
        self.ui.expert_button.clicked.connect(self.browse_expert_file)
        self.ui.param_button.clicked.connect(self.browse_param_file)
        self.ui.add_btn.clicked.connect(self.add_test_to_queue)
        self.ui.testfile_input.textChanged.connect(self.update_clean_symbol)
        self.ui.data_input.textChanged.connect(self.update_expert_list)
        self.ui.refresh_btn.clicked.connect(self.load_experts)
        


    # ----------------------------
    # Browse MT5 installation path
    # ----------------------------
    def browse_mt5_dir(self):
    
        file_path, _ = QFileDialog.getOpenFileName(
            self.ui, "Select MT5 Terminal", "", "Executable Files (*.exe)"
        )
        if file_path:
            self.ui.mt5_dir_input.setText(file_path)
            Logger.info(f"MT5 terminal selected: {file_path}")

            # Try auto-detect Data Folder using --datafolder
            try:
                    # ⚡ Fallback: try default roaming path
                    roaming = os.path.join(os.environ["APPDATA"], "MetaQuotes", "Terminal")
                    candidates = glob.glob(os.path.join(roaming, "*"))

                    found = False
                    for folder in candidates:
                        if os.path.isdir(os.path.join(folder, "config")):
                            self.ui.data_input.setText(folder)
                            os.makedirs(os.path.join(folder, "Agent Finder Results"), exist_ok=True)
                            QMessageBox.information(
                                self.ui, "MT5 Data Folder",
                                f"Auto-selected Data Folder:\n{folder}"
                            )
                            Logger.success(f"Auto-detected MT5 Data Folder: {folder}")
                            found = True
                            break

                    if not found:
                        QMessageBox.warning(
                            self.ui, "MT5 Data Folder",
                            "⚠️ Could not detect Data Folder automatically. Please set it manually."
                        )
                        Logger.warning("Failed to auto-detect MT5 Data Folder")

            except Exception as e:
                QMessageBox.critical(
                    self.ui, "Error",
                    f"❌ Failed to fetch MT5 Data Folder.\nError: {str(e)}"
                )
                Logger.error("Error while detecting MT5 Data Folder", e)

            # Try to connect MT5 after setting terminal path
            success = self.mt5.connect(file_path)
            if success:
                QMessageBox.information(self.ui, "MT5 Connection", "✅ MT5 connected successfully!")
                Logger.success("MT5 connected successfully")
            else:
                QMessageBox.critical(self.ui, "MT5 Connection", "❌ Failed to connect MT5. Please check the path.")
                Logger.error("Failed to connect MT5")

    # ----------------------------
    # Browse MT5 data folder manually
    # ----------------------------
    def browse_data_folder(self):
        folder = QFileDialog.getExistingDirectory(self.ui, "Select Data Folder")
        if folder:
            self.ui.data_input.setText(folder)
            Logger.info(f"Data folder selected: {folder}")

    # ----------------------------
    # Browse MT5 report folder
    # ----------------------------
    def browse_report_folder(self):
        folder = QFileDialog.getExistingDirectory(self.ui, "Select Report Folder")
        if folder:
            self.ui.report_input.setText(folder)
            Logger.info(f"Report folder selected: {folder}")

  

    def get_report_root(self, data_folder):
        """Return or create the main report root"""
        report_root = os.path.join(data_folder, "Agent Finder Results")

        os.makedirs(report_root, exist_ok=True)
        Logger.info(f"Report root folder: {report_root}")
        return report_root

    def create_batch_subfolder(self, report_root):
        """Create a new timestamped batch folder"""
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_folder = os.path.join(report_root, ts)
        os.makedirs(batch_folder, exist_ok=True)
        Logger.info(f"Created batch folder: {batch_folder}")
        return batch_folder
    
    def browse_expert_file(self):
        # Build Expert folder path from Data Folder
        expert_folder = os.path.join(self.ui.data_input.text(), "MQL5", "Experts")

        if not os.path.exists(expert_folder):
            QMessageBox.warning(self.ui, "Error", f"Expert folder not found:\n{expert_folder}")
            Logger.warning(f"Expert folder not found: {expert_folder}")
            return None

        # Open file dialog starting in Expert folder
        file_path, _ = QFileDialog.getOpenFileName(
            self.ui,
            "Select Expert File",
            expert_folder,
            "Expert Files (*.ex5 *.mq5);;All Files (*)"
        )

        if file_path:
            # Update expert input field in UI (if you have one)
            if hasattr(self.ui, "expert_input"):
                self.ui.expert_input.setText(file_path)
                Logger.info(f"Expert file selected: {file_path}")
            return file_path

        return None
    
    
    def browse_param_file(self):
        data_folder = self.ui.data_input.text()

        if not data_folder:
            QMessageBox.warning(self.ui, "Error", "Please set the Data Folder first.")
            Logger.warning("Data folder is not set.")
            return None

        # Possible locations for .set files
        paths_to_check = [
            os.path.join(data_folder, "Tester"),                       # common
            os.path.join(data_folder, "MQL5", "Profiles", "Tester"),   # fallback
        ]

        # Pick the first one that exists
        default_path = None
        for path in paths_to_check:
            if os.path.exists(path):
                Logger.info(f"Param folder found: {path}")
                default_path = path
                break

        if not default_path:
            QMessageBox.warning(self.ui, "Error", "❌ No Param folder found in Data Folder.")
            Logger.warning("No Param folder found in Data Folder.")
            return None

        # Open dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self.ui, "Select Param File", default_path,
            "Set Files (*.set);;All Files (*)"
        )
        if file_path:
            self.ui.param_input.setText(file_path)
            Logger.info(f"Param file selected: {file_path}")
            
    

    def test_settings(self):
        test_name = self.ui.testfile_input.text().strip()
        if not test_name:
            QMessageBox.warning(self.ui, "Error", "Please enter a test file name")
            Logger.warning("Test file name is not set")
            return None

        settings = {
            "test_name": test_name,
            "expert": self.ui.expert_input.text().strip(),
            "param_file": self.ui.param_input.text().strip(),
            "symbol_prefix": self.ui.symbol_prefix.text().strip(),
            "symbol_suffix": self.ui.symbol_suffix.text().strip(),
            "symbol": self.ui.symbol_input.text().strip(),
            "timeframe": self.ui.timeframe_combo.currentText(),
            "date_from": self.ui.date_from.date().toString("yyyy-MM-dd"),
            "date_to": self.ui.date_to.date().toString("yyyy-MM-dd"),
            "forward": self.ui.forward_combo.currentText(),
            "delay": self.ui.delay_input.value(),
            "model": self.ui.model_combo.currentText(),
            "deposit": self.ui.deposit_input.value(),
            "currency": self.ui.currency_input.text().strip(),
            "leverage": self.ui.leverage_input.text().strip(),
            "optimization": self.ui.optim_combo.currentText(),
            "criterion": self.ui.criterion_input.currentText(),
        }

        return settings
    

    def add_test_to_queue(self):
        settings = self.test_settings()
        if settings:
            self.queue.add_test_to_queue(settings)

            QMessageBox.information(self.ui, "Added", f"Test '{settings['test_name']}' added to queue.")
            Logger.success(f"Test '{settings['test_name']}' added to queue.")

   
    

    def get_best_symbol(self,user_input: str) -> str:
        symbols = [s.name for s in self.mt5.mt5.symbols_get()]
        user_input = user_input.upper().strip()

        # exact match
        if user_input in symbols:
            Logger.info(f"Exact match found: {user_input}")
            return user_input

        # find closest
        match = difflib.get_close_matches(user_input, symbols, n=1, cutoff=0.4)
        if match:
            Logger.info(f"Closest match found: {match[0]}")
        return match[0] if match else ""
    
    def update_clean_symbol(self):
        if self.mt5.connected == False:
            return
        
        raw = self.ui.testfile_input.text().strip()
        best = self.get_best_symbol(raw)
        if best:
            Logger.info(f"Best symbol found: {best}")
            self.ui.symbol_input.setText(best)

    def update_expert_list(self):
        data_folder = self.ui.data_input.text()
        expert_folder = os.path.join(data_folder, "MQL5", r"Experts\Advisors")

        if not os.path.exists(expert_folder):
            return

        # Find all .ex5 and .mq5 files
        expert_files = glob.glob(os.path.join(expert_folder, "*.ex5"))
        self.ui.experts = {os.path.basename(f): f for f in expert_files}
        # Extract just the filenames
        expert_names = self.ui.experts.keys()

        # Update the combo box
        if hasattr(self.ui, "expert_input") and isinstance(self.ui.expert_input, QComboBox):
            current_expert = self.ui.expert_input.currentText()
            self.ui.expert_input.clear()
            self.ui.expert_input.addItems(expert_names)
            # Try to restore previous selection if still available
            if current_expert in expert_names:
                index = self.ui.expert_input.findText(current_expert)
                self.ui.expert_input.setCurrentIndex(index)


    def load_experts(self, expert_folder):
        if not expert_folder or not isinstance(expert_folder, str):
            Logger.warning("Invalid expert folder path")
            return None

        expert_files = glob.glob(os.path.join(expert_folder, "*.ex5"))
        experts_dict = {os.path.basename(f): f for f in expert_files}
        self.ui.experts = experts_dict

        if not expert_files:
            return None

        # Get the latest file
        latest_file = max(expert_files, key=os.path.getmtime)
        latest_name = os.path.basename(latest_file)

        self.ui.expert_input.setText(latest_name)
        return latest_file