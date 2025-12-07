import psutil
import os,re,glob,datetime, shutil
import pandas as pd
import time
# from datetime import datetime
from aiagentfinder.utils import MT5Manager , Logger 
from aiagentfinder.utils.workerThread import ThreadRunner
from PyQt5.QtCore import Qt, QDate, QItemSelectionModel, QItemSelection
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QFileDialog, QTableWidgetSelectionRange, QTableWidget, QMessageBox,QComboBox,QApplication
from aiagentfinder.utils.ThreadRunnerV2 import ThreadRunnerV2

class SetProcessorController:
    def __init__(self,ui):
        self.ui = ui
        
        self.main_window = self.ui.parent()
        self.auto_batch_ui = self.main_window.autoBatch_page
        self.setfinder_ui = self.main_window.setFinder_page
        self.connected = False
        self.mt5 = MT5Manager()
        self.runner = ThreadRunner()
        self.runnerV2 = ThreadRunnerV2(self.main_window)
        self.logger = Logger()
        self.selected_reports = ["HTML Reports","Graph"]
   


        self.ui.browse_set_files.clicked.connect(self.browse_set_file)
        # self.ui.toggle_graph.stateChanged.connect(self.browse_set_file)
        # self.ui.toggle_csv.stateChanged.connect(self.browse_set_file)
        # self.ui.toggle_overview.stateChanged.connect(self.browse_set_file)
        # self.ui.toggle_semi_auto.stateChanged.connect(self.browse_set_file)

        self.ui.mt5_btn.clicked.connect(self.browse_mt5_dir)
        self.ui.refresh_btn.clicked.connect(self.refresh_expert)
        self.ui.expert_button.clicked.connect(self.browse_expert_file)
        self.ui.data_folder_input.textChanged.connect(self.update_expert_list)



        self.ui.date_combo.currentTextChanged.connect(self.toggle_date_fields)
        
        self.ui.copy_data_button.clicked.connect(self.copy_data_from_autotester)
        self.ui.copy_dates_button.clicked.connect(self.copy_dates_from_setfinder)

        self.ui.start_button.clicked.connect(self.on_start_button_clicked)

        self.ui.toggle_graph.stateChanged.connect(lambda state: self.update_selection("Graph", state))
        self.ui.toggle_overview.stateChanged.connect(lambda state: self.update_selection("Overview", state))
        self.ui.toggle_csv.stateChanged.connect(lambda state: self.update_selection("CSV", state))
        self.ui.toggle_semi_auto.stateChanged.connect(lambda state: self.update_selection("Semi-Auto", state))
        

        self.ui.stop_button.clicked.connect(self.on_stop_button_clicked)
        self.ui.resume_button.clicked.connect(self.on_resume_button_clicked)
        self.ui.kill_button.clicked.connect(self.on_kill_button_clicked)

        # self.ui.copy_data_button.clicked.connect(self.copy_data_from_autotester)

        # self.ui.resume_button.clicked.connect(self.resume_tests)
        # self.ui.schedule_toggle.stateChanged.connect(self.toggle_schedule)




    def browse_set_file(self):
        data_folder = self.ui.data_folder_input.text()

        if not data_folder:
            QMessageBox.warning(self.ui, "Error", "Please  set the Data Folder first.")
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

            # ✅ Open folder dialog (instead of file)
            folder_path = QFileDialog.getExistingDirectory(
                self.ui,
                "Select Set Folder",
                default_path
            )

            if folder_path:
                self.ui.input_set_files.setText(folder_path)
                Logger.info(f"Set folder selected: {folder_path}")
                set_files = [f for f in os.listdir(folder_path) if f.endswith(".set")]

                self.ui.set_table.setRowCount(len(set_files))
                for row, file in enumerate(set_files):
                    self.ui.set_table.setItem(row, 0, QTableWidgetItem(file))
                    self.ui.set_table.setItem(row, 1, QTableWidgetItem("WAITING"))
                    self.ui.set_table.setItem(row, 2, QTableWidgetItem("WAITING"))
                    self.ui.set_table.setItem(row, 3, QTableWidgetItem("WAITING"))
                    self.ui.set_table.setItem(row, 4, QTableWidgetItem("WAITING"))

                self.ui.status_label.setText(f"Successfully Detected {len(set_files)} Set Files")
                Logger.success(f"Detected {len(set_files)} set files in {folder_path}")
            else:
                QMessageBox.warning(self.ui, "Error", "❌ Please select a valid Set Folder.")
                Logger.warning("Please select a valid Set Folder.")
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


    def browse_mt5_dir(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.ui, "Select MT5 Terminal", "", "Executable Files (*.exe)"
        )
        if not file_path:
            return

        self.ui.mt5_input.setText(file_path)
        Logger.info(f"MT5 terminal selected: {file_path}")

        def task(file_path):
            result = {
                "file_path": file_path,
                "data_folder": None,
                "deposit_info": None,
                "error": None,
            }
            try:
                success = self.mt5.connect(file_path)
                if success:
                    dataPath = self.mt5.get_dataPath()
                    if dataPath:
                        result["data_folder"] = dataPath
                        os.makedirs(os.path.join(dataPath, "Agent Finder Results"), exist_ok=True)

                    result["deposit_info"] = self.mt5.get_deposit()

                    # Copy symbol list safely (avoid UI logging here)
                    _ = self.mt5.get_symbol_list()

                    self.mt5.disconnect()
                else:
                    result["error"] = f"Failed to connect: {self.mt5.last_error()}"

            except Exception as e:
                result["error"] = str(e)

            return result


        def on_done(result):
            if result.get("error"):
                QMessageBox.critical(self.ui, "MT5 Connection", f"❌ {result['error']}")
                return

            if result["data_folder"]:
                self.ui.data_folder_input.setText(result["data_folder"])
                Logger.info(f"Auto-selected Data Folder: {result['data_folder']}")

            if result["deposit_info"]:
                info = result["deposit_info"]
                self.ui.deposit_info = info
                self.ui.deposit_input.setText(str(info.get("balance", 0)))
                self.ui.currency_input.setText(info.get("currency", ""))
                self.ui.leverage_input.setValue(info.get("leverage", 0))
                QMessageBox.information(self.ui, "MT5 Connection", "✅ MT5 connected successfully!")
            else:
                QMessageBox.warning(self.ui, "MT5 Connection", "⚠️ No deposit info retrieved")

            # Optional: safely close MT5 here if you really want
            exe_name = os.path.basename(result["file_path"])
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == exe_name:
                    try:
                        proc.terminate()
                        print(f"Closed MT5 window: {exe_name}")
                    except Exception as e:
                        Logger.error(f"Could not close MT5 window: {e}")
        self.connected = True
                
        def on_error(err):
            QMessageBox.critical(
                self.ui, "Error",
                f"❌ Failed during MT5 setup.\nError: {str(err)}"
            )
            Logger.error(str(err))

        # ---------------------------
        # Run threaded
        # ---------------------------
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
                self.ui.data_folder_input.setText(folder)
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

    def browse_expert_file(self):
        try:
            expert_folder = os.path.join(self.ui.data_folder_input.text(), "MQL5", "Experts")

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
    
    def update_clean_symbol(self):
        raw = self.ui.testfile_input.text().strip()
        print("raw = ", raw)
        best = self.get_best_symbol(raw)
        if best:
            Logger.info(f"Best symbol found: {best}")
            self.ui.symbol_input.setText(best)

    def update_expert_list(self):
        data_folder = self.ui.data_folder_input.text()
        expert_folder = os.path.join(data_folder, "MQL5", "Experts")

        if not os.path.exists(expert_folder):
            return

        # Find all .ex5 files in Experts and subfolders
        expert_files = glob.glob(os.path.join(expert_folder, "**", "*.ex5"), recursive=True)

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

        print("expert_names = ", expert_names)

        # Update the combo box
        if hasattr(self.ui, "expert_input") and isinstance(self.ui.expert_input, QComboBox):
            current_expert = self.ui.expert_input.currentText()
            self.ui.expert_input.clear()
            self.ui.expert_input.addItems(expert_names)
            # Try to restore previous selection if still available
            if current_expert in expert_names:
                index = self.ui.expert_input.findText(current_expert)
                self.ui.expert_input.setCurrentIndex(index)

    def refresh_expert(self):
        if not hasattr(self.ui, "expert_input") or not self.ui.experts:
            return

        current_text = self.ui.expert_input.currentText()
        if not current_text:
            return

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

        versions = []
        plain_matches = []

        for name, info in self.ui.experts.items():
            name_base, _ = os.path.splitext(name)
            m = version_pattern.search(name_base)
            if m and name_base[:m.start()].strip(" _-") == prefix:
                # Found versioned match
                try:
                    version_val = parse_version(m.group(1))
                except Exception:
                    version_val = ()
                versions.append((version_val, name))
            elif name_base.strip(" _-") == prefix:
                # Non-versioned base expert
                plain_matches.append((info["modified"], name))

        # --- Step 2: Pick best ---
        if versions:
            # Case A: Use highest version
            latest_name = max(versions, key=lambda x: x[0])[1]
        elif plain_matches:
            # Case B: No versions → pick latest modified
            latest_name = max(plain_matches, key=lambda x: x[0])[1]
        else:
            return  # No match found

        # --- Step 3: Update UI ---
        index = self.ui.expert_input.findText(latest_name)
        if index != -1:
            self.ui.expert_input.setCurrentIndex(index)
    
    def load_experts(self, expert_folder):
        if not expert_folder or not isinstance(expert_folder, str):
            Logger.warning("Invalid expert folder path")
            return None

        def task(folder):
      
            expert_files = glob.glob(os.path.join(folder, "*.ex5"))
            experts_dict = {os.path.basename(f): f for f in expert_files}

            # Return both dict + latest file (if any)
            latest_file = None
            if expert_files:
                latest_file = max(expert_files, key=os.path.getmtime)
            return experts_dict, latest_file

        def on_done(result):
            experts_dict, latest_file = result
            self.ui.experts = experts_dict

            if not experts_dict:
                Logger.info("No expert files found")
                return

            latest_name = os.path.basename(latest_file)
            self.ui.expert_input.setText(latest_name)
            Logger.success(f"Loaded experts: {len(experts_dict)} found, latest = {latest_name}")

        # Run in background
        self.runner = ThreadRunner(self.ui)  # must exist in __init__
        self.runner.on_result = on_done
        self.runner.run(task, expert_folder)

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

    def copy_data_from_autotester(self):
        try:
          auto_batch_page = self.main_window.autoBatch_page
          mt5_dir_path = auto_batch_page.mt5_dir_input.text()
          data_dir_path = auto_batch_page.data_input.text()
          expert_name = auto_batch_page.expert_input.currentText()
          symbol_prefix = auto_batch_page.symbol_prefix.text()
          symbol_suffix = auto_batch_page.symbol_suffix.text()
          deposit = auto_batch_page.deposit_input.text()
          currency = auto_batch_page.currency_input.text()
          leverage = auto_batch_page.leverage_input.value() 
          timeframe = auto_batch_page.timeframe_combo.currentText()
          date_range = auto_batch_page.date_combo.currentText()
          date_from = auto_batch_page.date_from.date()
          date_to = auto_batch_page.date_to.date()

          Logger.info(f"AutoBatch Page Data: mt5_dir_path = {mt5_dir_path}, data_dir_path = {data_dir_path}, expert_name = {expert_name}, symbol_prefix = {symbol_prefix}, symbol_suffix = {symbol_suffix}, deposit = {deposit}, currency = {currency}, leverage = {leverage}, timeframe = {timeframe}, date_range = {date_range}, date_from = {date_from}, date_to = {date_to}")
          
          self.ui.mt5_input.setText(mt5_dir_path)
          self.ui.data_folder_input.setText(data_dir_path)
          self.ui.expert_input.setCurrentText(expert_name)
          self.ui.pair_prefix_input.setText(symbol_prefix)
          self.ui.pair_suffix_input.setText(symbol_suffix)
          self.ui.deposit_input.setText(deposit)
          self.ui.currency_input.setText(currency)
          self.ui.leverage_input.setValue(leverage)
          self.ui.date_combo.setCurrentText(date_range)
          self.ui.date_from.setDate(date_from)
          self.ui.date_to.setDate(date_to)
          self.ui.timeframe_combo.setCurrentText(timeframe)
        except Exception as e:
          Logger.error(f"Error in copy_data_from_autotester: {e}")
    
    def copy_dates_from_setfinder(self):
        try:
          self.ui.date_from.setDate(self.setfinder_ui.start_date_input.date())
          self.ui.date_to.setDate(self.setfinder_ui.end_date_input.date())
        except Exception as e:
          Logger.error(f"Error in copy_dates_from_setfinder: {e}")
   
    def update_selection(self, name, state):
            """Add or remove checkbox value from list based on state"""
            if state == Qt.Checked:
                if name not in self.selected_reports:
                    self.selected_reports.append(name)
            else:
                if name in self.selected_reports:
                    self.selected_reports.remove(name)
            print("Selected reports:", self.selected_reports)

    def read_set_file(self, path):
        try:
            # Try UTF-16 first
            with open(path, encoding="utf-16") as f:
                data = f.read()
                print("Read using UTF-16")
                return data

        except UnicodeError:
            # If UTF-16 fails, try UTF-8
            try:
                with open(path, encoding="utf-8") as f:
                    data = f.read()
                    print("Read using UTF-8")
                    return data
            except Exception as e:
                print(f"Failed to read file: {e}")
                return None

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def extract_symbol(self, path):
            data = self.read_set_file(path)
            
            for line in data.splitlines():

                line = line.strip().lstrip(';').strip()   # remove ; and trim spaces

                if line.startswith("Symbol="):
                    symbol = line.split("=")[1]
                    return symbol
                
            return 'EURUSD'
   
    def on_start_button_clicked(self):
        try:
            print("self.connected: ", self.connected)
            if not(self.connected):
                QMessageBox.warning(self.ui, "Error", "Problem in Connecting to MT5 terminal. Please Connect again")
                Logger.warning("Problem in Connecting to MT5 terminal.")
                return
            if (self.ui.set_table.rowCount()<=0):
                QMessageBox.warning(self.ui, "Warning", "No Set File To Process")
                Logger.warning("No Set File To Process")
                return


            report_columns = {"CSV": 2, "Graph": 3, "Overview": 4}

            # ---------------- UI Setup ----------------
            self.ui.stop_button.show()
            self.ui.resume_button.hide()
            self.ui.kill_button.show()
            self.ui.start_button.setEnabled(False)
            self.ui.start_button.setText("RUNNING...")

            # ---------------- Collect Inputs ----------------
            folder = self.ui.input_set_files.text().strip()
            mt5_path = self.ui.mt5_input.text().strip()
            data_path = self.ui.data_folder_input.text().strip()
            expert_name = self.ui.expert_input.currentText().strip()
            expert_file = self.ui.experts.get(expert_name)
            self.report_path = os.path.join(data_path, "Agent Finder Results",)
            max_retries = int(self.ui.retry_input.text())
            timestamp = time.time()
            timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(timestamp))
            # timestamp = datetime.now()

            Logger.info(f"Folder selected: {folder}")
            Logger.info(f"MT5 Path: {mt5_path}")
            Logger.info(f"Data Folder Path: {data_path}")
            Logger.info(f"Expert Name: {expert_name}")
            Logger.info(f"Expert File: {expert_file}")
            Logger.info(f"Report Path: {self.report_path}")
            Logger.info(f"Max retries: {max_retries}")

            path = os.path.join(folder, self.ui.set_table.item(0, 0).text())
            symbol = self.extract_symbol(path)

            # ---------------- Validation ----------------
            if not all([folder, mt5_path, data_path, expert_file]):
                QMessageBox.warning(self.ui, "Error", "Please fill all required fields before starting.")
                Logger.warning("Missing required fields before starting.")
                return

            # Ensure report folder exists
            try:
                os.makedirs(self.report_path, exist_ok=True)
                Logger.info(f"Report folder ready at: {self.report_path}")
            except Exception as e:
                Logger.error(f"Failed to create report folder: {e}")
                QMessageBox.critical(self.ui, "Error", f"Failed to create report folder:\n{e}")
                return

            # Collect .set files
            set_files = [f for f in os.listdir(folder) if f.endswith(".set")]
            if not set_files:
                QMessageBox.warning(self.ui, "Error", "No .set files found in the selected folder.")
                Logger.warning("No .set files found in folder.")
                return

            # ---------------- Task Definition ----------------
            def task(worker=None):
                try:

                    report_path = os.path.join("Agent Finder Results", f"AutoTester_{timestamp}", "Sets")
                    base_report_path = os.path.join(self.report_path, f"AutoTester_{timestamp}", "Sets")
                    os.makedirs(base_report_path, exist_ok=True)
                    Logger.info(f"Base report folder ready: {base_report_path}")
                    
                    for row in range(self.ui.set_table.rowCount()):
                            if ("CSV" not in self.selected_reports):
                                try:
                                    status_item = self.ui.set_table.item(row, 2)
                                    if status_item:
                                        status_item.setText("Not Selected")
                                    else:
                                        self.ui.set_table.setItem(row, 2, QTableWidgetItem("Not Selected"))
                                except Exception as e:
                                    Logger.warning(f"Failed to update table at row {row}: {e}")
                            else:
                                try:
                                    status_item = self.ui.set_table.item(row, 2)
                                    if status_item:
                                        status_item.setText("Waiting")
                                    else:
                                        self.ui.set_table.setItem(row, 2, QTableWidgetItem("Waiting"))
                                except Exception as e:
                                    Logger.warning(f"Failed to update table at row {row}: {e}")
                            
                            if ("Graph" not in self.selected_reports):
                                try:
                                    status_item = self.ui.set_table.item(row, 3)
                                    if status_item:
                                        status_item.setText("Not Selected")
                                    else:
                                        self.ui.set_table.setItem(row, 3, QTableWidgetItem("Not Selected"))
                                except Exception as e:
                                    Logger.warning(f"Failed to update table at row {row}: {e}")
                            else:
                                try:
                                    status_item = self.ui.set_table.item(row, 3)
                                    if status_item:
                                        status_item.setText("Waiting")
                                    else:
                                        self.ui.set_table.setItem(row, 3, QTableWidgetItem("Waiting"))
                                except Exception as e:
                                    Logger.warning(f"Failed to update table at row {row}: {e}")
                            
                            if ("Overview" not in self.selected_reports):
                                try:
                                    status_item = self.ui.set_table.item(row, 4)
                                    if status_item:
                                        status_item.setText("Not Selected")
                                    else:
                                        self.ui.set_table.setItem(row, 4, QTableWidgetItem("Not Selected"))
                                except Exception as e:
                                    Logger.warning(f"Failed to update table at row {row}: {e}")
                            else:
                                try:
                                    status_item = self.ui.set_table.item(row, 4)
                                    if status_item:
                                        status_item.setText("Waiting")
                                    else:
                                        self.ui.set_table.setItem(row, 4, QTableWidgetItem("Waiting"))
                                except Exception as e:
                                    Logger.warning(f"Failed to update table at row {row}: {e}")
                            
                    for row, set_file in enumerate(set_files):
                        # Stop immediately if requested
                        if worker and worker._stop:
                            Logger.info("Task stopped by user.")
                            return False

                        # Update table status
                        try:
                            status_item = self.ui.set_table.item(row, 1)
                            if status_item:
                                status_item.setText("PROCESSING")
                            else:
                                self.ui.set_table.setItem(row, 1, QTableWidgetItem("PROCESSING"))
                        except Exception as e:
                            Logger.warning(f"Failed to update table at row {row}: {e}")

                        # Build settings
                        forward_date = QDate.currentDate().toString("yyyy-MM-dd")
                        settings = {
                            "test_name": symbol,
                            "expert": expert_name,
                            "param_file": set_file,
                            "symbol": symbol,
                            "timeframe": self.ui.timeframe_combo.currentText(),
                            "symbol_prefix": self.ui.pair_prefix_input.text().strip(),
                            "symbol_suffix": self.ui.pair_suffix_input.text().strip(),
                            "date": self.ui.date_combo.currentText(),
                            "date_from": self.ui.date_from.date().toString("yyyy-MM-dd"),
                            "date_to": self.ui.date_to.date().toString("yyyy-MM-dd"),
                            "forward": "Disabled",
                            "forward_date": forward_date,
                            "delay": "100",
                            "delay_mode": "Time based",
                            "model": "Every tick based on real ticks",
                            "deposit": self.ui.deposit_input.text(),
                            "currency": self.ui.currency_input.text(),
                            "leverage": str(self.ui.leverage_input.value()),
                            "optimazation": "Disabled",
                            "criterion": "Balance Max"
                        }

                        

                        # Run strategy per report mode
                        

                        Logger.info(f"Running strategy for {set_file}")
                        retry = 0
                        success = False
                        Logger.info(f"Report folder ready: {os.path.join(report_path)}")
                        while retry < max_retries:
                            if worker and worker._stop:
                                Logger.info("Task stopped by user during retry loop.")
                                return False
                            while worker and worker._pause:
                                time.sleep(0.1)  # Pause support

                            try:
                                Logger.info(f"Running strategy for {set_file} attempt {retry+1}/{max_retries}")
                                print("---------------- Hassan ----------------------")
                                print("CSV" in self.selected_reports)
                                result = self.mt5.run_strategy(settings, data_path, mt5_path, report_path, self.ui.experts, report_type="HTML",setProcessor=True,save_csv= "CSV" in self.selected_reports)

                                print("self.mt5.pid = ",self.mt5.pid)


                                print("----------------------------------------------")
                                print('result["status"] = ',result["status"])
                                print("--------------------------------------")

                                if result["status"] == "success":
                                    success = True
                                    try:
                                        status_item = self.ui.set_table.item(row, 1)
                                        if status_item:
                                            status_item.setText("Completed")
                                        else:
                                            self.ui.set_table.setItem(row, 1, QTableWidgetItem("PROCESSING"))


                                        for report_mode in self.selected_reports[1:]:
                                            print("report_mode = ",report_mode)
                                            col_index = report_columns.get(report_mode, None)
                                            print("col_index = ",col_index)
                                            if col_index is not None:
                                                report_item = self.ui.set_table.item(row, col_index)
                                                if report_item:
                                                    report_item.setText("Generated")
                                            else:
                                                self.ui.set_table.setItem(row, col_index, QTableWidgetItem("Generated"))

                                    except Exception as e:
                                        Logger.warning(f"Failed to update table at row {row}: {e}")
                                    break

                                retry += 1
                                try:
                                    status_item = self.ui.set_table.item(row, 1)
                                    if status_item:
                                        status_item.setText(f"Failed ({retry}/{max_retries})")
                                    else:
                                        self.ui.set_table.setItem(row, 1, QTableWidgetItem(f"Failed ({retry}/{max_retries})"))

                                    for report_mode in self.selected_reports[1:]:
                                        print("report_mode = ",report_mode)
                                        col_index = report_columns.get(report_mode, None)
                                        if col_index is not None:
                                            report_item = self.ui.set_table.item(row, col_index)
                                            if report_item:
                                                report_item.setText("Failed")
                                            else:
                                                self.ui.set_table.setItem(row, col_index, QTableWidgetItem("Failed"))



                                except Exception as e:
                                    Logger.warning(f"Failed to update table at row {row}: {e}")
                                Logger.error("Strategy failed… retrying…")
                            except Exception as e:
                                Logger.error(f"Strategy crashed on attempt {retry+1}: {e}")
                                retry += 1

                        if not success:
                            Logger.error(f"❌ Strategy FAILED after {max_retries} attempts for {set_file}")
                            try:
                                status_item = self.ui.set_table.item(row, 1)
                                if status_item:
                                    status_item.setText(f"Failed")
                                else:
                                    self.ui.set_table.setItem(row, 1, QTableWidgetItem(f"Failed"))
                            except Exception as e:
                                Logger.warning(f"Failed to update table at row {row}: {e}")

                    self.organize_reports(base_report_path)
                    
                    return True


                except Exception as e:
                    Logger.error(f"Unexpected error in task: {e}")
                    return False

            # ---------------- Completion Callback ----------------
            def on_done(result):
                try:
                    if result:
                        QMessageBox.information(self.ui, "Success", "All tests completed successfully!")
                        Logger.success("✅ All tests completed successfully!")
                        for row in range(len(set_files)):
                            status_item = self.ui.set_table.item(row, 1)
                            if status_item:
                                status_item.setText("COMPLETED")
                            else:
                                self.ui.set_table.setItem(row, 1, QTableWidgetItem("COMPLETED"))
                    else:
                        QMessageBox.warning(self.ui, "Error", "Some tests failed or were stopped.")
                        Logger.warning("Some tests failed or were stopped.")

                    self.ui.kill_button.hide()
                    self.ui.resume_button.hide()
                    self.ui.stop_button.hide()
                    self.ui.start_button.show()
                    self.ui.start_button.setEnabled(True)
                    self.ui.start_button.setText("START")

                except Exception as e:
                    Logger.error(f"Error in on_done handler: {e}")

            # ---------------- Run in ThreadRunnerV2 ----------------
            self.runnerV2 = ThreadRunnerV2(parent=self.ui)
            self.runnerV2.on_result = on_done
            self.runnerV2.run(task, show_dialog=False)

        except Exception as e:
            Logger.error(f"Fatal error in on_start_button_clicked: {e}")
            QMessageBox.critical(self.ui, "Error", f"Unexpected error:\n{e}")

    def on_stop_button_clicked(self):
        try:
            if hasattr(self, 'runnerV2') and self.runnerV2.worker:
                self.logger.info("Stop button clicked - pausing the task")
                
                try:
                    self.runnerV2.pause()
                    self.logger.info("Runner paused successfully")
                except Exception as pause_err:
                    self.logger.error("Failed to pause runner", pause_err)
                
                # Update UI safely
                try:
                    self.ui.stop_button.hide()
                    self.ui.resume_button.show()
                    self.ui.kill_button.show()
                    self.ui.start_button.hide()
                    self.logger.info("UI updated after stopping")
                except Exception as ui_err:
                    self.logger.error("Failed to update UI after stop", ui_err)
            else:
                self.logger.warning("Stop button clicked but no active runner found")
        except Exception as e:
            self.logger.error("Error handling Stop button click", e)

    def on_resume_button_clicked(self):
        try:
            if hasattr(self, 'runnerV2') and self.runnerV2.worker:
                self.logger.info("Resume button clicked - resuming the task")
                
                try:
                    self.runnerV2.resume()
                    self.logger.info("Runner resumed successfully")
                except Exception as resume_err:
                    self.logger.error("Failed to resume runner", resume_err)
                
                # Update UI safely
                try:
                    self.ui.resume_button.hide()
                    self.ui.kill_button.hide()
                    self.ui.stop_button.show()
                    self.ui.start_button.show()
                    self.ui.start_button.setEnabled(False)
                    self.ui.start_button.setText("RUNNING...")
                    self.logger.info("UI updated after resume")
                except Exception as ui_err:
                    self.logger.error("Failed to update UI after resume", ui_err)
            else:
                self.logger.warning("Resume button clicked but no active runner found")
        except Exception as e:
            self.logger.error("Error handling Resume button click", e)

    def on_kill_button_clicked(self):
        try:
            if hasattr(self, 'runnerV2') and self.runnerV2.worker:
                self.logger.info("Kill button clicked - terminating the task")
                try:
                    pid = getattr(self.mt5, 'pid', None)
                    self.logger.debug(f"MT5 PID: {pid}")
                except Exception as e:
                    self.logger.warning(f"Could not get MT5 PID: {e}")
                    pid = None

                self.runnerV2.stop(immediate_stop=True, pid=pid)
                
                # Update UI safely
                try:
                    self.ui.kill_button.hide()
                    self.ui.resume_button.hide()
                    self.ui.stop_button.hide()
                    self.ui.start_button.show()
                    self.ui.start_button.setEnabled(True)
                    self.ui.start_button.setText("START")
                    self.logger.info("UI updated after kill")
                except Exception as ui_err:
                    self.logger.error("Failed to update UI after kill", ui_err)
            else:
                self.logger.warning("Kill button clicked but no active runner found")
        except Exception as e:
            self.logger.error("Error handling Kill button click", e)

    def organize_reports(self, base_report_path):

        try:
            # Create report folders if not exist
            for report_mode in self.selected_reports:
                report_mode_path = os.makedirs(os.path.join(base_report_path, report_mode), exist_ok=True)

            html_folder = os.path.join(base_report_path, "HTML Reports")
            overview_folder = os.path.join(base_report_path, "Overview")
            csv_folder = os.path.join(base_report_path, "CSV")
            graph_folder = os.path.join(base_report_path, "Graph")

            # Process files in base_report_path
            for file_name in os.listdir(base_report_path):
                try:
                    file_path = os.path.join(base_report_path, file_name)
                    if os.path.isdir(file_path):
                        continue  # skip folders

                    file_lower = file_name.lower()

                    # HTML/HTM files
                    if file_lower.endswith((".htm", ".html")):
                        dest = os.path.join(base_report_path, html_folder, file_name)
                        shutil.move(file_path, dest)
                        self.logger.info(f"Moved HTML file: {file_name} → HTML Reports")

                    # PNG files
                    elif file_lower.endswith(".png"):
                        if "-" in file_name and "Graph" in self.selected_reports:
                            dest = os.path.join(base_report_path, graph_folder, file_name)
                            shutil.move(file_path, dest)
                            self.logger.info(f"Moved PNG to Graph: {file_name}")
                        elif "Overview" in self.selected_reports:
                            dest = os.path.join(base_report_path, overview_folder, file_name)
                            shutil.move(file_path, dest)
                            self.logger.info(f"Moved PNG to Overview: {file_name}")

                    # CSV files
                    elif file_lower.endswith(".csv") and "CSV" in self.selected_reports:
                        dest = os.path.join(base_report_path, csv_folder, file_name)
                        shutil.move(file_path, dest)
                        self.logger.info(f"Moved CSV file: {file_name}")

                except Exception as file_err:
                    self.logger.error(f"Failed to process file: {file_name}", file_err)

            # Delete remaining files/folders in base_report_path
            for item in os.listdir(base_report_path):
                try:
                    item_path = os.path.join(base_report_path, item)

                    if item in folders_to_create:
                        continue  # keep report folders

                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        self.logger.info(f"Deleted file: {item}")
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        self.logger.info(f"Deleted folder: {item}")

                except Exception as del_err:
                    self.logger.error(f"Failed to delete item: {item}", del_err)

            self.logger.info("✅ Report organization completed.")

        except Exception as e:
            self.logger.error("Failed to organize reports", e)
