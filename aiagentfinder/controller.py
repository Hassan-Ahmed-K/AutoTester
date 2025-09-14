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
        file_path, _ = QFileDialog.getOpenFileName(
            self.ui, "Select MT5 Terminal", "", "Executable Files (*.exe)"
        )
        if not file_path:
            return

        self.ui.mt5_dir_input.setText(file_path)
        Logger.info(f"MT5 terminal selected: {file_path}")

        # ---------------------------
        # TASK for background thread
        # ---------------------------
        def task(file_path):
            result = {
                "file_path": file_path,
                "data_folder": None,
                "deposit_info": None,
            }

            try:
                success = self.mt5.connect(file_path)
                if success:
                    dataPath = self.mt5.get_dataPath()
                    
                    if dataPath:
                        result["data_folder"] = dataPath
                        os.makedirs(os.path.join(dataPath, "Agent Finder Results"), exist_ok=True)
                        Logger.success(f"MT5 Data Folder: {dataPath}")
                    else:
                        Logger.warning("Could not retrieve terminal_info from MT5")
                    # --- Deposit info ---
                    result["deposit_info"] = self.mt5.get_deposit()
                    
                    if result["deposit_info"]:
                        Logger.success("Deposit info retrieved successfully")
                    else:
                        Logger.warning("No deposit info retrieved")

                    self.mt5.get_symbol_list()

                    print("Disconnecting")
                    self.mt5.disconnect()

                    exe_name = os.path.basename(file_path)

                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'] == exe_name:
                            try:
                                proc.terminate()
                                print(f"Closed MT5 window: {exe_name}")
                            except Exception as e:
                                print(f"Could not close MT5 window: {e}")

                else:
                    Logger.error(f"Failed to connect to MT5: {self.mt5.last_error()}")

            except Exception as e:
                Logger.error(f"Error while connecting to MT5: {e}")

            return result


        # ---------------------------
        # CALLBACKS (main thread)
        # ---------------------------
        def on_done(result):
            if result["data_folder"]:
                self.ui.data_input.setText(result["data_folder"])
                Logger.info(f"Auto-selected Data Folder: {result['data_folder']}")
            else:
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
            else:
                QMessageBox.critical(self.ui, "MT5 Connection", "❌ Failed to connect MT5. Please check the path.")
            QApplication.processEvents()
        
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
        folder = QFileDialog.getExistingDirectory(self.ui, "Select Data Folder")
        if not folder:
            QMessageBox.warning(self.ui, "Error", "❌ Please select a valid Data Folder.")
            Logger.warning("Please select a valid Data Folder.")
            return

        def task(folder):
            try:
                # Ensure folder exists and prepare Agent Finder Results directory
                if not os.path.isdir(folder):
                    raise FileNotFoundError(f"Folder does not exist: {folder}")

                results_dir = os.path.join(folder, "Agent Finder Results")
                os.makedirs(results_dir, exist_ok=True)

                Logger.success(f"Data folder ready: {folder}")
                return folder
            except Exception as e:
                Logger.error(f"Error while validating Data Folder: {e}")
                raise

        def on_done(folder):
            # Update UI safely on main thread
            self.ui.data_input.setText(folder)
            QMessageBox.information(self.ui, "Data Folder", f"✅ Data folder set:\n{folder}")
            Logger.info(f"Data folder selected: {folder}")

        def on_error(err):
            QMessageBox.critical(self.ui, "Error", f"❌ Failed to select Data Folder.\nError: {str(err)}")
            Logger.error(f"Failed to select Data Folder: {err}")

        # Run threaded
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task, folder)

    def browse_report_folder(self):
        try:
            folder = QFileDialog.getExistingDirectory(self.ui, "Select Report Folder")
            if not folder:
                QMessageBox.warning(self.ui, "Error", "❌ Please select a valid Report Folder.")
                Logger.warning("Please select a valid Report Folder.")
                return

            # Define Background task
            def task(folder):
                if not os.path.isdir(folder):
                    raise FileNotFoundError(f"Folder does not exist: {folder}")

                # Ensure subfolder exists (optional, for consistency)
                os.makedirs(os.path.join(folder, "AI Agent Reports"), exist_ok=True)

                return folder

        
            def on_done(result_folder):
                self.ui.report_input.setText(result_folder)
                Logger.success(f"Report folder selected: {result_folder}")
                QMessageBox.information(
                    self.ui,
                    "Report Folder",
                    f"✅ Report folder set:\n{result_folder}"
                )

            def on_error(err):
                Logger.error(f"Error while selecting Report Folder: {err}")
                QMessageBox.critical(
                    self.ui,
                    "Error",
                    f"❌ Failed to select Report Folder.\nError: {str(err)}"
                )
            self.runner = ThreadRunner(self.ui)
            self.runner.on_result = on_done
            self.runner.on_error = on_error
            self.runner.run(task, folder)

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

        return settings
    
    def add_test_to_queue(self):
        settings = self.test_settings()
        if not settings:
            return

        def task():
            # The long/slow part of work
            self.queue.add_test_to_queue(settings)
            return settings["test_name"]

        def on_done(test_name):
            QMessageBox.information(self.ui, "Added", f"Test '{test_name}' added to queue.")
            Logger.success(f"Test '{test_name}' added to queue.")

        # Run in background with progress dialog
        self.runner = ThreadRunner(self.ui)   # make sure you initialized in __init__
        self.runner.on_result = on_done       # hook result handler
        self.runner.run(task)

    def get_best_symbol(self,user_input: str) -> str :
        symbols = self.mt5.symbol_list
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
        raw = self.ui.testfile_input.text().strip()
        print("raw = ", raw)
        best = self.get_best_symbol(raw)
        if best:
            Logger.info(f"Best symbol found: {best}")
            self.ui.symbol_input.setText(best)

    def update_expert_list(self):
        data_folder = self.ui.data_input.text()
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
        base_name, ext = os.path.splitext(current_text)

        # Pattern: capture "_number" at the end if present
        version_pattern = re.compile(r"^(.*)_(\d+)$")

        match = version_pattern.match(base_name)
        if match:
            # Case 1: Expert has versions
            prefix = match.group(1)
            versions = []
            for name, info in self.ui.experts.items():
                name_base, _ = os.path.splitext(name)
                m = version_pattern.match(name_base)
                if m and m.group(1) == prefix:
                    versions.append((int(m.group(2)), name))

            if versions:
                # Pick highest version
                latest_name = max(versions, key=lambda x: x[0])[1]
                index = self.ui.expert_input.findText(latest_name)
                if index != -1:
                    self.ui.expert_input.setCurrentIndex(index)
                    return

        # Case 2: No versions → pick latest modified among matches
        matches = [
            (info["modified"], name)
            for name, info in self.ui.experts.items()
            if name.startswith(base_name)
        ]

        if matches:
            latest_name = max(matches, key=lambda x: x[0])[1]
            index = self.ui.expert_input.findText(latest_name)
            if index != -1:
                self.ui.expert_input.setCurrentIndex(index)

    def load_experts(self, expert_folder):
        if not expert_folder or not isinstance(expert_folder, str):
            Logger.warning("Invalid expert folder path")
            return None

        def task(folder):
            import glob, os
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
    
    # --- helper method ---
    def toggle_date_fields(self, text):
        """Enable/disable date pickers and adjust dates based on combo selection."""
        today = QDate.currentDate()

        if text == "Entire history":
            # Disable pickers, set from a very old date to today
            self.ui.date_from.setEnabled(False)
            self.ui.date_to.setEnabled(False)
            self.ui.date_from.setDate(QDate(1970, 1, 1))  # or your earliest supported date
            self.ui.date_to.setDate(today)

        elif text == "Last month":

            date_from = today.addMonths(-1)
            self.ui.date_from.setDate(date_from)
            self.ui.date_to.setDate(today)

        elif text == "Last 3 months":
            self.ui.date_from.setEnabled(False)
            self.ui.date_to.setEnabled(False)
            self.ui.date_from.setDate(today.addMonths(-3))
            self.ui.date_to.setDate(today)

        elif text == "Last 6 months":
            self.ui.date_from.setEnabled(False)
            self.ui.date_to.setEnabled(False)
            self.ui.date_from.setDate(today.addMonths(-6))
            self.ui.date_to.setDate(today)    

        elif text == "Last year":
            # Disable pickers, set range to last year
            self.ui.date_from.setEnabled(False)
            self.ui.date_to.setEnabled(False)

            date_from = today.addYears(-1)
            self.ui.date_from.setDate(date_from)
            self.ui.date_to.setDate(today)

        elif text == "Custom period":
            # Enable pickers, let user choose
            self.ui.date_from.setEnabled(True)
            self.ui.date_to.setEnabled(True)
            self.ui.date_from.setDate(today)   # default both to today
            self.ui.date_to.setDate(today)

    def adjust_forward_date(self, text):
        """Adjust forward_date depending on combo selection."""
        today = QDate.currentDate()

        if text == "No":
            self.ui.forward_date.setEnabled(False)
            self.ui.forward_date.setDate(today)

        elif text == "1/4":
            self.ui.forward_date.setEnabled(False)
            self.ui.forward_date.setDate(today.addMonths(3))  # 1/4 year = 3 months

        elif text == "1/3":
            self.ui.forward_date.setEnabled(False)
            self.ui.forward_date.setDate(today.addMonths(4))  # 1/3 year ≈ 4 months

        elif text == "1/2":
            self.ui.forward_date.setEnabled(False)
            self.ui.forward_date.setDate(today.addMonths(6))  # half year

        elif text == "Custom":
            self.ui.forward_date.setEnabled(True)  # let user pick manually

    def update_delay_input(self, text):
        """Enable spinbox only when 'Custom Delay' is selected"""
        if text == "Custom Delay":
            self.delay_input.setEnabled(True)

        elif text == "Random delay":
            value = random.randint(0, 1000)
            self.ui.delay_input.setValue(value)
            self.ui.delay_input.setEnabled(False)

        elif "ms" in text:  
            # Extract number from string like "50 ms"
            value = int(text.replace(" ms", "").strip())
            self.ui.delay_input.setValue(value)
            self.ui.delay_input.setEnabled(False)
        else:
            # For Zero latency, Random delay, etc.
            self.ui.delay_input.setValue(0)
            self.ui.delay_input.setEnabled(False)

    def on_item_clicked(self, item):
        row = self.queue.get_element_index(item.text())
        self.selected_queue_item_index = row
        print(f"Clicked on: {item.text()} at index {row}")

    def move_up(self):
        if self.selected_queue_item_index == -1:
            QMessageBox.information(self.ui, "List Item Not Selected", "Please select a list item")
            return

        def task(index):
            self.queue.move_up(index)
            return index - 1

        def on_done(index):
            Logger.success(f"Moved item at index {index} up")
            self.selected_queue_item_index = index
            self.ui.queue_list.setCurrentRow(index)

        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.run(task, self.selected_queue_item_index)

    def move_down(self):
        if self.selected_queue_item_index == -1:
            QMessageBox.information(self.ui, "List Item Not Selected", "Please select a list item")
            return

        def task(index):
            self.queue.move_down(index)
            return index + 1

        def on_done(index):
            Logger.success(f"Moved item at index {index} down")
            self.selected_queue_item_index = index
            self.ui.queue_list.setCurrentRow(index)

        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.run(task, self.selected_queue_item_index)

    def dup_down(self):
        if self.selected_queue_item_index == -1:
            QMessageBox.information(self.ui, "List Item Not Selected", "Please select a list item")
            return

        def task(index):
            self.queue.duplicate_test(index)
            return index

        def on_done(index):
            Logger.success(f"Duplicated item at index {index}")
            self.selected_queue_item_index = -1

        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.run(task, self.selected_queue_item_index)

    def delete_test(self):
        if self.selected_queue_item_index == -1:
            QMessageBox.information(self.ui, "List Item Not Selected", "Please select a list item")
            return

        def task(index):
            self.queue.delete_test(index)
            return index

        def on_done(index):
            Logger.success(f"Deleted item at index {index}")
            self.selected_queue_item_index = -1

        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.run(task, self.selected_queue_item_index)

    def fetch_correlation(self, market="forex", period=50, symbols=None,
                      output_format="csv", endpoint="snapshot"):
        """Blocking: returns a dataframe"""

        if not symbols:
            symbols = ["EURUSD", "EURGBP", "AUDNZD"]  # fallback


        symbol_str = "|".join(symbols)
        url = (
            f"https://www.mataf.io/api/tools/{output_format}/correl/"
            f"{endpoint}/{market}/{period}/correlation.{output_format}?symbol={symbol_str}"
        )

        response = requests.get(url, timeout=30)
        
        response.raise_for_status()
        lines = response.text.splitlines()
        print(lines)
        csv_data = "\n".join(lines[3:])
        return pd.read_csv(StringIO(csv_data))
 
    def get_correlation(self, market="forex", period=50, symbols=None,
                        output_format="csv", endpoint="snapshot",
                        on_done=None, on_error=None):
        
        symbols = ["EURUSD", "EURGBP", "AUDNZD"]
        for test in self.queue.tests: 
            if test["symbol"] not in symbols:
                symbols.append(test["symbol"])

        print(symbols)


        # if not symbols:
        #     symbols = ["EURUSD", "EURGBP", "AUDNZD"]
           
        

        def task():
            return self.fetch_correlation(market, period, symbols, output_format, endpoint)


        def _on_done(df):
            if on_done:
                on_done(df)  # delegate
            else:
                # default: show heatmap
                try:
                    corr_df = df.pivot(index="pair1", columns="pair2", values="day")

                    def show_plot():
                        import matplotlib.pyplot as plt
                        import seaborn as sns

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

                        Logger.success("Correlation heatmap generated")

                    QTimer.singleShot(0, show_plot)

                except Exception as e:
                    QMessageBox.critical(self.ui, "Error", str(e))
                    Logger.error(str(e))

        def _on_error(err):
            if on_error:
                on_error(err)
            else:
                QMessageBox.critical(self.ui, "Error", str(err))

        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = _on_done
        self.runner.on_error = _on_error
        self.runner.run(task)
      
    def show_quantity_popup(self, title, text):
        if not self.mt5.connected:
            QMessageBox.warning(self.ui, "Error", "MT5 is not connected.")
            return

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
            return
        results["test_symbol_quantity"] = dialog1.get_value()

        # Second dialog
        dialog2 = QuantityDialog(parent=self.ui, title="Strategies Count", text="How many strategies are you running")
        if dialog2.exec_() != QDialog.Accepted:
            return
        results["strategies_count"] = dialog2.get_value()

        # Strategy names
        for i in range(results["strategies_count"]):
            dialog3 = TextDialog(parent=self.ui, title=f"Strategy {i+1} Name", text=f"Please Name Strategy {i+1}")
            if dialog3.exec_() != QDialog.Accepted:
                return
            results["strategies"].append(dialog3.get_value())

        # Symbol type radio dialog
        options = ["FX Only", "FX + Metals", "FX + Indices", "FX + Metal + Indices"]
        radio_dialog = RadioDialog(
            parent=self.ui,
            title="Symbols to Test",
            text="Which symbol do you want to include:",
            options=options
        )
        if radio_dialog.exec_() != QDialog.Accepted:
            return
        results["symbol_type"] = radio_dialog.get_value()

        # Correlation filter dialog
        correlationFilterDialog = QuantityDialog(
            parent=self.ui,
            title="Correlation Filter",
            text="""Enter a value between 0-100 to filter out highly correlated pairs.
                    1) If the correlation is high (above 80) and positive then the currencies move in the same way.
                    2) If the correlation is high (above 80) and negative then the currencies move in the opposite way.
                    3) If the correlation is low (below 60) then the currencies don't move in the same way."""
        )
        if correlationFilterDialog.exec_() != QDialog.Accepted:
            return
        results["correlationFilter"] = correlationFilterDialog.get_value()

        self.non_correlated_popus_option = results

        # Read all UI values before threading
        ui_values = {
            "expert": self.ui.expert_input.currentText().strip(),
            "param_file": self.ui.param_input.text().strip(),
            "symbol_prefix": self.ui.symbol_prefix.text().strip(),
            "symbol_suffix": self.ui.symbol_suffix.text().strip(),
            "symbol": self.ui.symbol_input.text().strip(),
            "timeframe": self.ui.timeframe_combo.currentText(),
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



        # Precompute symbols on main thread (fast)
        symbols = self.get_symbols_for_option(results["symbol_type"])

        # --------------------------------
        # Step 2: Background work (THREAD)
        # --------------------------------
        def task(symbols, results, ui_values):
            # blocking fetch in background
            df = self.fetch_correlation(
                market="forex",
                period=50,
                symbols=symbols,
                output_format="csv",
                endpoint="snapshot",
            )

            # compute uncorrelated pairs
            uncorrelated_pairs = self.get_top_uncorrelated_pairs_day(
                df,
                correlation=results["correlationFilter"],
                top_n=results["test_symbol_quantity"],
            )

            if uncorrelated_pairs.empty:
                return {"pairs": [], "settings": []}

            # build settings
            settings_list = []
            for _, row in uncorrelated_pairs.iterrows():
                # uncorrelated_pair = f"{row['pair1']}{row['pair2']}"
                uncorrelated_pair = f"{row['pair1']}"

                settings = {
                    "test_name": f"{uncorrelated_pair}_trend",
                    "expert": ui_values["expert"],
                    "param_file": ui_values["param_file"],
                    "symbol_prefix": ui_values["symbol_prefix"],
                    "symbol_suffix": ui_values["symbol_suffix"],
                    "symbol": uncorrelated_pair,
                    "timeframe": ui_values["timeframe"],
                    "date_from": ui_values["date_from"],
                    "date_to": ui_values["date_to"],
                    "forward": ui_values["forward"],
                    "delay": ui_values["delay"],
                    "model": ui_values["model"],
                    "deposit": ui_values["deposit"],
                    "currency": ui_values["currency"],
                    "leverage": ui_values["leverage"],
                    "optimization": ui_values["optimization"],
                    "criterion": ui_values["criterion"],
                }
                settings_list.append(settings)

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
                QMessageBox.information(self.ui, "Added", f"Test '{settings['test_name']}' added to queue.")
                Logger.success(f"Test '{settings['test_name']}' added to queue.")

        def on_error(err):
            QMessageBox.critical(self.ui, "Error", f"Failed to process correlation data:\n{err}")
            Logger.error(str(err))

        # run threaded
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task, symbols, results, ui_values)

    def get_symbols_for_option(self, option):
        if option == "FX Only":
            return self.mt5.get_fx_symbols()
        elif option == "FX + Metals":
            return self.mt5.get_fx_symbols() + self.mt5.get_metals_symbols()
        elif option == "FX + Indices":
            return self.mt5.get_fx_symbols() + self.mt5.get_indices_symbols()
        elif option == "FX + Metal + Indices":
            return self.mt5.get_fx_symbols() + self.mt5.get_metals_symbols() + self.mt5.get_indices_symbols()
        else:
            return self.mt5.get_fx_symbols()

    def get_top_uncorrelated_pairs_day(self, df, correlation=60, top_n=5):
        df_filtered = df[df["pair1"] != df["pair2"]].copy()
        df_filtered["abs_day"] = df_filtered["day"].abs()
        
        df_filtered = df_filtered[df_filtered["abs_day"] <= correlation].sort_values("abs_day", ascending=False)

        return df_filtered[["pair1", "pair2", "day"]].head(top_n)

    # def on_start_button_clicked(self, data_path, mt5_path, report_path):
    #     print("data_path = ",data_path)
    #     print("mt5_path = ",mt5_path)
    #     print("report_path = ",report_path)


    #     if not hasattr(self, "queue") or self.queue.is_empty():
    #         QMessageBox.warning(self.ui, "No Tests", "No tests in the queue. Please add tests first.")
    #         return

    #     QMessageBox.information(self.ui, "Starting", "Running tests in queue...")
    #     Logger.info("Starting queued tests...")

    #     # Example: run tests one by one
    #     while not self.queue.is_empty():
    #         test_settings = self.queue.get_next_test()
    #         self.mt5.run_test(test_settings, data_path, mt5_path, report_path)

    #     QMessageBox.information(self.ui, "Finished", "All tests completed.")
    #     Logger.success("All tests completed.")

    def on_start_button_clicked(self, data_path, mt5_path, report_path):
        print("data_path = ", data_path)
        print("mt5_path = ", mt5_path)
        print("report_path = ", report_path)

        if not hasattr(self, "queue") or self.queue.is_empty():
            QMessageBox.warning(self.ui, "No Tests", "No tests in the queue. Please add tests first.")
            return

        # QMessageBox.information(self.ui, "Starting", "Running tests in queue...")
        Logger.info("Starting queued tests...")

        def task():
            # Run tests one by one in the thread
            while not self.queue.is_empty():
                test_settings = self.queue.get_next_test()
                self.mt5.run_test(test_settings, data_path, mt5_path, report_path)
                self.queue.refresh_queue()
            return True  # signal finished

        def on_done(_):
            QMessageBox.information(self.ui, "Finished", "All tests completed.")
            Logger.success("All tests completed.")

        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.run(task)


    def on_test_selected(self, index):
        index = self.ui.queue_list.currentRow()  # Which item was clicked
        if 0 <= index < len(self.queue.tests):
            test_data = self.queue.tests[index]  # Get the selected test
            self.load_test_parameters(test_data)  # Show it on the form
        
    def load_test_parameters(self, test_data):
        # Expert & param files
        try: 
                self.ui.testfile_input.setText(test_data["test_name"])
                self.ui.expert_input.setCurrentText(test_data["expert"])
                self.ui.param_input.setText(test_data["param_file"])
                self.ui.symbol_prefix.setText(test_data["symbol_prefix"])
                self.ui.symbol_suffix.setText(test_data["symbol_suffix"])
                self.ui.symbol_input.setText(str(test_data["symbol"]))
                self.ui.timeframe_combo.setCurrentText(str(test_data["timeframe"]))
                self.ui.date_from.setDate(QDate.fromString(test_data["date_from"], "yyyy-MM-dd"))
                self.ui.date_to.setDate(QDate.fromString(test_data["date_to"], "yyyy-MM-dd"))
                self.ui.forward_date.setDate(QDate.fromString(test_data["forward"], "yyyy-MM-dd"))
                self.ui.delay_input.setValue(int(test_data["delay"]))
                self.ui.model_combo.setCurrentText(test_data["model"])
                self.ui.deposit_input.setText(str(test_data["deposit"]))
                self.ui.currency_input.setText(test_data["currency"])
                self.ui.leverage_input.setValue(float(test_data["leverage"]))
                self.ui.optim_combo.setCurrentText(str(test_data["optimization"]))
                self.ui.criterion_input.setCurrentText(str(test_data["criterion"]))

        except Exception as e:
               Logger.error(str(e))
       



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




    def copy_parameter(self, property:dict):
        print("property : ", property)
        self.queue.update_all_tests(property)
