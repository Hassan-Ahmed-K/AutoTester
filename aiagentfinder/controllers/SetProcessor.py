import psutil
import os,re,glob,datetime
import pandas as pd
from aiagentfinder.utils import MT5Manager , Logger 
from aiagentfinder.utils.workerThread import ThreadRunner
from PyQt5.QtCore import Qt, QDate, QItemSelectionModel, QItemSelection
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QFileDialog, QTableWidgetSelectionRange, QTableWidget, QMessageBox,QComboBox,QApplication

class SetProcessorController:
    def __init__(self,ui):
        self.ui = ui
        main_window = self.ui.parent()
        self.auto_batch_ui = main_window.autoBatch_page
        self.setfinder_ui = main_window.setFinder_page
        self.mt5 = MT5Manager()
        self.runner = ThreadRunner()
        self.logger = Logger()
   


        self.ui.browse_set_files.clicked.connect(self.browse_set_file)
        self.ui.toggle_graph.stateChanged.connect(self.browse_set_file)
        self.ui.toggle_csv.stateChanged.connect(self.browse_set_file)
        self.ui.toggle_overview.stateChanged.connect(self.browse_set_file)
        self.ui.toggle_semi_auto.stateChanged.connect(self.browse_set_file)

        self.ui.mt5_btn.clicked.connect(self.browse_mt5_dir)
        self.ui.refresh_btn.clicked.connect(self.refresh_expert)
        self.ui.expert_button.clicked.connect(self.browse_expert_file)
        self.ui.data_folder_input.textChanged.connect(self.update_expert_list)



        self.ui.date_combo.currentTextChanged.connect(self.toggle_date_fields)
        
        self.ui.copy_data_button.clicked.connect(self.copy_data_from_autotester)
        self.ui.copy_dates_button.clicked.connect(self.copy_dates_from_setfinder)

        self.ui.start_button.clicked.connect(self.on_start_button_clicked)
        # self.ui.resume_button.clicked.connect(self.resume_tests)
        # self.ui.schedule_toggle.stateChanged.connect(self.toggle_schedule)




    def browse_set_file(self):
        data_folder = self.ui.data_folder_input.text()

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
          self.ui.mt5_input.setText(self.auto_batch_ui.mt5_dir_input.text())
          self.ui.data_folder_input.setText(self.auto_batch_ui.data_input.text())
          self.ui.expert_input.setCurrentText(self.auto_batch_ui.expert_input.currentText())
          self.ui.pair_prefix_input.setText(self.auto_batch_ui.symbol_prefix.text())
          self.ui.pair_suffix_input.setText(self.auto_batch_ui.symbol_suffix.text())
          self.ui.deposit_input.setText(self.auto_batch_ui.deposit_input.text())
          self.ui.currency_input.setText(self.auto_batch_ui.currency_input.text())
          self.ui.leverage_input.setValue(self.auto_batch_ui.leverage_input.value())
          self.ui.date_combo.setCurrentText(self.auto_batch_ui.date_combo.currentText())
          self.ui.date_from.setDate(self.auto_batch_ui.date_from.date())
          self.ui.date_to.setDate(self.auto_batch_ui.date_to.date())
          self.ui.timeframe_combo.setCurrentText(self.auto_batch_ui.timeframe_combo.currentText())
        except Exception as e:
          Logger.error(f"Error in copy_data_from_autotester: {e}")
    def copy_dates_from_setfinder(self):
        try:
          self.ui.date_from.setDate(self.setfinder_ui.start_date_input.date())
          self.ui.date_to.setDate(self.setfinder_ui.end_date_input.date())
        except Exception as e:
          Logger.error(f"Error in copy_dates_from_setfinder: {e}")
   

    def on_start_button_clicked(self):
        try:
            folder = self.ui.input_set_files.text().strip()
            mt5_path = self.ui.mt5_input.text().strip()
            data_path = self.ui.data_folder_input.text().strip()
            expert_name = self.ui.expert_input.currentText().strip()
            expert_file = self.ui.experts.get(expert_name)
            report_path = os.path.join(data_path, "Agent Finder Results")

            # --------- Validate inputs ---------
            if not all([folder, mt5_path, data_path, expert_file]):
                QMessageBox.warning(self.ui, "Error", "Please fill all required fields before starting.")
                Logger.warning("Missing required fields before starting.")
                return

            # --------- Ensure report folder exists ---------
            try:
                os.makedirs(report_path, exist_ok=True)
                Logger.info(f"Report folder ready at: {report_path}")
            except Exception as e:
                Logger.error(f"Failed to create report folder: {e}")
                QMessageBox.critical(self.ui, "Error", f"Failed to create report folder:\n{e}")
                return

            # --------- Collect .set files ---------
            set_files = [f for f in os.listdir(folder) if f.endswith(".set")]
            if not set_files:
                QMessageBox.warning(self.ui, "Error", "No .set files found in the selected folder.")
                Logger.warning("No .set files found in folder.")
                return

            # --------- Task definition ---------
            def task():
                try:
                    for row, set_file in enumerate(set_files):
                        # Safely update table status
                        try:
                            if self.ui.set_table.item(row, 1):
                                self.ui.set_table.item(row, 1).setText("PROCESSING")
                            else:
                                self.ui.set_table.setItem(row, 1, QTableWidgetItem("PROCESSING"))
                        except Exception as e:
                            Logger.warning(f"Failed to update table at row {row}: {e}")

                        # Build settings dictionary
                        # symbol = os.path.basename(set_file).split("_")[0]
                        symbol = "NZDUSD"
                        forward_date = QDate.currentDate().toString("yyyy-MM-dd")
                        settings = {
                            "test_name": set_file,
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
                            "delay" : "100",
                            "delay_mode": "Time based",
                            "model": "Every tick based on real ticks",
                            "deposit": self.ui.deposit_input.text(),
                            "currency": self.ui.currency_input.text(),
                            "leverage": str(self.ui.leverage_input.value()),
                            "optimazation": "Disabled",
                            "criterion": "Balance Max"
                        }

                        # Run MT5 strategy
                        try:
                            self.mt5.run_strategy(settings, data_path, mt5_path, report_path, self.ui.experts)
                        except Exception as e:
                            Logger.error(f"Error running strategy for {set_file}: {e}")
                            continue

                    return True

                except Exception as e:
                    Logger.error(f"Unexpected error in task: {e}")
                    return False

            def on_done(result):
                try:
                    if result:
                        QMessageBox.information(self.ui, "Success", "All tests completed successfully!")
                        Logger.success("✅ All tests completed successfully!")
                        for row in range(len(set_files)):
                            if self.ui.set_table.item(row, 1):
                                self.ui.set_table.item(row, 1).setText("COMPLETED")
                            else:
                                self.ui.set_table.setItem(row, 1, QTableWidgetItem("COMPLETED"))
                    else:
                        QMessageBox.warning(self.ui, "Error", "Some tests failed. Check logs for details.")
                        Logger.warning("Some tests failed.")
                except Exception as e:
                    Logger.error(f"Error in on_done handler: {e}")

            # --------- Run task in thread ---------
            self.runner = ThreadRunner(self.ui)
            self.runner.on_result = on_done
            self.runner.run(task)

        except Exception as e:
            Logger.error(f"Fatal error in on_start_button_clicked: {e}")
            QMessageBox.critical(self.ui, "Error", f"Unexpected error:\n{e}")

        