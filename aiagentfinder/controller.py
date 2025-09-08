# type : ignore
from PyQt5.QtWidgets import QMessageBox, QFileDialog,QComboBox, QListWidget, QListWidgetItem, QDialog
from PyQt5.QtCore import QDate ,  QThread , QTimer
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
import os, glob , datetime

class AutoBatchController:
    def __init__(self, ui):
        self.ui = ui
        self.mt5 = MT5Manager()

        
        
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
        self.ui.param_button.clicked.connect(self.browse_param_file)
        self.ui.add_btn.clicked.connect(self.add_test_to_queue)
        self.ui.testfile_input.textChanged.connect(self.update_clean_symbol)
        self.ui.data_input.textChanged.connect(self.update_expert_list)
        self.ui.refresh_btn.clicked.connect(self.load_experts)
        self.ui.date_combo.currentTextChanged.connect(self.toggle_date_fields)
        self.ui.forward_combo.currentTextChanged.connect(self.adjust_forward_date)
        self.ui.delay_combo.currentTextChanged.connect(self.update_delay_input)
        self.ui.queue_list.itemClicked.connect(self.on_item_clicked)
        self.ui.move_up_btn.clicked.connect(self.move_up)
        self.ui.move_down_btn.clicked.connect(self.move_down)
        self.ui.dup_btn.clicked.connect(self.dup_down)
        self.ui.del_btn.clicked.connect(self.delete_test)
        self.ui.save_btn.clicked.connect(self.queue.save_queue)
        self.ui.load_btn.clicked.connect(self.queue.load_queue)
        self.ui.export_btn.clicked.connect(self.queue.export_template)
        self.ui.corr_btn.clicked.connect(lambda:self.show_correlation_popup(market="forex",period=50, symbols=None))
        self.ui.non_corr_btn.clicked.connect(lambda: self.show_quantity_popup(title="Test Pairs", text="How many pairs will be in you test list: "))
        self.ui.start_btn.clicked.connect(lambda: self.on_start_button_clicked(data_path = self.ui.data_input.text(), mt5_path =self.ui.mt5_dir_input.text(), report_path = self.ui.report_input.text() ))



    # ----------------------------
    # Browse MT5 installation path
    # ----------------------------

    def browse_mt5_dir(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.ui, "Select MT5 Terminal", "", "Executable Files (*.exe)"
        )
        if not file_path:
            return

        self.ui.mt5_dir_input.setText(file_path)

        # --- Setup worker in QThread ---
        self.thread = QThread()
        self.worker = MT5Worker(self.mt5, file_path)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_mt5_connected)
        self.worker.error.connect(lambda msg: Logger.error(msg, Exception(msg)))
        self.worker.log.connect(lambda msg: Logger.info(msg))

        # Cleanup after finish
        self.worker.finished.connect(self.thread.quit)
    
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)


        # Start thread
        self.thread.start()

        Logger.info("MT5 worker thread started")
    
    def on_mt5_connected(self, success, data_folder):
        try:
            self.ui.deposit_info = self.mt5.get_deposit()
            self.ui.deposit_input.setText(str(self.ui.deposit_info["balance"]))
            self.ui.currency_input.setText(self.ui.deposit_info["currency"])
            self.ui.leverage_input.setValue(self.ui.deposit_info["leverage"])
            # QMessageBox.information(self.ui, "MT5 Connection", "✅ MT5 connected successfully!")
            Logger.success("MT5 connected successfully")

            if data_folder:
                QMessageBox.information(self.ui, "MT5 Data Folder", f"Auto-selected Data Folder:\n{data_folder}")
                Logger.success(f"Auto-detected MT5 Data Folder: {data_folder}")
                self.ui.data_input.setText(data_folder)
                os.makedirs(os.path.join(data_folder, "Agent Finder Results"), exist_ok=True)

            def refocus():
                main_window = self.ui.window()
                main_window.showNormal()
                main_window.raise_()
                main_window.activateWindow()

            QTimer.singleShot(1000, refocus)
        except Exception as e:
            QMessageBox.critical(self.ui, "MT5 Connection", "❌ Failed to connect MT5. Please check the path.")
            Logger.error("Failed to connect MT5", e)


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

            "expert": self.ui.expert_input.currentText().strip(),
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
            "deposit": self.ui.deposit_input.text(),

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
            # first and last day of last month
            first_day_last_month = today.addMonths(-1)
            first_day_last_month = QDate(first_day_last_month.year(), first_day_last_month.month(), 1)

            last_day_last_month = QDate(first_day_last_month.year(), first_day_last_month.month(),
                                        first_day_last_month.daysInMonth())

            self.ui.date_from.setDate(first_day_last_month)
            self.ui.date_to.setDate(last_day_last_month)

        elif text == "Last year":
            # Disable pickers, set range to last year
            self.ui.date_from.setEnabled(False)
            self.ui.date_to.setEnabled(False)

            first_day_last_year = QDate(today.year() - 1, 1, 1)
            last_day_last_year = QDate(today.year() - 1, 12, 31)

            self.ui.date_from.setDate(first_day_last_year)
            self.ui.date_to.setDate(last_day_last_year)

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
        if(self.selected_queue_item_index != -1):
            print("self.selected_queue_item_index = ", self.selected_queue_item_index)
            self.queue.move_up(self.selected_queue_item_index)
            self.selected_queue_item_index = -1
        else:
            QMessageBox.information(self.ui, "List Item Not Selected",f"Please Select List Item")
    
    def move_down(self):
        if(self.selected_queue_item_index != -1):
            print("self.selected_queue_item_index = ", self.selected_queue_item_index)
            self.queue.move_down(self.selected_queue_item_index)
            self.selected_queue_item_index = -1
        else:
            QMessageBox.information(self.ui, "List Item Not Selected",f"Please Select List Item")

    def dup_down(self):
        if(self.selected_queue_item_index != -1):
            print("self.selected_queue_item_index = ", self.selected_queue_item_index)
            self.queue.duplicate_test(self.selected_queue_item_index)
            self.selected_queue_item_index = -1
        else:
            QMessageBox.information(self.ui, "List Item Not Selected",f"Please Select List Item")

    def delete_test(self):
        if(self.selected_queue_item_index != -1):
            print("self.selected_queue_item_index = ", self.selected_queue_item_index)
            self.queue.delete_test(self.selected_queue_item_index)
            self.selected_queue_item_index = -1
        else:
            QMessageBox.information(self.ui, "List Item Not Selected",f"Please Select List Item")

    def get_correlation( self,
        market="forex",
        period=50,
        symbols=None,
        output_format="csv",
        endpoint="snapshot"
    ):
       
        if symbols is None:
            symbols = ["EURUSD", "EURGBP", "AUDNZD"]  # default if nothing provided

        # Join symbols with |
        symbol_str = "|".join(symbols)

        # Build the URL
        url = f"https://www.mataf.io/api/tools/{output_format}/correl/{endpoint}/{market}/{period}/correlation.{output_format}?symbol={symbol_str}"

        # Request the URL
        response = requests.get(url)

        if response.status_code == 200:
            lines = response.text.splitlines()
            csv_data = "\n".join(lines[3:])  # drop metadata
            df = pd.read_csv(StringIO(csv_data))
            return df
        else:
            raise Exception(f"Error {response.status_code}: Unable to fetch data")
    
    
    def show_correlation_popup(self, market="forex", period=50, symbols=None):
            if getattr(self, "_correlation_busy", False):
                QMessageBox.warning(self.ui, "Please wait", "Correlation is already running...")
                return
       
            self._correlation_busy = True
            # --- Setup thread + worker ---
            self.thread = QThread()
            self.worker = CorrelationWorker(
                market=market,
                period=period,
                symbols=symbols
            )
            self.worker.moveToThread(self.thread)

            # Connect signals
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_correlation_ready)
            self.worker.error.connect(self.on_correlation_error)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.finished.connect(lambda: setattr(self, "_correlation_busy", False))


            # Start thread
            self.thread.start()
            Logger.info("Correlation worker thread started")
    def on_correlation_ready(self, df):
            try:
                corr_df = df.pivot(index="pair1", columns="pair2", values="day")

                plt.figure(figsize=(6, 4))

                sns.heatmap(
                    corr_df,
                    annot=True,
                    cmap="RdBu",  
                    center=0,       
                    vmin=-100,      
                    vmax=100,       
                    linewidths=0.5       
                )
                plt.title("Correlation Heatmap (Day)")
                plt.tight_layout()
                plt.show()

            except Exception as e:
                QMessageBox.critical(self.ui, "Error", str(e))


    def on_correlation_error(self, msg):
            QMessageBox.critical(self.ui, "Error", msg)
            Logger.error(msg, Exception(msg))

            
    def show_quantity_popup(self, title, text):
        if(self.mt5.connected):
            results = {
                "test_symbol_quantity": None,
                "strategies_count": None,
                "strategies": [],
                "symbol_type": None,
                "correlationFilter": None
            }

            # First dialog
            dialog1 = QuantityDialog(parent=self.ui, title=title, text=text)
            if dialog1.exec_() == QDialog.Accepted:
                qty1 = dialog1.get_value()
                results["test_symbol_quantity"] = qty1
                print("First quantity:", qty1)

                # Second dialog
                text = "How many strategies are you running"
                title = "Strategies Count"
                dialog2 = QuantityDialog(parent=self.ui, title=title, text=text)
                if dialog2.exec_() == QDialog.Accepted:
                    qty2 = dialog2.get_value()
                    results["strategies_count"] = qty2
                    print("Second quantity:", qty2)

                    # Loop for strategy names
                    for i in range(qty2):
                        text = f"Please Name Strategy {i+1}"
                        title = f"Strategy {i+1} Name"

                        dialog3 = TextDialog(parent=self.ui, title=title, text=text)
                        if dialog3.exec_() == QDialog.Accepted:
                            strategy_name = dialog3.get_value()
                            results["strategies"].append(strategy_name)
                            print("Strategy name:", strategy_name)
                        else:
                            print("Strategy dialog cancelled")
                            return  # stop immediately if cancelled

                    # Symbol type radio dialog
                    options = ["FX Only", "FX + Metals", "FX + Indices", "FX + Metal + Indices"]
                    radio_dialog = RadioDialog(
                        parent=self.ui,
                        title="Symbols to Test",
                        text="Which symbol do you want to include:",
                        options=options
                    )
                    if radio_dialog.exec_() == QDialog.Accepted:
                        symbol_type = radio_dialog.get_value()
                        results["symbol_type"] = symbol_type
                        print("Selected type for all strategies:", symbol_type)

                        # Correlation filter dialog
                        correlationFilterDialog = QuantityDialog(
                            parent=self.ui,
                            title="Correlation Filter",
                            text="""Enter a value between 0-100 to filter out highly correlated pairs.
                                    1) If the correlation is high (above 80) and positive then the currencies move in the same way.
                                    2) If the correlation is high (above 80) and negative then the currencies move in the opposite way.
                                    3) If the correlation is low (below 60) then the currencies don't move in the same way."""
                        )
                        if correlationFilterDialog.exec_() == QDialog.Accepted:   
                            correlationFilter = correlationFilterDialog.get_value()
                            results["correlationFilter"] = correlationFilter
                            print("Correlation Filter:", correlationFilter)
                        else:
                            print("Correlation filter dialog cancelled")
                    else:
                        print("Radio dialog cancelled")
                else:
                    print("Second dialog cancelled")
            else:
                print("First dialog cancelled")

            print("Final results:", results)
            self.non_correlated_popus_option = results

            symbols= self.get_symbols_for_option(results["symbol_type"])

            print("symbols = ",symbols)

            correlation = self.get_correlation(
                market="forex",
                period=50,
                symbols=symbols,
                output_format="csv",
                endpoint="snapshot"
            )

    
            uncorrelated_pairs = self.get_top_uncorrelated_pairs_day(
                                                                        correlation,
                                                                        results["correlationFilter"],
                                                                        results["test_symbol_quantity"]
                                                                    )

            if uncorrelated_pairs.empty:
                QMessageBox.warning(
                    self.ui,
                    "No Pairs Found",
                    f"No uncorrelated pairs found with correlation ≤ {results['correlationFilter']}."
                )
                Logger.warning(f"No uncorrelated pairs found with correlation ≤ {results['correlationFilter']}.")
                return  # exit early

            print(f"uncorrelated_pairs = {uncorrelated_pairs}")

            for _, row in uncorrelated_pairs.iterrows():
                uncorrelated_pair = f"{row['pair1']}{row['pair2']}"
                settings = {
                    "test_name": f"{uncorrelated_pair}_trend",
                    "expert": self.ui.expert_input.currentText().strip(),
                    "param_file": self.ui.param_input.text().strip(),
                    "symbol_prefix": self.ui.symbol_prefix.text().strip(),
                    "symbol_suffix": self.ui.symbol_suffix.text().strip(),
                    "symbol": uncorrelated_pair,
                    "timeframe": self.ui.timeframe_combo.currentText(),
                    "date_from": self.ui.date_from.date().toString("yyyy-MM-dd"),
                    "date_to": self.ui.date_to.date().toString("yyyy-MM-dd"),
                    "forward": self.ui.forward_combo.currentText(),
                    "delay": self.ui.delay_input.value(),
                    "model": self.ui.model_combo.currentText(),
                    "deposit": self.ui.deposit_input.text(),
                    "currency": self.ui.currency_input.text().strip(),
                    "leverage": self.ui.leverage_input.text().strip(),
                    "optimization": self.ui.optim_combo.currentText(),
                    "criterion": self.ui.criterion_input.currentText(),
                }

                if settings:
                    self.queue.add_test_to_queue(settings)
                    QMessageBox.information(self.ui, "Added", f"Test '{settings['test_name']}' added to queue.")
                    Logger.success(f"Test '{settings['test_name']}' added to queue.")
        
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

    def get_top_uncorrelated_pairs_day(self,df,correlation=60,top_n=5):
        df_filtered = df[df["pair1"] != df["pair2"]].copy()
        df_filtered["abs_day"] = df_filtered["day"].abs()
        df_filtered = df_filtered[df_filtered["abs_day"] <= correlation].sort_values("abs_day", ascending=False)

        return df_filtered[["pair1", "pair2", "day"]].head(top_n)


    def on_start_button_clicked(self, data_path, mt5_path, report_path):
        print("data_path = ",data_path)
        print("mt5_path = ",mt5_path)
        print("report_path = ",report_path)


        if not hasattr(self, "queue") or self.queue.is_empty():
            QMessageBox.warning(self.ui, "No Tests", "No tests in the queue. Please add tests first.")
            return

        QMessageBox.information(self.ui, "Starting", "Running tests in queue...")
        Logger.info("Starting queued tests...")

        # Example: run tests one by one
        while not self.queue.is_empty():
            test_settings = self.queue.get_next_test()
            self.mt5.run_test(test_settings, data_path, mt5_path, report_path)

        QMessageBox.information(self.ui, "Finished", "All tests completed.")
        Logger.success("All tests completed.")


