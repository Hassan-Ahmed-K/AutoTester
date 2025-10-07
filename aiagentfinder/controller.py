# type : ignore
from PyQt5.QtWidgets import QMessageBox, QFileDialog,QComboBox, QListWidget, QListWidgetItem, QDialog,QApplication
from PyQt5.QtCore import QDate ,  QThread , QTimer , Qt
from aiagentfinder.utils import MT5Manager , Logger , MT5Worker, CorrelationWorker
from aiagentfinder.queue_manager import QueueManager
import difflib
import random
import requests
import pandas as pd
from io import StringIO
import matplotlib.pyplot as plt
import seaborn as sns
from aiagentfinder.utils.QuantityDialog import QuantityDialog
from aiagentfinder.utils.TextDialog import TextDialog
from aiagentfinder.utils.RadioDialog import RadioDialog
import os, glob , datetime, re
import psutil
from aiagentfinder.utils.workerThread import Worker, ThreadRunner



class AutoBatchController:
    def __init__(self, ui):
        self.ui = ui
        self.current_index = None
        self.mt5 = MT5Manager()
        self.runner = ThreadRunner()


        
        self.symbols= []
        self.queue = QueueManager(ui) 
        self.selected_queue_item_index = -1
        self.non_correlated_popus_option = {}
        self.ui.mt5_dir_input

        # --- Connect UI buttons ---
        self.ui.mt5_dir_btn.clicked.connect(self.browse_mt5_dir)
        self.ui.data_btn.clicked.connect(self.browse_data_folder)
        self.ui.report_btn.clicked.connect(self.browse_report_folder)
        self.ui.expert_button.clicked.connect(self.browse_expert_file)
        self.ui.exper_copy_to_all.clicked.connect(lambda: self.copy_parameter({"expert": self.ui.expert_input.currentText()}))
        self.ui.param_button.clicked.connect(self.browse_param_file)
        self.ui.add_btn.clicked.connect(self.add_test_to_queue)
        self.ui.testfile_input.textChanged.connect(self.update_clean_symbol)
        self.ui.data_input.textChanged.connect(self.update_expert_list)
        self.ui.refresh_btn.clicked.connect(self.refresh_expert)
        self.ui.date_combo.currentTextChanged.connect(self.toggle_date_fields)
        self.ui.date_combo.currentTextChanged.connect(self.adjust_forward_date)
        self.ui.forward_combo.currentTextChanged.connect(self.adjust_forward_date)
        self.ui.forward_copy_down.clicked.connect(lambda: self.copy_parameter({"forward": self.ui.forward_combo.currentText(), "forward_date": self.ui.forward_date.date().toString("yyyy-MM-dd")}))
        self.ui.model_copy_to_all.clicked.connect(lambda: self.copy_parameter({"model": self.ui.model_combo.currentText()}))
        self.ui.delay_combo.currentTextChanged.connect(self.update_delay_input)
        self.ui.optim_copy_to_all.clicked.connect(lambda: self.copy_parameter({"optimization": self.ui.optim_combo.currentText()}))
        self.ui.criterion_copy_to_all.clicked.connect(lambda: self.copy_parameter({"criterion": self.ui.criterion_input.currentText()}))
        self.ui.queue_list.itemClicked.connect(self.on_item_clicked)
        self.ui.move_up_btn.clicked.connect(self.move_up)
        self.ui.move_down_btn.clicked.connect(self.move_down)
        self.ui.dup_btn.clicked.connect(self.dup_down)
        self.ui.del_btn.clicked.connect(self.delete_test)
        self.ui.save_btn.clicked.connect(self.queue.save_queue)
        self.ui.load_btn.clicked.connect(self.queue.load_queue)
        self.ui.export_btn.clicked.connect(self.queue.export_template)
        self.ui.corr_btn.clicked.connect(lambda:self.get_correlation(market="forex",period=50, symbols=None))
        self.ui.non_corr_btn.clicked.connect(lambda: self.show_quantity_popup(title="Test Pairs", text="How many pairs will be in you test list: "))
        self.ui.start_btn.clicked.connect(lambda: self.on_start_button_clicked(data_path = self.ui.data_input.text(), mt5_path =self.ui.mt5_dir_input.text(), report_path = self.ui.report_input.text() ))
        self.ui.queue_list.itemClicked.connect(self.on_test_selected)


    def browse_mt5_dir(self):
        Logger.info("Opening file dialog to select MT5 terminal...")

        file_path, _ = QFileDialog.getOpenFileName(
            self.ui, "Select MT5 Terminal", "", "Executable Files (*.exe)"
        )
        if not file_path:
            Logger.warning("No MT5 terminal selected by user.")
            return

        self.ui.mt5_dir_input.setText(file_path)
        Logger.success(f"MT5 terminal selected: {file_path}")

        # ---------------------------
        # TASK for background thread
        # ---------------------------
        def task(file_path):
            Logger.debug(f"Background task started for MT5 file: {file_path}")
            result = {
                "file_path": file_path,
                "data_folder": None,
                "deposit_info": None,
            }

            try:
                Logger.info("Attempting to connect to MT5...")
                success = self.mt5.connect(file_path)

                if success:
                    Logger.success("Successfully connected to MT5.")
                    dataPath = self.mt5.get_dataPath()

                    if dataPath:
                        result["data_folder"] = dataPath
                        os.makedirs(os.path.join(dataPath, "Agent Finder Results"), exist_ok=True)
                        Logger.success(f"MT5 Data Folder detected: {dataPath}")
                    else:
                        Logger.warning("Could not retrieve MT5 Data Folder from terminal_info.")

                    # --- Deposit info ---
                    Logger.info("Fetching deposit info...")
                    result["deposit_info"] = self.mt5.get_deposit()

                    if result["deposit_info"]:
                        Logger.success(f"Deposit info retrieved: Balance={result['deposit_info']['balance']}, "
                                       f"Currency={result['deposit_info']['currency']}, "
                                       f"Leverage={result['deposit_info']['leverage']}")
                    else:
                        Logger.warning("No deposit info retrieved from MT5.")

                    Logger.info("Fetching symbol list...")
                    self.mt5.get_symbol_list()

                    Logger.debug("Disconnecting from MT5...")
                    self.mt5.disconnect()
                    Logger.info("Disconnected from MT5.")

                    exe_name = os.path.basename(file_path)
                    Logger.debug(f"Looking for MT5 process: {exe_name}")

                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == exe_name:
                            try:
                                proc.terminate()
                                Logger.success(f"Closed MT5 process: {exe_name} (PID: {proc.info['pid']})")
                            except Exception as e:
                                Logger.error(f"Could not close MT5 process {exe_name}: {e}")

                else:
                    Logger.error(f"Failed to connect to MT5: {self.mt5.last_error()}")

            except Exception as e:
                Logger.error("Exception while connecting to MT5", e)

            Logger.debug("Background task finished.")
            return result

        # ---------------------------
        # CALLBACKS (main thread)
        # ---------------------------
        def on_done(result):
            Logger.debug("on_done callback triggered with result.")
            if result["data_folder"]:
                self.ui.data_input.setText(result["data_folder"])
                Logger.info(f"Auto-selected Data Folder: {result['data_folder']}")
            else:
                Logger.warning("MT5 Data Folder could not be detected automatically.")
                QMessageBox.warning(
                    self.ui, "MT5 Data Folder",
                    "⚠️ Could not detect Data Folder automatically. Please set it manually."
                )

            if result["deposit_info"]:
                self.ui.deposit_info = result["deposit_info"]
                self.ui.deposit_input.setText(str(result["deposit_info"]["balance"]))
                self.ui.currency_input.setText(result["deposit_info"]["currency"])
                self.ui.leverage_input.setValue(result["deposit_info"]["leverage"])
                QMessageBox.information(self.ui, "MT5 Connection", "✅ MT5 connected successfully!")
                Logger.success("MT5 connection completed successfully and UI updated.")
            else:
                QMessageBox.critical(self.ui, "MT5 Connection", "❌ Failed to connect MT5. Please check the path.")
                Logger.error("Deposit info missing — MT5 connection considered failed.")

            QApplication.processEvents()
        
        def on_error(err):
            Logger.error(f"Error in MT5 setup thread: {err}")
            QMessageBox.critical(
                self.ui, "Error",
                f"❌ Failed during MT5 setup.\nError: {str(err)}"
            )

        # ---------------------------
        # Run threaded
        # ---------------------------
        Logger.info("Starting MT5 setup in background thread...")
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task, file_path)

    def browse_data_folder(self):
        Logger.info("Opening folder dialog to select Data Folder...")

        folder = QFileDialog.getExistingDirectory(self.ui, "Select Data Folder")
        if not folder:
            QMessageBox.warning(self.ui, "Error", "❌ Please select a valid Data Folder.")
            Logger.warning("User cancelled Data Folder selection or chose invalid folder.")
            return

        Logger.success(f"Data Folder selected by user: {folder}")

        # ---------------------------
        # TASK for background thread
        # ---------------------------
        def task(folder):
            Logger.debug(f"Background task started for Data Folder: {folder}")
            try:
                if not os.path.isdir(folder):
                    Logger.error(f"Folder does not exist: {folder}")
                    raise FileNotFoundError(f"Folder does not exist: {folder}")

                results_dir = os.path.join(folder, "Agent Finder Results")
                os.makedirs(results_dir, exist_ok=True)
                Logger.success(f"'Agent Finder Results' directory ready at: {results_dir}")

                Logger.debug("Background task completed successfully.")
                return folder

            except Exception as e:
                Logger.error("Exception while validating Data Folder", e)
                raise

        # ---------------------------
        # CALLBACKS (main thread)
        # ---------------------------
        def on_done(folder):
            Logger.debug("on_done callback triggered for Data Folder.")
            try:
                self.ui.data_input.setText(folder)
                QMessageBox.information(self.ui, "Data Folder", f"✅ Data folder set:\n{folder}")
                Logger.success(f"Data Folder confirmed and set in UI: {folder}")
            except Exception as e:
                Logger.error("Error while updating UI with Data Folder", e)
                QMessageBox.critical(self.ui, "Error", f"❌ Failed to update UI.\nError: {str(e)}")

        def on_error(err):
            Logger.error(f"Error in Data Folder setup thread: {err}")
            QMessageBox.critical(
                self.ui, "Error",
                f"❌ Failed to select Data Folder.\nError: {str(err)}"
            )

        # ---------------------------
        # Run threaded
        # ---------------------------
        Logger.info("Starting Data Folder validation in background thread...")
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task, folder)


    def browse_report_folder(self):
        Logger.info("Opening Report Folder selection dialog...")  # Log start
        try:
            folder = QFileDialog.getExistingDirectory(self.ui, "Select Report Folder")
            Logger.debug(f"User selected folder: {folder}")  # Log raw user selection

            if not folder:
                QMessageBox.warning(self.ui, "Error", "❌ Please select a valid Report Folder.")
                Logger.warning("No folder selected. User must choose a valid Report Folder.")
                return

            # Define Background task
            def task(folder):
                Logger.info(f"Starting background task for folder: {folder}")
                if not os.path.isdir(folder):
                    Logger.error(f"Folder does not exist: {folder}")
                    raise FileNotFoundError(f"Folder does not exist: {folder}")

                # Ensure subfolder exists
                subfolder = os.path.join(folder, "AI Agent Reports")
                os.makedirs(subfolder, exist_ok=True)
                Logger.success(f"Verified folder and ensured subfolder exists: {subfolder}")

                return folder

            def on_done(result_folder):
                Logger.info(f"Background task completed. Folder ready: {result_folder}")
                self.ui.report_input.setText(result_folder)
                Logger.success(f"Report folder set successfully: {result_folder}")
                QMessageBox.information(
                    self.ui,
                    "Report Folder",
                    f"✅ Report folder set:\n{result_folder}"
                )

            def on_error(err):
                Logger.error(f"Background task failed with error: {err}")
                QMessageBox.critical(
                    self.ui,
                    "Error",
                    f"❌ Failed to select Report Folder.\nError: {str(err)}"
                )

            Logger.info("Initializing ThreadRunner for folder task...")
            self.runner = ThreadRunner(self.ui)
            self.runner.on_result = on_done
            self.runner.on_error = on_error
            self.runner.run(task, folder)
            Logger.info("ThreadRunner started for report folder task.")

        except Exception as e:
            Logger.error(f"Error while opening Report Folder dialog: {e}")
            QMessageBox.critical(
                self.ui,
                "Error",
                f"❌ Failed to open Report Folder dialog.\nError: {str(e)}"
            )


    def create_batch_subfolder(self, report_root):
        try:
            """Create a new timestamped batch folder"""
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_folder = os.path.join(report_root, ts)
            os.makedirs(batch_folder, exist_ok=True)
            Logger.info(f"Created batch folder: {batch_folder}")
            if not batch_folder:
                QMessageBox.critical(self.ui, "Error", "❌ Failed to create batch folder.")
                Logger.error("Failed to create batch folder")
            return batch_folder

        except Exception as e:  
            Logger.error(f"Error while creating batch folder: {e}")            
            QMessageBox.critical(self.ui, "Error", f"❌ Failed to create batch folder.\nError: {str(e)}")
    
    def browse_expert_file(self):
        try:
            expert_folder = os.path.join(self.ui.data_input.text(), "MQL5", "Experts")

            if not os.path.exists(expert_folder):
                QMessageBox.warning(self.ui, "Error", f"Expert folder not found:\n{expert_folder}")
                Logger.warning(f"Expert folder not found: {expert_folder}")
                return None

            # Step 1: Open dialog in main thread
            file_path, _ = QFileDialog.getOpenFileName(
                self.ui,
                "Select Expert File",
                expert_folder,
                "Expert Files (*.ex5 *.mq5);;All Files (*)"
            )

            if not file_path:
                QMessageBox.warning(self.ui, "Error", "❌ Please select a valid Expert File.")
                Logger.warning("Please select a valid Expert File.")
                return None


            def task(file_path):
                file_name = os.path.basename(file_path)
                return {"file_path": file_path, "file_name": file_name}

            
            def on_done(result):
                # file_path = result["file_path"]
                file_name = result["file_name"]

                # Clean placeholder
                if (
                    self.ui.expert_input.count() == 1
                    and self.ui.expert_input.itemText(0) == "Please Attach Data File"
                ):
                    self.ui.expert_input.clear()

                # Avoid duplicates
                if self.ui.expert_input.findText(file_name) == -1:
                    self.ui.expert_input.addItem(file_name)

                self.ui.expert_input.setCurrentText(file_name)
                Logger.success(f"Expert file selected: {file_name}")

         
            def on_error(err):
                Logger.error(f"Error while selecting Expert File: {err}")
                QMessageBox.critical(
                    self.ui,
                    "Error",
                    f"❌ Failed to select Expert File.\nError: {str(err)}"
                )

            # -----------------------
            # Step 5: Run threaded
            # -----------------------
            self.runner = ThreadRunner(self.ui)
            self.runner.on_result = on_done
            self.runner.on_error = on_error
            self.runner.run(task, file_path)

        except Exception as e:
            Logger.error(f"Error while selecting Expert File: {e}")
            QMessageBox.critical(
                self.ui, "Error",
                f"❌ Failed to select Expert File.\nError: {str(e)}"
            )

    def browse_param_file(self):
        data_folder = self.ui.data_input.text()

        if not data_folder:
            QMessageBox.warning(self.ui, "Error", "Please set the Data Folder first.")
            Logger.warning("Data folder is not set.")
            return None

   
   
        def task(data_folder):
            paths_to_check = [
                os.path.join(data_folder, "MQL5", "Profiles", "Tester"), # fallback
            ]

            for path in paths_to_check:
                if os.path.exists(path):
                 return path

            return None

    
        def on_done(default_path):
            if not default_path:
                QMessageBox.warning(self.ui, "Error", "❌ No Param folder found in Data Folder.")
                Logger.warning("No Param folder found in Data Folder.")
                return

            Logger.info(f"Param folder found: {default_path}")

            # Open file dialog on main thread
            file_path, _ = QFileDialog.getOpenFileName(
                self.ui,
                "Select Param File",
                default_path,
                "Set Files (*.set);;All Files (*)"
            )
            
            if (file_path):
                self.ui.param_input.setText(os.path.basename(file_path))
                Logger.info(f"Param file selected: {file_path}")
            else:
                QMessageBox.warning(self.ui, "Error", "❌ Please select a valid Param File.")
                Logger.warning("Please select a valid Param File.")

        def on_error(err):
            Logger.error(f"Error while selecting Param File: {err}")
            QMessageBox.critical(
                self.ui, "Error",
                f"❌ Failed to select Param File.\nError: {str(err)}"
            )

        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task, data_folder)

    def test_settings(self):
        test_name = self.ui.testfile_input.text().strip()
        if not test_name:
            QMessageBox.warning(self.ui, "Error", "Please enter a test file name")

            Logger.warning("Test file name is not set")

            return None
        
        

        settings = {
            "test_name": test_name,

            "expert": self.ui.expert_input.currentText().strip(),
            "param_file": self.ui.param_input.text().strip(),
            "symbol_prefix": self.ui.symbol_prefix.text().strip(),
            "symbol_suffix": self.ui.symbol_suffix.text().strip(),
            "symbol": self.ui.symbol_input.text().strip(),
            "timeframe": self.ui.timeframe_combo.currentText(),
            "date": self.ui.date_combo.currentText(),
            "date_from": self.ui.date_from.date().toString("yyyy-MM-dd"),
            "date_to": self.ui.date_to.date().toString("yyyy-MM-dd"),
            "forward": self.ui.forward_combo.currentText(),
            "forward_date": self.ui.forward_date.date().toString("yyyy-MM-dd"),
            "delay": self.ui.delay_input.value(),
            "delay_mode": self.ui.delay_combo.currentText(),
            "model": self.ui.model_combo.currentText(),
            "deposit": self.ui.deposit_input.text(),
            "currency": self.ui.currency_input.text().strip(),
            "leverage": self.ui.leverage_input.text().strip(),
            "optimization": self.ui.optim_combo.currentText(),
            "criterion": self.ui.criterion_input.currentText(),
        }

        return settings
    
    def add_test_to_queue(self):
        Logger.info("Starting process to add test to queue...")

        settings = self.test_settings()
        if not settings:
            Logger.warning("No test settings found. Aborting add_test_to_queue.")
            return
        Logger.debug(f"Test settings retrieved: {settings}")

        def task():
            Logger.info(f"Running background task to queue test: {settings['test_name']}")
            try:
                # The long/slow part of work
                self.queue.add_test_to_queue(settings)
                Logger.success(f"Test '{settings['test_name']}' successfully queued in background task.")
                return settings["test_name"]
            except Exception as e:
                Logger.error(f"Error while adding test '{settings['test_name']}' to queue: {e}")
                raise

        def on_done(test_name):
            Logger.info(f"Background task completed. Test ready: {test_name}")
            QMessageBox.information(self.ui, "Success", f"✅ Test {test_name} added to queue")
            Logger.success(f"Test '{test_name}' added to queue successfully.")

        def on_error(err):
            Logger.error(f"Failed to add test to queue. Error: {err}")
            QMessageBox.critical(
                self.ui,
                "Error",
                f"❌ Failed to add test to queue.\nError: {str(err)}"
            )

        Logger.info("Initializing ThreadRunner for add_test_to_queue task...")
        self.runner = ThreadRunner(self.ui)   # make sure you initialized in __init__
        self.runner.on_result = on_done       # hook result handler
        self.runner.on_error = on_error       # hook error handler
        self.runner.run(task)
        Logger.info("ThreadRunner started for add_test_to_queue task.")

    def get_best_symbol(self, user_input: str) -> str:
        Logger.info("Starting symbol lookup...")
        Logger.debug(f"Raw user input: '{user_input}'")

        try:
            symbols = self.mt5.symbol_list
            Logger.debug(f"Available symbols count: {len(symbols)}")

            user_input = user_input.upper().strip()
            Logger.debug(f"Normalized user input: '{user_input}'")

            # Exact match
            if user_input in symbols:
                Logger.success(f"Exact match found: {user_input}")
                return user_input

            # Closest match using difflib
            match = difflib.get_close_matches(user_input, symbols, n=1, cutoff=0.4)
            if match:
                Logger.info(f"Closest match found: {match[0]} for input '{user_input}'")
                return match[0]
            else:
                Logger.warning(f"No match found for input '{user_input}'. Returning empty string.")
                return ""

        except Exception as e:
            Logger.error(f"Error during symbol lookup for input '{user_input}': {e}")
            return ""

    def update_clean_symbol(self):
        Logger.info("Starting update_clean_symbol...")

        try:
            raw = self.ui.testfile_input.text().strip()
            Logger.debug(f"Raw symbol from input: '{raw}'")

            best = self.get_best_symbol(raw)
            Logger.debug(f"get_best_symbol returned: '{best}'")

            if best:
                self.ui.symbol_input.setText(best)
                Logger.success(f"UI updated with best symbol: {best}")
            else:
                Logger.warning(f"No valid symbol found for input: '{raw}'")

        except Exception as e:
            Logger.error(f"Error in update_clean_symbol: {e}")

    def update_expert_list(self):
        Logger.info("Starting update_expert_list...")

        try:
            data_folder = self.ui.data_input.text().strip()
            Logger.debug(f"Data folder: '{data_folder}'")

            expert_folder = os.path.join(data_folder, "MQL5", "Experts")
            Logger.debug(f"Looking for Experts in: '{expert_folder}'")

            if not os.path.exists(expert_folder):
                Logger.warning(f"Expert folder not found: {expert_folder}")
                return

            # Find all .ex5 files in Experts and subfolders
            expert_files = glob.glob(os.path.join(expert_folder, "**", "*.ex5"), recursive=True)
            Logger.info(f"Found {len(expert_files)} expert file(s).")

            # Store filename → {path, modified date}
            self.ui.experts = {
                os.path.basename(f): {
                    "path": f,
                    "modified": datetime.datetime.fromtimestamp(os.path.getmtime(f))
                }
                for f in expert_files
            }

            # Just show filenames in combo box
            expert_names = list(self.ui.experts.keys())
            Logger.debug(f"Expert names: {expert_names}")

            # Update the combo box
            if hasattr(self.ui, "expert_input") and isinstance(self.ui.expert_input, QComboBox):
                current_expert = self.ui.expert_input.currentText()
                Logger.debug(f"Current expert selection: '{current_expert}'")

                self.ui.expert_input.clear()
                self.ui.expert_input.addItems(expert_names)

                # Try to restore previous selection if still available
                if current_expert in expert_names:
                    index = self.ui.expert_input.findText(current_expert)
                    self.ui.expert_input.setCurrentIndex(index)
                    Logger.success(f"Restored previous expert selection: {current_expert}")
                else:
                    Logger.info("Previous expert selection not found in updated list.")

            Logger.success("Expert list updated successfully.")

        except Exception as e:
            Logger.error(f"Error while updating expert list: {e}")


    def refresh_expert(self):
        Logger.info("Refreshing expert selection...")

        try:
            if not hasattr(self.ui, "expert_input") or not self.ui.experts:
                Logger.warning("No expert_input widget or no experts available.")
                return

            current_text = self.ui.expert_input.currentText()
            if not current_text:
                Logger.warning("No current expert selected in combo box.")
                return

            Logger.debug(f"Current expert text: '{current_text}'")

            # Remove extension for matching base names
            base_name, _ = os.path.splitext(current_text)

            # Regex for versions like 1, 2.1, 3.2.5 etc.
            version_pattern = re.compile(r'[_ -]?(\d+(?:\.\d+)*)$')

            def parse_version(v):
                """Convert version string like '2.1.5' -> tuple (2,1,5)."""
                return tuple(map(int, v.split('.')))

            # --- Step 1: Detect prefix and versions ---
            match = version_pattern.search(base_name)
            if match:
                prefix = base_name[:match.start()].strip(" _-")
            else:
                prefix = base_name.strip(" _-")

            Logger.debug(f"Detected expert prefix: '{prefix}'")

            versions = []
            plain_matches = []

            for name, info in self.ui.experts.items():
                name_base, _ = os.path.splitext(name)
                m = version_pattern.search(name_base)
                if m and name_base[:m.start()].strip(" _-") == prefix:
                    try:
                        version_val = parse_version(m.group(1))
                        versions.append((version_val, name))
                        Logger.debug(f"Versioned match found: {name} (version={version_val})")
                    except Exception as e:
                        Logger.error(f"Failed to parse version in '{name}': {e}")
                elif name_base.strip(" _-") == prefix:
                    plain_matches.append((info["modified"], name))
                    Logger.debug(f"Plain match found: {name}")

            # --- Step 2: Pick best ---
            if versions:
                latest_name = max(versions, key=lambda x: x[0])[1]
                Logger.success(f"Selected highest version expert: {latest_name}")
            elif plain_matches:
                latest_name = max(plain_matches, key=lambda x: x[0])[1]
                Logger.success(f"Selected most recently modified expert: {latest_name}")
            else:
                Logger.warning("No matching experts found for prefix.")
                return

            # --- Step 3: Update UI ---
            index = self.ui.expert_input.findText(latest_name)
            if index != -1:
                self.ui.expert_input.setCurrentIndex(index)
                Logger.info(f"Expert combo box updated to: {latest_name}")
            else:
                Logger.warning(f"Latest expert '{latest_name}' not found in combo box.")

        except Exception as e:
            Logger.error(f"Unexpected error while refreshing expert: {e}")


    def load_experts(self, expert_folder):
        try:
            if not expert_folder or not isinstance(expert_folder, str):
                Logger.warning("Invalid expert folder path provided to load_experts")
                return None

            Logger.info(f"Loading experts from folder: {expert_folder}")

            def task(folder):
                try:
                    if not os.path.isdir(folder):
                        raise FileNotFoundError(f"Expert folder does not exist: {folder}")

                    expert_files = glob.glob(os.path.join(folder, "*.ex5"))
                    Logger.debug(f"Found {len(expert_files)} expert file(s) in {folder}")

                    experts_dict = {os.path.basename(f): f for f in expert_files}

                    # Pick latest by modification date
                    latest_file = None
                    if expert_files:
                        latest_file = max(expert_files, key=os.path.getmtime)
                        Logger.debug(f"Latest expert file detected: {latest_file}")
                    else:
                        Logger.warning("No expert .ex5 files found in the given folder")

                    return experts_dict, latest_file
                except Exception as e:
                    Logger.error(f"Error during expert file scan: {e}")
                    raise

            def on_done(result):
                try:
                    experts_dict, latest_file = result
                    self.ui.experts = experts_dict

                    if not experts_dict:
                        Logger.warning("No expert files loaded into UI")
                        return

                    latest_name = os.path.basename(latest_file) if latest_file else None
                    if latest_name:
                        self.ui.expert_input.setText(latest_name)
                        Logger.success(
                            f"Loaded {len(experts_dict)} expert(s). Latest = {latest_name}"
                        )
                    else:
                        Logger.info(f"Loaded {len(experts_dict)} expert(s), no latest file identified")
                except Exception as e:
                    Logger.error(f"Error in on_done while updating UI with experts: {e}")

            def on_error(err):
                Logger.error(f"Failed to load experts: {err}")

            # Run in background
            self.runner = ThreadRunner(self.ui)  # must exist in __init__
            self.runner.on_result = on_done
            self.runner.on_error = on_error
            self.runner.run(task, expert_folder)

        except Exception as e:
            Logger.error(f"Unexpected error in load_experts: {e}")

    
    # --- helper method ---
    def toggle_date_fields(self, text):
        try:
            today = QDate.currentDate()
            Logger.info(f"Date range option selected: {text}")

            if text == "Entire history":
                # Disable pickers, set from a very old date to today
                self.ui.date_from.setEnabled(False)
                self.ui.date_to.setEnabled(False)
                self.ui.date_from.setDate(QDate(1970, 1, 1))
                self.ui.date_to.setDate(today)
                Logger.success(f"Date range set: 1970-01-01 → {today.toString()}")

            elif text == "Last month":
                date_from = today.addMonths(-1)
                self.ui.date_from.setDate(date_from)
                self.ui.date_to.setDate(today)
                Logger.success(f"Date range set: {date_from.toString()} → {today.toString()}")

            elif text == "Last 3 months":
                self.ui.date_from.setEnabled(False)
                self.ui.date_to.setEnabled(False)
                date_from = today.addMonths(-3)
                self.ui.date_from.setDate(date_from)
                self.ui.date_to.setDate(today)
                Logger.success(f"Date range set: {date_from.toString()} → {today.toString()}")

            elif text == "Last 6 months":
                self.ui.date_from.setEnabled(False)
                self.ui.date_to.setEnabled(False)
                date_from = today.addMonths(-6)
                self.ui.date_from.setDate(date_from)
                self.ui.date_to.setDate(today)
                Logger.success(f"Date range set: {date_from.toString()} → {today.toString()}")

            elif text == "Last year":
                # Disable pickers, set range to last year
                self.ui.date_from.setEnabled(False)
                self.ui.date_to.setEnabled(False)
                date_from = today.addYears(-1)
                self.ui.date_from.setDate(date_from)
                self.ui.date_to.setDate(today)
                Logger.success(f"Date range set: {date_from.toString()} → {today.toString()}")

            elif text == "Custom period":
                # Enable pickers, let user choose
                self.ui.date_from.setEnabled(True)
                self.ui.date_to.setEnabled(True)
                self.ui.date_from.setDate(today)
                self.ui.date_to.setDate(today)
                Logger.info("Custom period enabled, defaulting both pickers to today.")

            else:
                Logger.warning(f"Unknown date range option: {text}")

        except Exception as e:
            Logger.error(f"Error in toggle_date_fields with option '{text}': {e}")


    # def adjust_forward_date(self, text):
    #     """Adjust forward_date depending on combo selection."""
    #     today = QDate.currentDate()
    #     Logger.info(f"Adjusting forward date: option selected = {text}")

    #     if text == "No":
    #         self.ui.forward_date.setEnabled(False)
    #         self.ui.forward_date.setDate(today)
    #         Logger.debug("Forward date disabled, set to today")

    #     elif text == "1/4":
    #         self.ui.forward_date.setEnabled(False)
    #         new_date = today.addMonths(3)
    #         self.ui.forward_date.setDate(new_date)
    #         Logger.debug(f"Forward date set to {new_date.toString('yyyy-MM-dd')} (1/4 year)")

    #     elif text == "1/3":
    #         self.ui.forward_date.setEnabled(False)
    #         new_date = today.addMonths(4)
    #         self.ui.forward_date.setDate(new_date)
    #         Logger.debug(f"Forward date set to {new_date.toString('yyyy-MM-dd')} (1/3 year)")

    #     elif text == "1/2":
    #         self.ui.forward_date.setEnabled(False)
    #         new_date = today.addMonths(6)
    #         self.ui.forward_date.setDate(new_date)
    #         Logger.debug(f"Forward date set to {new_date.toString('yyyy-MM-dd')} (1/2 year)")

    #     elif text == "Custom":
    #         self.ui.forward_date.setEnabled(True)  # let user pick manually
    #         Logger.info("Forward date enabled for custom selection")

    #     else:
    #         Logger.warning(f"Unknown forward date option: {text}")


    def adjust_forward_date(self, text):
        """Adjust forward_date based on selected testing period and forward fraction."""
        try:
            Logger.info(f"Adjusting forward date based on selection: {text}")

            # Get testing period
            date_from = self.ui.date_from.date()
            date_to = self.ui.date_to.date()

            # Calculate total testing duration in days
            total_days = date_from.daysTo(date_to)
            if total_days <= 0:
                Logger.warning("Invalid test period: date_from >= date_to")
                return

            # Handle forward options
            if text == "No":
                self.ui.forward_date.setEnabled(False)
                self.ui.forward_date.setDate(date_to)  # No forward, same as test end
                Logger.debug("Forward date disabled, set to test end date")

            elif text in ("1/4", "1/3", "1/2"):
                self.ui.forward_date.setEnabled(False)

                # Convert "1/3" -> 1/3 fraction
                fraction = eval(text)  # safe here since only predefined values are allowed

                # Forward starts after (1 - fraction) of period completed
                forward_start_offset = int(total_days * (1 - fraction))

                # New forward date = test period start + offset
                new_forward_date = date_from.addDays(forward_start_offset)
                self.ui.forward_date.setDate(new_forward_date)

                Logger.debug(
                    f"Forward date set to {new_forward_date.toString('yyyy-MM-dd')} "
                    f"({text} of test period from {date_from.toString()} → {date_to.toString()})"
                )

            elif text == "Custom":
                self.ui.forward_date.setEnabled(True)
                Logger.info("Forward date enabled for custom selection")

            else:
                Logger.warning(f"Unknown forward date option: {text}")

        except Exception as e:
            Logger.error(f"Error adjusting forward date for '{text}': {e}")

    def update_delay_input(self, text):
        Logger.info(f"Updating delay input: option selected = {text}")
        try:
            if text == "Custom Delay":
                self.ui.delay_input.setEnabled(True)
                Logger.debug("Custom Delay selected → delay input enabled for manual entry")

            elif text == "Random delay":
                value = random.randint(0, 1000)
                self.ui.delay_input.setValue(value)
                self.ui.delay_input.setEnabled(False)
                Logger.debug(f"Random Delay selected → set value = {value} ms, input disabled")

            elif "ms" in text:
                # Extract number from string like "50 ms"
                value = int(text.replace(" ms", "").strip())
                self.ui.delay_input.setValue(value)
                self.ui.delay_input.setEnabled(False)
                Logger.debug(f"Fixed delay selected → set value = {value} ms, input disabled")

            else:
                # For Zero latency, default, etc.
                self.ui.delay_input.setValue(0)
                self.ui.delay_input.setEnabled(False)
                Logger.debug("Unknown/Zero latency option → set value = 0 ms, input disabled")

            # Final confirmation log
            Logger.success(f"Delay input updated successfully (current value = {self.ui.delay_input.value()} ms)")

        except Exception as e:
            Logger.error(f"Error updating delay input: {str(e)}")


    def on_item_clicked(self, item):
        try:
            Logger.info(f"Item clicked: {item.text()}")
            row = self.queue.get_element_index(item.text())
            self.selected_queue_item_index = row
            Logger.success(f"Selected queue item → text='{item.text()}', index={row}")
        except Exception as e:
            Logger.error(f"Error handling item click: {str(e)}")


    def move_up(self):
        if self.selected_queue_item_index == -1:
            Logger.warning("Move up attempted with no item selected")
            QMessageBox.information(self.ui, "List Item Not Selected", "Please select a list item")
            return

        def task(index):
            Logger.info(f"Moving item at index {index} up")
            self.queue.move_up(index)
            return index - 1

        def on_done(index):
            Logger.success(f"Item moved up successfully → new index = {index}")
            self.selected_queue_item_index = index
            self.ui.queue_list.setCurrentRow(index)

        Logger.debug("Starting background task to move item up")
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.run(task, self.selected_queue_item_index)


    def move_down(self):
        if self.selected_queue_item_index == -1:
            Logger.warning("Move down attempted with no item selected")
            QMessageBox.information(self.ui, "List Item Not Selected", "Please select a list item")
            return

        def task(index):
            Logger.info(f"Moving item at index {index} down")
            self.queue.move_down(index)
            return index + 1

        def on_done(index):
            Logger.success(f"Item moved down successfully → new index = {index}")
            self.selected_queue_item_index = index
            self.ui.queue_list.setCurrentRow(index)

        Logger.debug("Starting background task to move item down")
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.run(task, self.selected_queue_item_index)


    def dup_down(self):
        if self.selected_queue_item_index == -1:
            Logger.warning("Duplicate attempted with no item selected")
            QMessageBox.information(self.ui, "List Item Not Selected", "Please select a list item")
            return

        def task(index):
            Logger.info(f"Duplicating item at index {index}")
            self.queue.duplicate_test(index)
            return index

        def on_done(index):
            Logger.success(f"Item duplicated successfully at index {index}")

        Logger.debug("Starting background task to duplicate item")
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.run(task, self.selected_queue_item_index)


    def delete_test(self):
        if self.selected_queue_item_index == -1:
            Logger.warning("Delete attempted with no item selected")
            QMessageBox.information(self.ui, "List Item Not Selected", "Please select a list item")
            return

        def task(index):
            Logger.info(f"Deleting item at index {index}")
            self.queue.delete_test(index)
            return index

        def on_done(index):
            Logger.success(f"Deleted item at index {index}")
            # Adjust selection index after deletion
            if index == len(self.queue):
                self.selected_queue_item_index = index - 1
                Logger.debug(f"Adjusted selected_queue_item_index to {self.selected_queue_item_index}")
            else:
                self.selected_queue_item_index = index
                Logger.debug(f"Kept selected_queue_item_index at {self.selected_queue_item_index}")

        Logger.debug("Starting background task to delete item")
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.run(task, self.selected_queue_item_index)


    def fetch_correlation(self, market="forex", period=50, symbols=None,
                      output_format="csv", endpoint="snapshot"):
        """Blocking: returns a dataframe"""

        try:
            if not symbols:
                symbols = ["EURUSD", "EURGBP", "AUDNZD"]  # fallback
                Logger.warning("No symbols provided, using fallback symbols: EURUSD, EURGBP, AUDNZD")

            symbol_str = "|".join(symbols)
            Logger.debug(f"Fetching correlation with params → market={market}, period={period}, "
                        f"symbols={symbol_str}, format={output_format}, endpoint={endpoint}")

            url = (
                f"https://www.mataf.io/api/tools/{output_format}/correl/"
                f"{endpoint}/{market}/{period}/correlation.{output_format}?symbol={symbol_str}"
            )
            Logger.info(f"Requesting correlation data from URL: {url}")

            response = requests.get(url, timeout=30)
            response.raise_for_status()
            Logger.success("Successfully fetched correlation data from API")

            lines = response.text.splitlines()
            Logger.debug(f"Received {len(lines)} lines of response data")

            # Skip first 3 metadata lines
            csv_data = "\n".join(lines[3:])
            df = pd.read_csv(StringIO(csv_data))
            Logger.info(f"Parsed CSV into DataFrame with {len(df)} rows")

            # Filter symbols
            before_count = len(df)
            df = df[df['pair1'].isin(symbols) & df['pair2'].isin(symbols)]
            after_count = len(df)
            Logger.debug(f"Filtered DataFrame from {before_count} → {after_count} rows (symbol filtering)")

            Logger.success("Correlation DataFrame prepared successfully")
            return df

        except requests.exceptions.RequestException as e:
            Logger.error(f"Network error while fetching correlation data: {e}")
            raise
        except Exception as e:
            Logger.error(f"Unexpected error in fetch_correlation: {e}")
            raise

 
    def get_correlation(self, market="forex", period=50, symbols=None,
                    output_format="csv", endpoint="snapshot",
                    on_done=None, on_error=None):
        try:
            # Collect unique symbols from queue
            symbols = []
            for test in self.queue.tests: 
                if test["symbol"] not in symbols:
                    symbols.append(test["symbol"])

            Logger.info(f"Preparing to fetch correlation for symbols: {symbols} "
                        f"(market={market}, period={period}, format={output_format}, endpoint={endpoint})")

            def task():
                Logger.debug("Starting background correlation fetch task")
                df = self.fetch_correlation(market, period, symbols, output_format, endpoint)
                Logger.debug(f"Background task finished, DataFrame shape={df.shape}")
                return df

            def _on_done(df):
                Logger.success(f"Correlation data received with {len(df)} rows")
                if on_done:
                    Logger.debug("Delegating correlation result to custom on_done handler")
                    on_done(df)
                else:
                    Logger.debug("No custom on_done handler, generating default heatmap")
                    try:
                        corr_df = df.pivot(index="pair1", columns="pair2", values="day")
                        Logger.info(f"Pivoted correlation DataFrame to shape {corr_df.shape}")

                        def show_plot():
                            Logger.debug("Rendering correlation heatmap")
                            plt.figure(figsize=(6, 4))
                            sns.heatmap(
                                corr_df,
                                annot=True,
                                fmt=".0f",
                                cmap="RdBu",
                                center=0,
                                vmin=-100,
                                vmax=100,
                                linewidths=0.5
                            )
                            plt.title("Correlation Heatmap (Day)")
                            plt.tight_layout()
                            plt.show()
                            Logger.success("Correlation heatmap generated successfully")

                        QTimer.singleShot(0, show_plot)

                    except Exception as e:
                        Logger.error(f"Error generating correlation heatmap: {e}")
                        QMessageBox.critical(self.ui, "Error", str(e))

            def _on_error(err):
                Logger.error(f"Correlation fetch failed: {err}")
                if on_error:
                    Logger.debug("Delegating error to custom on_error handler")
                    on_error(err)
                else:
                    QMessageBox.critical(self.ui, "Error", str(err))

            Logger.debug("Starting correlation fetch in background thread")
            self.runner = ThreadRunner(self.ui)
            self.runner.on_result = _on_done
            self.runner.on_error = _on_error
            self.runner.run(task)

        except Exception as e:
            Logger.error(f"Unexpected error in get_correlation: {e}")
            QMessageBox.critical(self.ui, "Error", str(e))

      
    def show_quantity_popup(self, title, text):
        Logger.info(f"Opening quantity popup: {title} - {text}")

        results = {
            "test_symbol_quantity": None,
            "strategies_count": None,
            "strategies": [],
            "symbol_type": None,
            "correlationFilter": None
        }

        # ---------------------------
        #  Step 1: Collect user input (MAIN THREAD)
        # ---------------------------

        # First dialog
        dialog1 = QuantityDialog(parent=self.ui, title=title, text=text)
        if dialog1.exec_() != QDialog.Accepted:
            Logger.warning("Quantity dialog cancelled by user.")
            return
        results["test_symbol_quantity"] = dialog1.get_value()
        Logger.info(f"Test symbol quantity set to: {results['test_symbol_quantity']}")

        # Second dialog
        dialog2 = QuantityDialog(parent=self.ui, title="Strategies Count", text="How many strategies are you running")
        if dialog2.exec_() != QDialog.Accepted:
            Logger.warning("Strategies count dialog cancelled by user.")
            return
        results["strategies_count"] = dialog2.get_value()
        Logger.info(f"Strategies count set to: {results['strategies_count']}")

        # Strategy names
        for i in range(results["strategies_count"]):
            dialog3 = TextDialog(parent=self.ui, title=f"Strategy {i+1} Name", text=f"Please Name Strategy {i+1}")
            if dialog3.exec_() != QDialog.Accepted:
                Logger.warning(f"Strategy {i+1} name dialog cancelled by user.")
                return
            strategy_name = dialog3.get_value()
            results["strategies"].append(strategy_name)
            Logger.info(f"Strategy {i+1} set to: {strategy_name}")

        # Symbol type radio dialog
        options = ["FX Only", "FX + Metals", "FX + Indices", "FX + Metal + Indices"]
        radio_dialog = RadioDialog(
            parent=self.ui,
            title="Symbols to Test",
            text="Which symbol do you want to include:",
            options=options
        )
        if radio_dialog.exec_() != QDialog.Accepted:
            Logger.warning("Symbol type dialog cancelled by user.")
            return
        results["symbol_type"] = radio_dialog.get_value()
        Logger.info(f"Symbol type selected: {results['symbol_type']}")

        # Correlation filter dialog
        correlationFilterDialog = QuantityDialog(
            parent=self.ui,
            title="Correlation Filter",
            text="""Enter a value between 0-100 to filter out highly correlated pairs.
                    1) If the correlation is high (above 80) and positive then the currencies move in the same way.
                    2) If the correlation is high (above 80) and negative then the currencies move in the opposite way.
                    3) If the correlation is low (below 60) then the currencies don't move in the same way.""",
            default_value=60
        )
        if correlationFilterDialog.exec_() != QDialog.Accepted:
            Logger.warning("Correlation filter dialog cancelled by user.")
            return
        results["correlationFilter"] = correlationFilterDialog.get_value()
        Logger.info(f"Correlation filter set to: {results['correlationFilter']}")

        self.non_correlated_popus_option = results
        Logger.debug(f"Collected popup results: {results}")

        # Read all UI values before threading
        ui_values = {
            "expert": self.ui.expert_input.currentText().strip(),
            "param_file": self.ui.param_input.text().strip(),
            "symbol_prefix": self.ui.symbol_prefix.text().strip(),
            "symbol_suffix": self.ui.symbol_suffix.text().strip(),
            "symbol": self.ui.symbol_input.text().strip(),
            "timeframe": self.ui.timeframe_combo.currentText(),
            "date": self.ui.date_combo.currentText(),
            "date_from": self.ui.date_from.date().toString("yyyy-MM-dd"),
            "date_to": self.ui.date_to.date().toString("yyyy-MM-dd"),
            "forward": self.ui.forward_combo.currentText(),
            "forward_date": self.ui.forward_date.date().toString("yyyy-MM-dd"),
            "delay_mode": self.ui.delay_combo.currentText(),
            "delay": self.ui.delay_input.value(),
            "model": self.ui.model_combo.currentText(),
            "deposit": self.ui.deposit_input.text(),
            "currency": self.ui.currency_input.text().strip(),
            "leverage": self.ui.leverage_input.text().strip(),
            "optimization": self.ui.optim_combo.currentText(),
            "criterion": self.ui.criterion_input.currentText(),
        }
        Logger.debug(f"Collected UI values: {ui_values}")

        # Precompute symbols on main thread (fast)
        symbols = self.get_symbols_for_option(results["symbol_type"])
        Logger.info(f"Symbols resolved for type '{results['symbol_type']}': {symbols}")

        # --------------------------------
        # Step 2: Background work (THREAD)
        # --------------------------------
        def task(symbols, results, ui_values):
            Logger.debug("Starting background task: fetching correlation data")
            df = self.fetch_correlation(
                market="forex",
                period=50,
                symbols=symbols,
                output_format="csv",
                endpoint="snapshot",
            )
            Logger.success(f"Correlation data fetched, DataFrame shape={df.shape}")

            # compute uncorrelated pairs
            uncorrelated_pairs = self.get_top_uncorrelated_pairs_day(
                df,
                correlation=results["correlationFilter"],
                top_n=results["test_symbol_quantity"],
            )
            Logger.info(f"Uncorrelated pairs found: {len(uncorrelated_pairs)}")

            if uncorrelated_pairs.empty:
                Logger.warning("No uncorrelated pairs found.")
                return {"pairs": [], "settings": []}

            # build settings
            settings_list = []
            for _, row in uncorrelated_pairs.iterrows():
                uncorrelated_pair = f"{row['pair1']}"
                for strategy in results["strategies"]:
                    settings = {
                        "test_name": f"{uncorrelated_pair}_{strategy}",
                        **ui_values,
                        "symbol": uncorrelated_pair,
                    }
                    settings_list.append(settings)
                    Logger.debug(f"Generated test settings: {settings['test_name']}")

            return {
                "pairs": uncorrelated_pairs[["pair1", "pair2", "day"]].to_dict("records"),
                "settings": settings_list,
            }

        def on_done(payload):
            pairs = payload.get("pairs", [])
            settings_list = payload.get("settings", [])

            if not pairs:
                QMessageBox.warning(
                    self.ui,
                    "No Pairs Found",
                    f"No uncorrelated pairs found with correlation ≤ {results['correlationFilter']}."
                )
                Logger.warning(f"No uncorrelated pairs found with correlation ≤ {results['correlationFilter']}.")
                return

            for settings in settings_list:
                self.queue.add_test_to_queue(settings)
                Logger.success(f"Test '{settings['test_name']}' added to queue.")

            QMessageBox.information(self.ui, "Added", f"{len(settings_list)} Test cases added to queue.")
            Logger.info(f"Added {len(settings_list)} test cases to queue successfully.")

        def on_error(err):
            Logger.error(f"Failed to process correlation data: {err}")
            QMessageBox.critical(self.ui, "Error", f"Failed to process correlation data:\n{err}")

        # run threaded
        Logger.debug("Launching threaded task for correlation and uncorrelated pair processing")
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task, symbols, results, ui_values)



    def get_symbols_for_option(self, option):
        Logger.info(f"Fetching symbols for option: {option}")

        if option == "FX Only":
            symbols = self.mt5.get_fx_symbols()
            Logger.success(f"Retrieved {len(symbols)} FX symbols")
            return symbols
        elif option == "FX + Metals":
            symbols = self.mt5.get_fx_symbols() + self.mt5.get_metals_symbols()
            Logger.success(f"Retrieved {len(symbols)} FX + Metals symbols")
            return symbols
        elif option == "FX + Indices":
            symbols = self.mt5.get_fx_symbols() + self.mt5.get_indices_symbols()
            Logger.success(f"Retrieved {len(symbols)} FX + Indices symbols")
            return symbols
        elif option == "FX + Metal + Indices":
            symbols = (
                self.mt5.get_fx_symbols()
                + self.mt5.get_metals_symbols()
                + self.mt5.get_indices_symbols()
            )
            Logger.success(f"Retrieved {len(symbols)} FX + Metals + Indices symbols")
            return symbols
        else:
            Logger.warning(f"Unknown option '{option}' provided, defaulting to FX only")
            symbols = self.mt5.get_fx_symbols()
            Logger.success(f"Retrieved {len(symbols)} FX symbols (default fallback)")
            return symbols


    def get_top_uncorrelated_pairs_day(self, df, correlation=60, top_n=5):
        Logger.info(f"Finding top {top_n} uncorrelated pairs with correlation ≤ {correlation}")

        # df.to_csv("correlation_raw.csv", index=False)  # for debugging

        # Filter out identical pairs
        df_filtered = df[df["pair1"] != df["pair2"]].copy()
        Logger.debug(f"Filtered out identical pairs, remaining rows: {len(df_filtered)}")

        # Normalize pair order (so A,B and B,A become the same)
        df_filtered["pair_min"] = df_filtered[["pair1", "pair2"]].min(axis=1)
        df_filtered["pair_max"] = df_filtered[["pair1", "pair2"]].max(axis=1)

        # Drop duplicates after normalization
        df_filtered = df_filtered.drop_duplicates(subset=["pair_min", "pair_max"])

        # Add absolute correlation values
        df_filtered["abs_day"] = df_filtered["day"].abs()

        # Filter by correlation threshold
        df_filtered = df_filtered[df_filtered["abs_day"] <= correlation].sort_values("abs_day", ascending=True)
        Logger.debug(f"After applying correlation filter ≤ {correlation}, rows left: {len(df_filtered)}")


        corr_df = df_filtered.pivot(index="pair1", columns="pair2", values="day")
        # corr_df.to_csv("corr_df.csv", index=False)


        # Select top_n
        top_pairs = df_filtered[["pair_min", "pair_max", "day"]].head(top_n)
        top_pairs = top_pairs.rename(columns={"pair_min": "pair1", "pair_max": "pair2"})

        top_pairs.to_csv("correlation.csv", index=False)
        Logger.success(f"Top {len(top_pairs)} uncorrelated pairs selected")

        return top_pairs


    # def get_top_uncorrelated_pairs_day(self, df, correlation=60, top_n=5):
    #     """
    #     Return top N uncorrelated pairs based on 'day' correlation values.
    #     Keeps same columns as input (pair1, pair2, day) to avoid breaking controller.
    #     """
    #     Logger.info(f"Finding top {top_n} uncorrelated pairs with correlation ≤ {correlation}")

    #     try:
    #         df_filtered = df[df["pair1"] != df["pair2"]].copy()
    #         df_filtered["abs_day"] = df_filtered["day"].abs()

    #         # Filter for low correlation
    #         df_filtered = df_filtered[df_filtered["abs_day"] <= correlation]

    #         if df_filtered.empty:
    #             Logger.warning("No pairs found under the correlation threshold.")
    #             return pd.DataFrame(columns=["pair1", "pair2", "day"])

    #         # Sort ascending by correlation magnitude
    #         df_filtered = df_filtered.sort_values("abs_day", ascending=True)

    #         # Select top N pairs
    #         top_pairs = df_filtered.head(top_n)[["pair1", "pair2", "day"]].reset_index(drop=True)

    #         top_pairs.to_csv("uncorrelated_pairs.csv", index=False)
    #         Logger.success(f"Top {len(top_pairs)} uncorrelated pairs found: {top_pairs[['pair1','pair2']].values.tolist()}")

    #         return top_pairs

    #     except Exception as e:
    #         Logger.error(f"Error in get_top_uncorrelated_pairs_day: {e}")
    #         return pd.DataFrame(columns=["pair1", "pair2", "day"])



    def on_start_button_clicked(self, data_path, mt5_path, report_path):
        Logger.info(f"Start button clicked with paths: data='{data_path}', mt5='{mt5_path}', report='{report_path}'")

        if not hasattr(self, "queue") or self.queue.is_empty():
            QMessageBox.warning(self.ui, "No Tests", "No tests in the queue. Please add tests first.")
            Logger.warning("Start aborted: Queue is empty or not initialized.")
            return

        Logger.info("Starting queued tests...")

        def task():
            # Run tests one by one in the thread
            while not self.queue.is_empty():
                test_settings = self.queue.get_next_test()
                Logger.debug(f"Running test with settings: {test_settings}")
                try:
                    self.mt5.run_test(test_settings, data_path, mt5_path, report_path, self.ui.experts)
                    Logger.success(f"Test '{test_settings.get('test_name', 'Unnamed')}' completed successfully.")
                except Exception as e:
                    Logger.error(f"Error while running test '{test_settings.get('test_name', 'Unnamed')}': {str(e)}")
                self.queue.refresh_queue()
                Logger.debug("Queue refreshed after test execution.")
            return True  # signal finished

        def on_done(_):
            QMessageBox.information(self.ui, "Finished", "All tests completed.")
            Logger.success("All tests completed successfully.")

        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.run(task)


    def on_test_selected(self, index):
        Logger.info(f"Test selection triggered. Raw index={index}")

        index = self.ui.queue_list.currentRow()  # Which item was clicked
        Logger.debug(f"Current row selected in queue_list: {index}")

        if hasattr(self, "current_index") and self.current_index is not None:
            if 0 <= self.current_index < len(self.queue.tests):
                Logger.debug(f"Saving parameters of previously selected test at index {self.current_index}")
                self.update_current_test_parameters(self.current_index)

        if 0 <= index < len(self.queue.tests):
            self.current_index = index
            test_data = self.queue.tests[index]  # Get the selected test
            Logger.info(f"New test selected at index {index}: {test_data.get('test_name', 'Unnamed Test')}")
            self.load_test_parameters(test_data)  # Show it on the form
            Logger.debug(f"Test data loaded into UI: {test_data}")
        else:
            Logger.warning(f"Invalid test index selected: {index}")


    def load_test_parameters(self, test_data):
        Logger.info(f"Loading test parameters for: {test_data.get('test_name', 'Unnamed Test')}")

        try:
            # Expert & param files
            self.ui.testfile_input.setText(test_data.get("test_name", ""))
            Logger.debug(f"Set test_name: {test_data.get('test_name', '')}")

            self.ui.expert_input.setCurrentText(test_data.get("expert", ""))
            Logger.debug(f"Set expert: {test_data.get('expert', '')}")

            self.ui.param_input.setText(test_data.get("param_file", ""))
            Logger.debug(f"Set param_file: {test_data.get('param_file', '')}")

            self.ui.symbol_input.setText(str(test_data.get("symbol", "")))
            Logger.debug(f"Set symbol: {test_data.get('symbol', '')}")

            self.ui.timeframe_combo.setCurrentText(test_data.get("timeframe", ""))
            Logger.debug(f"Set timeframe: {test_data.get('timeframe', '')}")

            self.ui.symbol_prefix.setText(test_data.get("symbol_prefix", ""))
            self.ui.symbol_suffix.setText(test_data.get("symbol_suffix", ""))
            Logger.debug(f"Set symbol prefix/suffix: {test_data.get('symbol_prefix', '')}/{test_data.get('symbol_suffix', '')}")

            self.ui.date_combo.setCurrentText(test_data.get("date", ""))
            Logger.debug(f"Set date: {test_data.get('date', '')}")

            # Handle date_from
            date_from_str = test_data.get("date_from", "")
            date_from = QDate.fromString(date_from_str, "yyyy-MM-dd")
            if date_from.isValid():
                self.ui.date_from.setDate(date_from)
                Logger.debug(f"Set date_from: {date_from_str}")
            else:
                self.ui.date_from.setDate(QDate(2000, 1, 1))
                Logger.warning(f"Invalid date_from '{date_from_str}', set to default 2000-01-01")

            # Handle date_to
            date_to_str = test_data.get("date_to", "")
            date_to = QDate.fromString(date_to_str, "yyyy-MM-dd")
            if date_to.isValid():
                self.ui.date_to.setDate(date_to)
                Logger.debug(f"Set date_to: {date_to_str}")
            else:
                self.ui.date_to.setDate(QDate(2000, 1, 1))
                Logger.warning(f"Invalid date_to '{date_to_str}', set to default 2000-01-01")

            # Handle forward_date
            self.ui.forward_combo.setCurrentText(test_data.get("forward", ""))
            forward_str = test_data.get("forward_date", "")
            forward_date = QDate.fromString(forward_str, "yyyy-MM-dd")
            if forward_date.isValid():
                self.ui.forward_date.setDate(forward_date)
                Logger.debug(f"Set forward_date: {forward_str}")
            else:
                self.ui.forward_date.setDate(QDate(2000, 1, 1))
                Logger.warning(f"Invalid forward_date '{forward_str}', set to default 2000-01-01")

            self.ui.delay_combo.setCurrentText(test_data.get("delay_mode", ""))
            self.ui.delay_input.setValue(int(test_data.get("delay", 0)))
            Logger.debug(f"Set delay: {test_data.get('delay', 0)} mode: {test_data.get('delay_mode', '')}")

            self.ui.model_combo.setCurrentText(test_data.get("model", ""))
            self.ui.deposit_input.setText(str(test_data.get("deposit", "")))
            self.ui.currency_input.setText(test_data.get("currency", ""))
            self.ui.leverage_input.setValue(float(test_data.get("leverage", 0)))
            Logger.debug(f"Set model: {test_data.get('model', '')}, deposit: {test_data.get('deposit', '')}, "
                        f"currency: {test_data.get('currency', '')}, leverage: {test_data.get('leverage', 0)}")

            self.ui.optim_combo.setCurrentText(str(test_data.get("optimization", "")))
            self.ui.criterion_input.setCurrentText(str(test_data.get("criterion", "")))
            Logger.debug(f"Set optimization: {test_data.get('optimization', '')}, criterion: {test_data.get('criterion', '')}")

            Logger.success(f"Successfully loaded parameters for test '{test_data.get('test_name', 'Unnamed Test')}'")

        except Exception as e:
            Logger.error(f"Error loading test parameters: {str(e)}")

        
    def update_current_test_parameters(self, index):
        """Save the current form values into the test at given index."""
        try:
            Logger.info(f"Updating test parameters at index {index}...")

            self.queue.tests[index] = {
                "test_name": self.ui.testfile_input.text(),
                "expert": self.ui.expert_input.currentText(),
                "param_file": self.ui.param_input.text(),
                "symbol": self.ui.symbol_input.text(),
                "timeframe": self.ui.timeframe_combo.currentText(),
                "symbol_prefix": self.ui.symbol_prefix.text(),
                "symbol_suffix": self.ui.symbol_suffix.text(),
                "date": self.ui.date_combo.currentText(),
                "date_from": self.ui.date_from.date().toString("yyyy-MM-dd"),
                "date_to": self.ui.date_to.date().toString("yyyy-MM-dd"),
                "forward": self.ui.forward_combo.currentText(),
                "forward_date": self.ui.forward_date.date().toString("yyyy-MM-dd"),
                "delay_mode": self.ui.delay_combo.currentText(),
                "delay": self.ui.delay_input.value(),
                "model": self.ui.model_combo.currentText(),
                "deposit": self.ui.deposit_input.text(),
                "currency": self.ui.currency_input.text(),
                "leverage": self.ui.leverage_input.value(),
                "optimization": self.ui.optim_combo.currentText(),
                "criterion": self.ui.criterion_input.currentText(),
            }

            Logger.info(f"Test parameters updated successfully at index {index}: {self.queue.tests[index]}")

        except Exception as e:
            Logger.error(f"Error saving test parameters at index {index}: {str(e)}")





        
       



        # Do this for all the other parameter fields

    # def schedule_test(self):
    #     selected_date = self.ui.schedule_date.date().toPyDate()
        
    #     # Default time at 9:00 AM (you can change it)
    #     run_time = datetime.combine(selected_date, time(hour=0, minute=0))
    #     now = datetime.now()
        
    #     if run_time <= now:
    #         print("Selected date/time is in the past!")
    #         return
        
    #     # Schedule the job
    #     self.scheduler.add_job(self.my_function, 'date', run_date=run_time)
    #     print(f"Function scheduled for {run_time}")

    # def my_function(self):
    #     print("huzaifa")




    def copy_parameter(self, property: dict):
        """Copy given property to all tests in the queue."""
        try:
            Logger.info(f"Copying parameter to all tests: {property}")
            self.queue.update_all_tests(property)
            Logger.info("Parameter copied successfully to all tests.")
        except Exception as e:
            Logger.error(f"Error copying parameter {property}: {str(e)}")

