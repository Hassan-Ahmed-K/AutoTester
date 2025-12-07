import csv
import os
import pandas as pd
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import QFileDialog, QMessageBox,QTableWidgetItem, QHeaderView,QPushButton
from PyQt5.QtCore import Qt
from aiagentfinder.utils import Logger
from aiagentfinder.utils.workerThread import ThreadRunner
from bs4 import BeautifulSoup
import chardet
import re
import matplotlib.pyplot as plt
from functools import partial

class HtmlHunterController:
    def __init__(self, ui):
        self.ui = ui
        self.runner = ThreadRunner()
        self.main_window = self.ui.parent()
        self.auto_batch_ui = self.main_window.autoBatch_page
        self.setprocessor_ui = self.main_window.setProcessor_page


        # Internal storage for reports
        self.report_files = []          
        self.report_names = []          
        self.report_name = None         
        self.file_path = None           
        self.report_dfs = {}    
        self.export_folder_path = None        

        # Connect buttons
        self.ui.btn_html.clicked.connect(self.browse_html_folder)
        self.ui.btn_export.clicked.connect(self.browse_export_folder)
        self.ui.grouped_text.itemClicked.connect(
            lambda item: self.show_dataframe_in_table({item.text(): self.report_dfs[item.text()]})
        )
        self.ui.btn_filter.clicked.connect(self.apply_table_filter)
        self.ui.btn_export_sel.clicked.connect(self.export_selected_reports)


    def browse_html_folder(self):
        """Select HTML Reports folder and list XML/HTM report files."""
        try:
            # Determine base data folder
            data_folder = (self.auto_batch_ui.data_input.text() or "").strip()
            if not data_folder:
                print()
                data_folder = (self.setprocessor_ui.data_folder_input.text() or "").strip()

            if not data_folder or not os.path.exists(data_folder):
                QMessageBox.warning(self.ui, "Error", "Data path is not set or invalid!")
                self.logger.warning("Data path is not set or invalid!")
                return


            print("data_folder = ",data_folder)
            if data_folder != "":
                html_folder = os.path.join(data_folder, "Agent Finder Results")
            else:
                html_folder = ""

            folder_path = QFileDialog.getExistingDirectory(
                self.ui, "Select HTML Reports Folder", html_folder
            )

            if not folder_path:
                QMessageBox.warning(self.ui, "Error", "Please select a valid HTML Reports folder.")
                self.logger.warning("No folder selected for HTML Reports.")
                return

            # Set folder path in QLineEdit
            self.ui.txt_html.setText(folder_path)
            self.logger.info(f"HTML Reports folder selected: {folder_path}")

            # List all valid report files
            valid_extensions = (".xml", ".htm", ".html", ".xml.htm")
            try:
                files = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)]
            except Exception as e:
                self.logger.error(f"Failed to list files in folder: {folder_path}", e)
                QMessageBox.warning(self.ui, "Error", f"Failed to list files in folder: {folder_path}")
                return

            if not files:
                QMessageBox.warning(
                    self.ui,
                    "No Report Files Found",
                    "The selected folder does not contain any valid XML/HTM files."
                )
                self.logger.warning(f"No valid report files found in folder: {folder_path}")
                return

            # Store internally
            self.report_files = [os.path.join(folder_path, f) for f in files]
            self.report_names = files
            self.report_name = files[0]
            self.file_path = self.report_files[0]

            # Update UI list widget
            try:
                self.ui.grouped_text.clear()
                self.ui.grouped_text.addItems(files)
            except Exception as e:
                self.logger.error("Failed to update report list UI", e)

            # Log details
            self.logger.info(f"Report directory: {folder_path}")
            self.logger.info(f"Total reports found: {len(files)}")
            self.logger.info(f"Report files: {self.report_files}")
            self.logger.info(f"Default report file: {self.file_path}")

            # Read all HTML reports in background
            try:
                self.read_all_html_reports()
            except Exception as e:
                self.logger.error("Failed to read HTML reports", e)

        except Exception as e:
            self.logger.error("Unexpected error in browse_html_folder", e)
            QMessageBox.critical(self.ui, "Error", f"Unexpected error:\n{e}")

    def read_html_file(self, file_path):
        """Read HTML file content with UTF-16 fallback to UTF-8."""
        try:
            with open(file_path, "r", encoding="utf-16") as f:
                content = f.read()
                self.logger.info(f"Read HTML file successfully (UTF-16): {file_path}")
                return content
        except UnicodeError:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.logger.info(f"Read HTML file successfully (UTF-8 fallback): {file_path}")
                    return content
            except Exception as e:
                self.logger.error(f"Failed to read HTML file (UTF-8 fallback): {file_path}", e)
                return None
        except Exception as e:
            self.logger.error(f"Failed to read HTML file: {file_path}", e)
            return None

    def clean_html_text(self, html):
        """Strip HTML tags and normalize whitespace."""
        try:
            if not html:
                return ""
            # Remove HTML tags
            text = re.sub(r"<.*?>", "", html)
            # Normalize spacing
            text = re.sub(r"\s+", " ", text)
            cleaned = text.strip()
            self.logger.debug(f"Cleaned HTML text, length: {len(cleaned)}")
            return cleaned
        except Exception as e:
            self.logger.error("Error cleaning HTML text", e)
            return ""

    def extract_table_data(self, table):
        try:
            rows = table.find_all("tr")
            if not rows:
                self.logger.warning("No rows found in the table.")
                return [], ""

            # Raw HTML of all rows
            raw_html = "\n".join(str(r) for r in rows)

            # Clean text version
            clean_text = self.clean_html_text(raw_html)

            # Extract metrics or inputs from cleaned text
            try:
                clean_data = self.extract_inputs_and_metrics(clean_text)
                self.logger.debug(f"Extracted metrics from table: {clean_data}")
            except Exception as e:
                clean_data = ""
                self.logger.error("Failed to extract inputs and metrics from table", e)

            # Extract structured row/column data
            data = []
            for row in rows:
                try:
                    cols = row.find_all(["td", "th"])
                    cols = [ele.get_text(strip=True) for ele in cols]
                    if cols:
                        data.append(cols)
                except Exception as e:
                    self.logger.warning(f"Failed to parse row: {row}", e)

            return data, clean_data

        except Exception as e:
            self.logger.error("Failed to extract table data", e)
            return [], ""

    def extract_inputs_and_metrics(self, text):
 
        data = {}

        try:
            # ---------------- Extract Inputs ----------------
            input_patterns = {
                "AllowNewSequence": r"AllowNewSequence\s*=\s*(\w+)",
                "StrategyDescription": r"StrategyDescription\s*=\s*([^\s]+)",
                "ColorScheme": r"ColorScheme\s*=\s*(\d+)",
                "MAGIC_NUMBER": r"MAGIC_NUMBER\s*=\s*(\d+)",
                "TradeComment": r"TradeComment\s*=\s*([^\s]+)",
                "UseRandomEntryDelay": r"UseRandomEntryDelay\s*=\s*(\w+)",
                "MaxSpreadPips": r"MaxSpreadPips\s*=\s*([\d\.]+)",
                "apiKey": r"apiKey\s*=\s*([A-Za-z0-9]+)",
                "CustomTradingTimes": r"CustomTradingTimes\s*=\s*(\w+)",
                "MondayStartEnd": r"MondayStartEnd\s*=\s*([\d:]+-[\d:]+)",
                "LotSize": r"LotSize\s*=\s*([\d\.]+)",
                "MaxLots": r"MaxLots\s*=\s*([\d\.]+)",
                "MaxSequencesPerDay": r"MaxSequencesPerDay\s*=\s*(\d+)",
            }

            for key, pattern in input_patterns.items():
                try:
                    m = re.search(pattern, text)
                    if m:
                        data[key] = m.group(1).strip()
                except Exception as e:
                    self.logger.warning(f"Failed to extract input {key}: {e}")

            # ---------------- Extract Metrics ----------------
            metrics_patterns = {
                "Profit": r"Total Net Profit:\s*([-\d\s]+\.\d+)",
                "PF": r"Profit Factor:\s*([\d\.]+)",
                "RF": r"Recovery Factor:\s*([\d\.]+)",
                "Avg Win": r"Average profit trade:\s*([-\d\.]+)",
                "Avg Loss": r"Average loss trade:\s*([-\d\.]+)",
                "Trade Vol": r"Total Trades:\s*(\d+)",
                "Max DD": r"Balance Drawdown Maximal:\s*([\d\.]+)",
                "Max Drawdown": r"Equity Drawdown Maximal:\s*([\d\.]+)",
                "Max Hold": r"Maximal position holding time:\s*(\d{1,3}:\d{2}:\d{2})",
                "Avg Hold": r"Average position holding time:\s*(\d{1,3}:\d{2}:\d{2})",
            }

            for key, pattern in metrics_patterns.items():
                try:
                    m = re.search(pattern, text)
                    if m:
                        data[key] = m.group(1).replace(" ", "")
                except Exception as e:
                    self.logger.warning(f"Failed to extract metric {key}: {e}")

            self.logger.info(f"Extracted Inputs and Metrics: {data}")

        except Exception as e:
            self.logger.error("Failed to extract inputs and metrics from text", e)

        return data

    def save_to_csv(self, filepath, rows):
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)  # ensure folder exists

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

            self.logger.success(f"Saved CSV file: {filepath}")

        except Exception as e:
            self.logger.error(f"Failed to save CSV file: {filepath}", e)

    def process_table_2(self, table):

        orders_data = []
        deals_data = []

        capture_orders = False
        capture_deals = False

        expecting_orders_header = False
        expecting_deals_header = False

        try:
            rows = table.find_all("tr")

            for row in rows:
                try:
                    cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
                    if not any(cells):
                        continue

                    row_text = "".join(cells).lower()

                    # Detect sections
                    if "orders" == row_text or (len(cells) == 1 and "orders" in cells[0].lower()):
                        self.logger.debug("Found Orders Section")
                        capture_orders = True
                        capture_deals = False
                        expecting_orders_header = True
                        continue

                    if "deals" == row_text or (len(cells) == 1 and "deals" in cells[0].lower()):
                        self.logger.debug("Found Deals Section")
                        capture_orders = False
                        capture_deals = True
                        expecting_deals_header = True
                        continue

                    # Capture rows
                    if capture_orders:
                        orders_data.append(cells)
                        expecting_orders_header = False
                    elif capture_deals:
                        deals_data.append(cells)
                        expecting_deals_header = False

                except Exception as inner_e:
                    self.logger.error(f"Error processing row: {cells}", inner_e)

            self.logger.info(f"Processed table: {len(orders_data)} orders, {len(deals_data)} deals")
            return orders_data, deals_data

        except Exception as e:
            self.logger.error("Failed to process table", e)
            return [], []

    def read_all_html_reports(self):
        """Parse all XML/HTML report files in a background thread."""
        
        if not self.report_files:
            Logger.error("❌ No report files found to process.")
            QMessageBox.warning(self.ui, "Warning", "No report files found to process.")
            return

        Logger.info(f"📂 Starting parsing for {len(self.report_files)} files...")

        def task():
            dfs = {}

            for file_path in self.report_files:
                report_name = os.path.basename(file_path)
                ext = report_name.lower()

                if ext.endswith((".htm", ".html", ".xml.htm")):
                    Logger.info(f"🔍 Parsing HTML report: {report_name}")

                    content = self.read_html_file(file_path)  # fixed variable
                    if not content:
                        Logger.warning(f"No content found in {report_name}")
                        continue

                    soup = BeautifulSoup(content, "html.parser")
                    tables = soup.find_all("table")

                    html_tables = []  # store extracted tables if needed

                    # ---------- Table 1 ----------
                    if len(tables) >= 1:
                        Logger.info("Processing Table 1...")
                        t1_data = self.extract_table_data(tables[0])

                        print("-----------------------------------------------------------------")
                        print("t1_data = ",t1_data)
                        print("-----------------------------------------------------------------")

                        
                        html_tables.append(t1_data)

                    # ---------- Table 2 ----------
                    if len(tables) >= 2:
                        Logger.info("Processing Table 2...")
                        orders, deals = self.process_table_2(tables[1])
                        orders = pd.DataFrame(orders)
                        deals = pd.DataFrame(deals)
                        try:
                        # If first column name is int → wrong table → header is on row 0
                            if isinstance(deals.columns[0], int):
                                Logger.info("🔧 Fixing deals table: detected numeric columns, using row 0 as header.")

                                new_header = deals.iloc[0]
                                deals = deals[2:]
                                deals.columns = new_header
                                deals = deals.reset_index(drop=True)

                            if isinstance(orders.columns[0], int):

                                new_header = orders.iloc[0]
                                print("new_header = ", new_header)
                                orders = orders[2:]
                                orders.columns = new_header
                                orders = orders.reset_index(drop=True)

                            # Clean column names finally
                            deals.columns = [str(col).strip() for col in deals.columns]
                            orders.columns = [str(col).strip() for col in orders.columns]

                            orders["Open Time"] = pd.to_datetime(orders["Open Time"])
                            deals["Time"] = pd.to_datetime(deals["Time"])

                            merged_df = orders.merge(
                                                        deals,
                                                        left_on="Open Time",
                                                        right_on="Time",
                                                        how="inner"
                                                    )


                        except Exception as e:
                           Logger.error(f"❌ Failed while fixing deals header: {e}")
                        html_tables.append(merged_df)
                    else:
                        Logger.warning("Table 2 not found!")

                    if html_tables:
                        dfs[report_name] = html_tables
                        Logger.success(f"Parsed HTML report: {report_name} ({len(html_tables)} tables)")
                    else:
                        Logger.warning(f"No tables found in HTML report: {report_name}")

            return {"dataframes": dfs}

        # ---------- Callbacks ----------
        def on_done(result):
            if not isinstance(result, dict):
                Logger.error("❌ Invalid parse result.")
                QMessageBox.warning(self.ui, "Warning", "Parsing completed, but no valid data returned.")
                return

            self.report_dfs = result.get("dataframes", {})
            if not self.report_dfs:
                Logger.error("❌ No valid DataFrames extracted.")
                QMessageBox.warning(self.ui, "Warning", "No tables found in HTML reports.")
                return

            Logger.info(f"📘 Successfully parsed {len(self.report_dfs)} reports.")
            QMessageBox.information(self.ui, "Success",
                                    f"✅ Parsed {len(self.report_dfs)} XML/HTML reports successfully!")
            
            if self.report_dfs:
                first_report_name = next(iter(self.report_dfs.keys()))
                Logger.info(f"📂 Auto-loading first report: {first_report_name}")
                self.log_to_ui(f"📂 Auto-loading first report: {first_report_name}")
                self.show_dataframe_in_table({first_report_name: self.report_dfs[first_report_name]})
                self.ui.grouped_text.setCurrentRow(0)

            # self.fill_table_threaded()

        def on_error(err):
            Logger.error(f"❌ Parsing failed: {err}")
            QMessageBox.critical(self.ui, "Error", f"❌ Parsing Failed:\n{err}")

        # ---------- Run in background thread ----------
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)

    def browse_export_folder(self):
        try:
            print("self.auto_batch_ui.data_input.text() = ",self.auto_batch_ui.data_input.text())
            data_folder = (self.auto_batch_ui.data_input.text() or "").strip()
            if not data_folder:
                print()
                data_folder = (self.setprocessor_ui.data_folder_input.text() or "").strip()

            if data_folder != "":
                export_folder = os.path.join(data_folder, "Agent Finder Results")
            else:
                export_folder = ""
        


            export_folder_path = QFileDialog.getExistingDirectory(
                self.ui, "Select HTML Reports Folder", export_folder
            )

            if not export_folder_path:
                QMessageBox.warning(self.ui, "Error", "❌ Please select a valid HTML Reports folder.")
                Logger.warning("No folder selected for HTML Reports.")
                return

            self.export_folder_path = export_folder_path
            self.ui.txt_export.setText(export_folder_path)
            Logger.success(f"Export folder selected: {export_folder_path}")
        except Exception as e:
            Logger.error(f"Error while selecting export folder: {e}")

            QMessageBox.critical(self.ui, "Error", f"❌ Failed to select export folder.\nError: {str(e)}")
        
    def safe_float(self,x):
        try:
            if x is None or x == "" or str(x).strip() == "":
                return 0.0
            return float(str(x).replace(",", "").strip())
        except:
            return 0.0

    def show_dataframe_in_table(self, report_dict: dict):
            """
            Populate the QTableWidget with merged clean_data and deals DataFrame in a background thread.
            """

            print("show_dataframe_in_table")
            
            if not report_dict:
                Logger.warning("❌ No report data passed.")
                return

            report_name, tables = next(iter(report_dict.items()))
            properties = tables[0]  
            orders_deals_table = tables[1]     
            # deals = tables[2]     
            

            def task():
                try:
                    print("---------------------------------------------------------------")
                    print("properties.keys() = ",properties.keys())
                    print("properties.values() = ",properties.values())
                    print("---------------------------------------------------------------")


                    column_mapping = {
                        "Profit": "Total Net Profit",
                        "Max DD": "Equity Drawdown Maximal",
                        "RF": "Recovery Factor",
                        "PF": "Profit Factor",
                        "Avg Win": "Average profit trade",
                        "Avg Loss": "Average loss trade",
                        "Trade Vol": "Total Trades",
                        "Lot Size": "LotSize",
                        "Peak Lot Size": "MaxLots",
                        "Max Sq No": "MaxSequencesPerDay",
                        "Max Lots": "MaxLots", 
                        "Lot Expo": "LotSizeExponent",
                        "Max Hold": "Maximal position holding time",
                        "Avg Hold": "Average position holding time",
                        "Graph": "Graph",
                        "Overview": "Overview"
                    }

                    df = pd.DataFrame([properties])
                    df.to_csv("curren_Selectection.csv", index=False)

                    for col in column_mapping.values():
                        if col not in df.columns:
                            df[col] = ""

                    self.filtered_df = df[list(column_mapping.values())].rename(
                        columns={v: k for k, v in column_mapping.items()}
                    ).fillna("").reset_index(drop=True)

                    table_data = []
                    for _, row in self.filtered_df.iterrows():
                        table_data.append([("" if pd.isna(val) else str(val)) for val in row])

                    headers = self.filtered_df.columns.tolist()
                    return headers, table_data

                except Exception as e:
                    raise e

            def on_done(result):
                if not result:
                    Logger.error("❌ No table data returned from thread.")
                    return

                headers, table_data = result
                table = self.ui.middle_message
                table.clear()
                table.setRowCount(0)
                table.setColumnCount(len(headers))
                table.setHorizontalHeaderLabels(headers)

                for row_idx, row_values in enumerate(table_data):
                    table.insertRow(row_idx)
                    for col_idx, value in enumerate(row_values):
                        key = headers[col_idx]
                        if key == "Graph":
                            btn = QPushButton("Open")
                       
                            btn.clicked.connect(partial(self.show_graph, row_idx))
                            table.setCellWidget(row_idx, col_idx, btn)
                            
                            continue

                        if key == "Overview":
                            btn = QPushButton("Open")
                            btn.clicked.connect(partial(self.show_overview, row_idx))
                            table.setCellWidget(row_idx, col_idx, btn)
                            continue
                        item = QTableWidgetItem(value)
                        item.setTextAlignment(Qt.AlignCenter)
                        table.setItem(row_idx, col_idx, item)

                header_widget = table.horizontalHeader()
                header_widget.setSectionResizeMode(QHeaderView.Stretch)
                self.log_to_ui(f"✅ Table populated successfully with {len(table_data)} rows and {len(headers)} columns.")
                Logger.info(f"✅ Table populated successfully with {len(table_data)} rows and {len(headers)} columns.")

            def on_error(err):
                Logger.error(f"❌ Failed to populate table: {err}")
                QMessageBox.critical(self.ui, "Error", f"Failed to populate table:\n{str(err)}")


            self.runner = ThreadRunner(self.ui)
            self.runner.on_result = on_done
            self.runner.on_error = on_error
            self.runner.run(task)

    def show_graph(self, row_data):
            """Generate graph using thread runner with safe extraction."""

            def task():
                try:
                    row_idx = int(row_data)

                    row = self.filtered_df.iloc[row_idx]

                    profit = self.safe_float(row.get("Profit", 0))
                    max_dd = self.safe_float(row.get("Max DD", 0))
                    pf = self.safe_float(row.get("PF", 0))
                    rf = self.safe_float(row.get("RF", 0))

                    avg_win = self.safe_float(row.get("Avg Win", 0)) * profit
                    avg_loss = self.safe_float(row.get("Avg Loss", 0)) * profit

                    return {
                        "profit": profit,
                        "max_dd": max_dd,
                        "pf": pf,
                        "rf": rf,
                        "avg_win": avg_win,
                        "avg_loss": avg_loss,
                        "title": row.get("Name", "Report Graph")   # FIX HERE
                    }

                except Exception as e:
                    raise Exception(f"Graph Thread Failed: {e}")


            def on_done(m):
                try:
                    print(m)
                    x = ["Profit", "Max DD", "PF", "RF", "AvgWin", "AvgLoss"]
                    y = [m["profit"], m["max_dd"], m["pf"], m["rf"], m["avg_win"], m["avg_loss"]]


                    fig = plt.figure(figsize=(6, 4))
                    plt.plot(x, y, marker="o")
                    plt.grid(True)
                    plt.title(m["title"])
                    plt.tight_layout()
                    plt.show(block=False)


                except Exception as e:
                    QMessageBox.critical(self.ui, "Graph Error", str(e))

                self.active_runners.remove(runner)

            def on_error(err):
                QMessageBox.critical(self.ui, "Thread Error", str(err))
                self.active_runners.remove(runner)

            runner = ThreadRunner(self.ui)
            if not hasattr(self, "active_runners"):
                self.active_runners = []

            self.active_runners.append(runner)
            runner.on_result = on_done
            runner.on_error = on_error
            runner.run(task)

    def show_overview(self, row_data):
            """Open overview dialog using thread runner with safe parsing."""



            def task():
                try:
                    # Safely extract all values from row_data
                    profit = self.safe_float(row_data.get("Profit", 0))
                    max_dd = self.safe_float(row_data.get("Max DD", 0))
                    trades = int(self.safe_float(row_data.get("Trades", 0)))
                    pf = self.safe_float(row_data.get("PF", 0))
                    rf = self.safe_float(row_data.get("RF", 0))
                    win_rate = self.safe_float(row_data.get("Win%", 0))

                    # Your added formulas
                    avg_win = self.safe_float(row_data.get("Avg Win", 0)) * profit
                    avg_loss = self.safe_float(row_data.get("Avg Loss", 0)) * profit

                    return {
                        "title": row_data.get("Name", "Overview"),
                        "profit": profit,
                        "max_dd": max_dd,
                        "pf": pf,
                        "rf": rf,
                        "trades": trades,
                        "win_rate": win_rate,
                        "avg_win": avg_win,
                        "avg_loss": avg_loss
                    }

                except Exception as e:
                    raise Exception(f"Overview Thread Failed: {e}")

            def on_done(m):
                try:
                    text = (
                        f"<b>Report Overview</b><br><br>"
                        f"Profit: {m['profit']}<br>"
                        f"Max Drawdown: {m['max_dd']}<br>"
                        f"Profit Factor (PF): {m['pf']}<br>"
                        f"Recovery Factor (RF): {m['rf']}<br>"
                        f"Trades: {m['trades']}<br>"
                        f"Win Rate: {m['win_rate']}%<br><br>"
                        f"Avg Win (scaled): {m['avg_win']}<br>"
                        f"Avg Loss (scaled): {m['avg_loss']}<br>"
                    )

                    dlg = QMessageBox(self.ui)
                    dlg.setWindowTitle(m["title"])
                    dlg.setText(text)
                    dlg.exec_()

                except Exception as e:
                    QMessageBox.critical(self.ui, "Overview Error", str(e))

                self.active_runners.remove(runner)

            def on_error(err):
                QMessageBox.critical(self.ui, "Thread Error", f"Failed to load overview:\n{err}")
                self.active_runners.remove(runner)

            # ----- ThreadRunner Setup -----
            runner = ThreadRunner(self.ui)
            if not hasattr(self, "active_runners"):
                self.active_runners = []

            self.active_runners.append(runner)
            runner.on_result = on_done
            runner.on_error = on_error
            runner.run(task)
   
    def apply_table_filter(self):
        try:
            # --- 1. Safe filter reads ---
            max_dd    = self.safe_float(self.ui.txt_drawdown.text() or float("inf"))
            min_rf    = self.safe_float(self.ui.txt_recovery.text() or 0)
            min_pf    = self.safe_float(self.ui.txt_profit.text() or 0)
            target_dd = self.safe_float(self.ui.txt_target.text() or float("inf"))

            if not self.report_dfs:
                QMessageBox.warning(self.ui, "No Reports", "No reports loaded.")
                return

            # --- 2. Get selected report ---
            selected_item = self.ui.grouped_text.currentItem()
            if not selected_item:
                QMessageBox.warning(self.ui, "No Report Selected", "Select a report first.")
                return

            report_name = selected_item.text()
            clean_data, orders, deals = self.report_dfs.get(report_name, (None, None, None))

            if deals is None or deals.empty:
                QMessageBox.warning(self.ui, "No Deals", "This report has no deals.")
                return

            # --- 3. Convert clean_data to dict ---
            if isinstance(clean_data, pd.DataFrame):
                clean = clean_data.to_dict(orient="records")[0]
            elif isinstance(clean_data, pd.Series):
                clean = clean_data.to_dict()
            elif isinstance(clean_data, dict):
                clean = clean_data
            else:
                clean = {}

            # --- 4. Merge static clean_data + dynamic deal values ---
            merged_rows = []
            for _, deal_row in deals.iterrows():

                row = dict(clean)

                # Profit
                profit = self.safe_float(deal_row.get("Profit", 0))
                row["Profit"] = profit

                # Static metrics
                row["Max DD"] = (self.safe_float(clean.get("Max DD", 0))/100)*profit
                row["RF"]     = self.safe_float(clean.get("RF", 0))
                row["PF"]     = self.safe_float(clean.get("PF", 0))

                # --- Custom calculations ---
                row["Avg Win"]  = self.safe_float(clean.get("Avg Win", 0)) * profit
                row["Avg Loss"] = self.safe_float(clean.get("Avg Loss", 0)) * profit

                merged_rows.append(row)

            df = pd.DataFrame(merged_rows)

            # Force numeric
            for col in ["Max DD", "RF", "PF", "Profit", "Avg Win", "Avg Loss"]:
                if col in df:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            # --- 5. Apply filters ---
            filtered_df = df[
                (df["Max DD"] <= max_dd) &
                (df["RF"] >= min_rf) &
                (df["PF"] >= min_pf) &
                (df["Max DD"] <= target_dd)
            ]

            columns_to_show = [
                    "Profit", "Max DD", "RF", "PF",
                    "Avg Win", "Avg Loss", "Trade Vol",
                    "LotSize", "MaxLots", "MaxSequencesPerDay",
                    "Lot Expo", "Max Hold", "Avg Hold",
                    "Graph", "Overview"
                ]
            filtered_df = filtered_df[[col for col in columns_to_show if col in filtered_df.columns]]


            # --- 6. ADD Graph + Overview columns so buttons appear ---
            filtered_df["Graph"] = "Open"
            filtered_df["Overview"] = "Open"

            # --- 7. Show table ---
            self.log_to_ui(f"Filtered {filtered_df.shape[0]} rows")
            self.populate_qtable_from_df(filtered_df)

        except Exception as e:
            Logger.error(f"Filter error: {e}")
            QMessageBox.critical(self.ui, "Error", f"Filtering failed:\n{e}")

    def populate_qtable_from_df(self, df):
        table = self.ui.middle_message
        table.clear()

        if df is None or df.empty:
            table.setRowCount(0)
            table.setColumnCount(0)
            self.log_to_ui("Empty df — table cleared")
            Logger.info("Empty df — table cleared")
            return

        columns = [str(c) for c in df.columns.tolist()]

        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setRowCount(len(df))

        for row_idx, (_, row) in enumerate(df.iterrows()):
            for col_idx, col_name in enumerate(columns):

                # --- Graph Button ---
                if col_name.lower() == "graph":
                    btn = QPushButton("Open")
                    btn.clicked.connect(partial(self.show_graph, row_idx))
                    table.setCellWidget(row_idx, col_idx, btn)
                    continue

                # --- Overview Button ---
                if col_name.lower() == "overview":
                    btn = QPushButton("Open")
                    btn.clicked.connect(partial(self.show_overview, row_idx))
                    table.setCellWidget(row_idx, col_idx, btn)
                    continue

                # --- Normal cell ---
                value = "" if pd.isna(row[col_name]) else str(row[col_name])
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_idx, col_idx, item)

        # Stretch columns
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.log_to_ui(f"Table populated with {len(df)} rows and {len(columns)} cols")
        Logger.info(f"Table populated with {len(df)} rows and {len(columns)} cols")

    def log_to_ui(self, message: str):
        """
        Append a message to the bottom_message QTextEdit and scroll to the bottom.
        """
        if hasattr(self.ui, "log_box") and self.ui.log_box is not None:
            # Append message with newline
            self.ui.log_box.append(message)
            
            # Ensure the last message is visible
            self.ui.log_box.verticalScrollBar().setValue(
                self.ui.log_box.verticalScrollBar().maximum()
            )
        else:
            print("⚠️ bottom_message widget not found. Message:", message)

    def export_selected_reports(self):
        try:
            Logger.info("Starting export_selected_reports...")

            # Validate export folder
            if not os.path.isdir(self.export_folder_path):
                raise Exception(f"Export folder does not exist: {self.export_folder_path}")

            # Validate dataframe
            if self.filtered_df is None or self.filtered_df.empty:
                raise Exception("Filtered DataFrame is empty — nothing to export.")

            file_path = os.path.join(self.export_folder_path, self.report_name + ".csv")
            Logger.info(f"Exporting report to: {file_path}")

            # Save CSV
            self.filtered_df.to_csv(file_path, index=False)
            Logger.info("Report export successful.")

            QMessageBox.information(self.ui, "Export Complete", f"Report exported to:\n{file_path}")

        except Exception as e:
            Logger.error(f"Export failed: {e}")
            QMessageBox.critical(self.ui, "Export Error", str(e))

                


            
