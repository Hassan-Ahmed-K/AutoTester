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

from extract_tables import clean_html_text, save_to_csv
class HtmlHunterController:
    def __init__(self, ui):
        self.ui = ui
        self.runner = ThreadRunner()
        self.auto_batch_ui = self.ui.parent().autoBatch_page
        self.setprocessor_ui = self.ui.parent().setProcessor_page


        # Internal storage for reports
        self.report_files = []          
        self.report_names = []          
        self.report_name = None         
        self.file_path = None           
        self.report_dfs = {}            

        # Connect buttons
        self.ui.btn_html.clicked.connect(self.browse_html_folder)
        self.ui.btn_export.clicked.connect(self.browse_export_folder)
        self.ui.grouped_text.itemClicked.connect(
            lambda item: self.show_dataframe_in_table({item.text(): self.report_dfs[item.text()]})
        )
        self.ui.btn_filter.clicked.connect(self.apply_table_filter)

    def browse_html_folder(self):
        """Select HTML Reports folder and list XML/HTM report files."""
        try:
            data_folder = (self.auto_batch_ui.data_input.text() or "").strip()
            if not data_folder:
                data_folder = (self.setprocessor_ui.data_folder_input.text() or "").strip()
            if not data_folder or not os.path.exists(data_folder):
                QMessageBox.warning(self.ui, "Error", "Data path is not set or invalid!")
                Logger.warning("Data path is not set or invalid!")
                return

            # Default HTML Reports folder
            html_folder = os.path.join(data_folder, "Agent Finder Results")
            folder_path = QFileDialog.getExistingDirectory(
                self.ui, "Select HTML Reports Folder", html_folder
            )

            if not folder_path:
                QMessageBox.warning(self.ui, "Error", "❌ Please select a valid HTML Reports folder.")
                Logger.warning("No folder selected for HTML Reports.")
                return

            # Set folder path in QLineEdit
            self.ui.txt_html.setText(folder_path)
            Logger.success(f"HTML Reports folder selected: {folder_path}")

            # List all valid files
            valid_extensions = (".xml", ".htm", ".html", ".xml.htm")
            files = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)]

            if not files:
                QMessageBox.warning(
                    self.ui,
                    "No Report Files Found",
                    "The selected folder does not contain any valid XML/HTM files."
                )
                return

            # Store internally
            self.report_files = [os.path.join(folder_path, f) for f in files]
            self.report_names = files
            self.report_name = files[0]
            self.file_path = self.report_files[0]

            # Update UI list widget
            self.ui.grouped_text.clear()
            self.ui.grouped_text.addItems(files)

            Logger.info(f"📂 Report directory: {folder_path}")
            Logger.info(f"📄 Total reports found: {len(files)}")
            Logger.info(f"📄 Report files: {self.report_files}")
            Logger.info(f"📄 Default report file: {self.file_path}")

            # Read all HTML reports in background
            self.read_all_html_reports()
                
    
            

        except Exception as e:
            Logger.error(f"Error while selecting HTML Reports folder: {e}")
            QMessageBox.critical(self.ui, "Error", f"❌ Failed to select HTML Reports folder.\nError: {str(e)}")

    def read_html_file(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-16") as f:
                return f.read()
        except UnicodeError:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    def clean_html_text(self,html):
        # remove tags
        text = re.sub(r"<.*?>", "", html)
        # normalize spacing
        text = re.sub(r"\s+", " ", text)
        return text.strip()


    def extract_table_data(self,table):
        rows = table.find_all("tr")
        raw_html = "\n".join(str(r) for r in rows)

        clean_text = self.clean_html_text(raw_html)

        clean_data= self.extract_inputs_and_metrics(clean_text)

        data = []
        for row in rows:
            cols = row.find_all(["td", "th"])
            cols = [ele.get_text(strip=True) for ele in cols]
            if cols:
                data.append(cols)

        return data , clean_data
    def extract_inputs_and_metrics(self,text):
        data = {}

        # Inputs
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
            m = re.search(pattern, text)
            if m:
                data[key] = m.group(1).strip()

        # Metrics
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
            m = re.search(pattern, text)
            if m:
                data[key] = m.group(1).replace(" ", "")  # remove spaces in numbers
        print("Extracted Inputs and Metrics:"  , data)
        return data

    def save_to_csv(self,filepath, rows):
        # filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        print(f"Saved {filepath}")

    def process_table_2(self,table):
        rows = table.find_all("tr")
        
        orders_data = []
        deals_data = []
        
        current_section = None
        # State machine: None -> FOUND_ORDERS -> ORDERS_HEADER -> ORDERS_DATA -> FOUND_DEALS -> DEALS_HEADER -> DEALS_DATA

        capture_orders = False
        capture_deals = False
        
        # To handle the "next row is header" logic
        expecting_orders_header = False
        expecting_deals_header = False
        
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
            
            # Check for empty rows that might be spacers
            if not any(cells):
                continue
                
            # Check for Section Headers
            # The snippet shows the "Orders" text is in a <th> with colspan, or just a cell with "Orders"
            # We'll check if "Orders" is the only substantial text or if it's explicitly "Orders"
            
            # Join cells to check content easily
            row_text = "".join(cells).lower()
            
            if "orders" == row_text or (len(cells) == 1 and "orders" in cells[0].lower()):
                print("Found Orders Section")
                capture_orders = True
                capture_deals = False
                expecting_orders_header = True
                continue
                
            if "deals" == row_text or (len(cells) == 1 and "deals" in cells[0].lower()):
                print("Found Deals Section")
                capture_orders = False
                capture_deals = True
                expecting_deals_header = True
                continue
                
            # Capture Data
            if capture_orders:
                if expecting_orders_header:
                    orders_data.append(cells) # Add header
                    expecting_orders_header = False
                else:
                    orders_data.append(cells)
                    
            elif capture_deals:
                if expecting_deals_header:
                    deals_data.append(cells)
                    expecting_deals_header = False
                else:
                    deals_data.append(cells)

        return orders_data, deals_data
    

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
                        t1_data, clean_data = self.extract_table_data(tables[0])
                        # self.save_to_csv(filepath, t1_data)
                        html_tables.append(clean_data)

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

                                # row 0 contains the actual header names
                                new_header = deals.iloc[0]

                                # drop that row
                                deals = deals[2:]

                                # replace column names with real header
                                deals.columns = new_header

                                # reset index
                                deals = deals.reset_index(drop=True)

                            # Clean column names finally
                            deals.columns = [str(col).strip() for col in deals.columns]

                        except Exception as e:
                           Logger.error(f"❌ Failed while fixing deals header: {e}")
    
                        # self.save_to_csv(filepath, orders)
                        # self.save_to_csv(filepath, deals)
                        html_tables.append(orders)
                        html_tables.append(deals)
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
            print("Report DataFrames:", self.report_dfs)
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
            data_folder = (self.auto_batch_ui.data_input.text() or "").strip()
            if not data_folder:
                data_folder = (self.setprocessor_ui.data_folder_input.text() or "").strip()
            if not data_folder or not os.path.exists(data_folder):
                QMessageBox.warning(self.ui, "Error", "Data path is not set or invalid!")
                Logger.warning("Data path is not set or invalid!")
                return
            
            export_folder = os.path.join(data_folder, "Agent Finder Results")


            export_folder_path = QFileDialog.getExistingDirectory(
                self.ui, "Select HTML Reports Folder", export_folder
            )

            if not export_folder_path:
                QMessageBox.warning(self.ui, "Error", "❌ Please select a valid HTML Reports folder.")
                Logger.warning("No folder selected for HTML Reports.")
                return


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
            
            if not report_dict:
                Logger.warning("❌ No report data passed.")
                return

            report_name, tables = next(iter(report_dict.items()))
             # Assuming tables are stored as DataFrames:
            clean_data = tables[0]  # DataFrame with inputs & metrics
            orders = tables[1]      # DataFrame of orders (if needed)
            deals = tables[2]       # DataFrame of deals
            
            
            try:
                # If first column name is int → wrong table → header is on row 0
                if isinstance(deals.columns[0], int):
                    Logger.info("🔧 Fixing deals table: detected numeric columns, using row 0 as header.")

                    # row 0 contains the actual header names
                    new_header = deals.iloc[0]

                    # drop that row
                    deals = deals[2:]

                    # replace column names with real header
                    deals.columns = new_header

                    # reset index
                    deals = deals.reset_index(drop=True)

                # Clean column names finally
                deals.columns = [str(col).strip() for col in deals.columns]

            except Exception as e:
                Logger.error(f"❌ Failed while fixing deals header: {e}")
                return
            if len(tables) < 3:
                Logger.warning(f"❌ Report {report_name} missing required tables.")
                return


            if deals is None :
                Logger.warning(f"⚠️ No deals found in report {report_name}.")
                return
            if clean_data is None :
                Logger.info("⚠️ No data to display")
                return

            Logger.info(f"📂 Preparing table for report: {report_name} ({len(deals)} deals)")

            if clean_data is None or deals is None or deals.empty:
                Logger.info("⚠️ No data to display.")
                self.ui.table.clear()
                self.ui.table.setRowCount(0)
                self.ui.table.setColumnCount(0)
                return

            def task():
                try:
                    # Merge clean_data (static values) with each row in deals
                    merged_rows = []
                    for _, deal_row in deals.iterrows():
                        row_data = {}
                        # Copy static values from clean_data
                        for k, v in clean_data.items():
                            row_data[k] = v
                        # Dynamic values from deals
                        profit = self.safe_float(deal_row.get("Profit", 0))
                        row_data["Profit"] = profit
                        row_data["Avg Win"] = self.safe_float(clean_data.get("Avg Win", 0)) * profit
                        row_data["Avg Loss"] = self.safe_float(clean_data.get("Avg Loss", 0)) * profit
                        # You can add other deal-specific columns if needed
                        merged_rows.append(row_data)

                    # Convert to DataFrame
                    df = pd.DataFrame(merged_rows)

                    # Ensure all mapped columns exist
                    column_mapping = {
                        "Profit": "Profit",
                        "Max DD": "Max DD",
                        "RF": "RF",
                        "PF": "PF",
                        "Avg Win": "Avg Win",
                        "Avg Loss": "Avg Loss",
                        "Trade Vol": "Trade Vol",
                        "Lot Size": "LotSize",
                        "Peak Lot Size": "MaxLots",
                        "Max Sq No": "MaxSequencesPerDay",
                        "Max Lots": "MaxLots", 
                        "Lot Expo": "Lot Expo",
                        "Max Hold": "Max Hold",
                        "Avg Hold": "Avg Hold",
                        "Graph": "Graph",
                        "Overview": "Overview"
                    }

                    for col in column_mapping.values():
                        if col not in df.columns:
                            df[col] = ""

                    filtered_df = df[list(column_mapping.values())].rename(
                        columns={v: k for k, v in column_mapping.items()}
                    ).fillna("").reset_index(drop=True)

                    table_data = []
                    for _, row in filtered_df.iterrows():
                        table_data.append([("" if pd.isna(val) else str(val)) for val in row])

                    headers = filtered_df.columns.tolist()
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
                            btn.setMaximumSize(60, 60)
                       
                            btn.clicked.connect(partial(self.show_graph, row_idx))
                            table.setCellWidget(row_idx, col_idx, btn)
                            
                            continue

                        if key == "Overview":
                            btn = QPushButton("Open")
                            btn.setMaximumSize(60, 60)
                            btn.clicked.connect(partial(self.show_overview, row_idx))
                            table.setCellWidget(row_idx, col_idx, btn)
                            continue
                        item = QTableWidgetItem(value)
                        item.setTextAlignment(Qt.AlignCenter)
                        table.setItem(row_idx, col_idx, item)

                header_widget = table.horizontalHeader()
                header_widget.setSectionResizeMode(QHeaderView.Stretch)
                Logger.info(f"✅ Table populated successfully with {len(table_data)} rows and {len(headers)} columns.")

            def on_error(err):
                Logger.error(f"❌ Failed to populate table: {err}")
                QMessageBox.critical(self.ui, "Error", f"Failed to populate table:\n{str(err)}")

            self.runner = ThreadRunner(self.ui)
            self.runner.on_result = on_done
            self.runner.on_error = on_error
            self.runner.run(task)




    def show_graph(self, row_index):
        try:
            row_index = int(row_index)
            report_key = list(self.report_dfs.keys())[0]  # first report for simplicity
            df = self.report_dfs[report_key]

            if df is None or df.empty:
                Logger.warning(f"⚠️ Report {report_key} is empty. Cannot generate graph.")
                QMessageBox.warning(self.ui, "Graph Warning", f"No data available for {report_key}.")
                return

            def task():
                try:
                    # Extract metrics from the specific row
                    row = df.iloc[row_index]
                    profit = float(row.get("Profit", 0) or 0)
                    max_dd = float(row.get("Max DD", 0) or 0)
                    pf = float(row.get("PF", 0) or 0)
                    rf = float(row.get("RF", 0) or 0)

                    return {"Profit": profit, "Max DD": max_dd, "PF": pf, "RF": rf}
                except Exception as e:
                    Logger.error(f"❌ Error extracting row metrics: {e}")
                    return {"Profit": 0, "Max DD": 0, "PF": 0, "RF": 0}

            def on_done(metrics):
                Logger.info(f"Opening graph for row {row_index} of report {report_key}")
                x = ["Profit", "Max DD", "RF", "PF"]
                y = [metrics[k] for k in x]

                fig = plt.figure(figsize=(6, 4))
                plt.plot(x, y, marker="o")
                plt.title(f"{report_key} - Row {row_index}")
                plt.grid(True)
                plt.tight_layout()
                fig.show()

                self.active_runners.remove(runner)

            def on_error(err):
                QMessageBox.critical(self.ui, "Graph Error", f"Failed to generate graph:\n{err}")
                if runner in self.active_runners:
                    self.active_runners.remove(runner)

            runner = ThreadRunner(self.ui)
            if not hasattr(self, "active_runners"):
                self.active_runners = []

            self.active_runners.append(runner)
            runner.on_result = on_done
            runner.on_error = on_error
            runner.run(task)

        except Exception as e:
            Logger.error(f"❌ show_graph failed: {e}")
            QMessageBox.critical(self.ui, "Graph Error", f"Failed to open graph:\n{e}")


    def show_overview(self, row_index):

            report_key = list(self.report_dfs.keys())[row_index]

            def task():
                # Metrics extraction in background
                return self.get_report_metrics(report_key)

            def on_done(metrics):
                Logger.info(f"Opening overview for: {report_key}")

                # --- UI THREAD ---
                overview_text = "\n".join([f"{k}: {v}" for k, v in metrics.items()])

                QMessageBox.information(
                    self.ui,
                    f"Overview - {report_key}",
                    overview_text
                )
         
            def on_error(err):
                QMessageBox.critical(self.ui, "Overview Error", f"Failed to fetch overview:\n{err}")

            runner = ThreadRunner(self.ui)
            if not hasattr(self, "active_runners"):
                self.active_runners = []

            self.active_runners.append(runner)

            runner.on_result = on_done
            runner.on_error = on_error
            runner.run(task)
    
#     def apply_table_filter(self):
#             try:
#                 # --- Read filter values (with safe defaults) ---
#                 try:
#                     max_dd    = self.safe_float(self.ui.txt_drawdown.text()) if self.ui.txt_drawdown.text() else float("inf")
#                     min_rf    = self.safe_float(self.ui.txt_recovery.text())  if self.ui.txt_recovery.text() else 0.0
#                     min_pf    = self.safe_float(self.ui.txt_profit.text())    if self.ui.txt_profit.text() else 0.0
#                     target_dd = self.safe_float(self.ui.txt_target.text())    if self.ui.txt_target.text() else float("inf")
#                 except Exception:
#                     # If safe_float throws, fallback to safe defaults
#                     max_dd, min_rf, min_pf, target_dd = float("inf"), 0.0, 0.0, float("inf")

#                 if not self.report_dfs:
#                     Logger.warning("No report data to filter.")
#                     return

#                 # --- Get first report & verify structure ---
#                 report_name = next(iter(self.report_dfs.keys()))
#                 tables = self.report_dfs[report_name]

#                 if not isinstance(tables, (list, tuple)) or len(tables) < 3:
#                     Logger.error(f"Report structure invalid for '{report_name}': expected (clean_data, orders, deals). Got: {type(tables)} / len={len(tables) if hasattr(tables, '__len__') else 'n/a'}")
#                     QMessageBox.warning(self.ui, "Filter error", "Report structure invalid. See logs.")
#                     return

#                 clean_data, orders, deals = tables[0], tables[1], tables[2]

#                 # --- Quick sanity checks & logging for debugging ---
#                 Logger.info(f"Filtering report '{report_name}': deals type={type(deals)}, rows={(len(deals) if hasattr(deals, '__len__') else 'n/a')}")
#                 # Show a few sample columns for diagnosis
#                 try:
#                     sample_deal = deals.head(3).to_dict(orient="records") if hasattr(deals, "head") else (deals[:3] if hasattr(deals, "__getitem__") else None)
#                     Logger.info(f"Sample deals (first 3): {sample_deal}")
#                 except Exception:
#                     Logger.info("Could not log sample deals (non-DataFrame)")

#                 # --- Make defensive copies ---
#                 # clean_data may be dict, pandas.Series, or DataFrame row — normalize to dict
#                 if hasattr(clean_data, "to_dict"):
#                     try:
#                         clean_data_dict = clean_data.to_dict()
#                     except Exception:
#                         # fallback: iterate
#                         clean_data_dict = dict(clean_data)
#                 elif isinstance(clean_data, dict):
#                     clean_data_dict = dict(clean_data)
#                 else:
#                     # last resort
#                     try:
#                         clean_data_dict = dict(clean_data)
#                     except Exception:
#                         clean_data_dict = {}

#                 # Use shallow copy for deals
#                 deals_copy = deals.copy() if hasattr(deals, "copy") else deals

#                 # --- Normalize numeric values from clean_data (so we won't get zeros by accident) ---
#                 def get_clean_numeric(key, default=0.0):
#                     return self.safe_float(clean_data_dict.get(key, default))

#                 clean_max_dd = get_clean_numeric("Max DD", 0.0)
#                 clean_rf     = get_clean_numeric("RF", 0.0)
#                 clean_pf     = get_clean_numeric("PF", 0.0)

#                 Logger.info(f"Strategy metrics from clean_data: Max DD={clean_max_dd}, RF={clean_rf}, PF={clean_pf}")

#                 # --- Build merged rows (per-deal) using clean_data metrics for filtering ---
#                 merged_rows = []
#                 # Make sure deals is iterable of rows (pandas DataFrame or list of dicts)
#                 if hasattr(deals_copy, "iterrows"):
#                     iterator = deals_copy.iterrows()
#                     is_dataframe = True
#                 elif isinstance(deals_copy, (list, tuple)):
#                     iterator = enumerate(deals_copy)
#                     is_dataframe = False
#                 else:
#                     # single-row fallback
#                     iterator = enumerate([deals_copy])
#                     is_dataframe = False

#                 for idx, deal_row in iterator:
#                     row_data = {}

#                     # Copy static clean_data values for showing in table
#                     # If clean_data is 1-row DataFrame, convert to dict properly
#                     if isinstance(clean_data, pd.DataFrame):
#                         static_dict = clean_data.to_dict(orient="records")[0]
#                     else:
#                         static_dict = clean_data

#                     for k, v in static_dict.items():
#                         row_data[k] = v


#                     # Deal-specific Profit (case-insensitive check)
#                     profit = None
#                     try:
#                         if is_dataframe:
#                             # deal_row is (index, Series) when iterrows() used: deal_row[1] if we mistakenly used enumerate
#                             # But since we used iterrows() above we have (index, Series) with deal_row being Series only if we unpack differently.
#                             # To be safe handle both:
#                             if isinstance(deal_row, tuple) and len(deal_row) == 2:
#                                 deal_series = deal_row[1]
#                             else:
#                                 deal_series = deal_row
#                             profit = deal_series.get("Profit", deal_series.get("profit", 0))
#                         else:
#                             # deal_row is dict-like
#                             if isinstance(deal_row, tuple) and len(deal_row) == 2:
#                                 deal_obj = deal_row[1]
#                             else:
#                                 deal_obj = deal_row
#                             profit = deal_obj.get("Profit", deal_obj.get("profit", 0))
#                     except Exception:
#                         profit = 0

#                     row_data["Profit"] = self.safe_float(profit)

#                     # KEY FIX: Use clean_data metrics for each row so filters use real numbers
#                     row_data["Max DD"] = clean_max_dd
#                     row_data["RF"]     = clean_rf
#                     row_data["PF"]     = clean_pf

#                     merged_rows.append(row_data)

#                 # --- Convert to DataFrame safely ---
#                 try:
#                     df = pd.DataFrame(merged_rows)
#                 except Exception as e:
#                     Logger.error(f"Failed to build merged DataFrame: {e}")
#                     QMessageBox.critical(self.ui, "Error", f"Failed to build merged DataFrame:\n{e}")
#                     return

#                 Logger.info(f"Merged df shape: {df.shape}. Columns: {list(df.columns)}")
#                 # show sample of df for debug
#                 try:
#                     Logger.info(f"Merged df head:\n{df.head(5).to_dict(orient='records')}")
#                 except Exception:
#                     pass

#                 # --- Ensure the numeric columns are numeric (coerce) ---
#                 numeric_cols = [
#                     "Profit", "Max DD", "RF", "PF",
#                     "Avg Win", "Avg Loss",
#                     "Trade Vol", "LotSize", "MaxLots",
#                     "MaxSequencesPerDay", "Lot Expo",
#                     "Max Hold", "Avg Hold"
#                 ]

#                 for col in numeric_cols:
#                     if col in df.columns:
#                         df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

#                 # --- Apply row-level filtering ---
#                 filtered_df = df[
#                     (df["Max DD"] <= max_dd) &
#                     (df["RF"] >= min_rf) &
#                     (df["PF"] >= min_pf) &
#                     (df["Max DD"] <= target_dd)
#                 ]

#                 Logger.info(f"Filtered df shape: {filtered_df.shape}")

#                 columns_to_show = [
#                     "Profit", "Max DD", "RF", "PF",
#                     "Avg Win", "Avg Loss", "Trade Vol",
#                     "LotSize", "MaxLots", "MaxSequencesPerDay", "MaxLots",
#                     "Lot Expo", "Max Hold", "Avg Hold",
#                     "Graph", "Overview"
#                 ]

# # Keep only existing columns
#                 filtered_df = filtered_df[[col for col in columns_to_show if col in filtered_df.columns]]

#                 # Render table
#                 self.populate_qtable_from_df(filtered_df)

#                 # --- Populate the QTable with filtered_df ---
#                 self.populate_qtable_from_df(filtered_df)

#             except Exception as e:
#                 Logger.error(f"Failed to apply table filter: {e}")
#                 QMessageBox.critical(self.ui, "Error", f"Failed to filter table:\n{str(e)}")

    def apply_table_filter(self):
            try:
                # --- 1. Read filter values safely ---
                max_dd    = self.safe_float(self.ui.txt_drawdown.text() or float("inf"))
                min_rf    = self.safe_float(self.ui.txt_recovery.text() or 0)
                min_pf    = self.safe_float(self.ui.txt_profit.text() or 0)
                target_dd = self.safe_float(self.ui.txt_target.text() or float("inf"))

                if not self.report_dfs:
                    Logger.warning("No report data to filter.")
                    return

                # --- 2. Get first report ---
                report_name = next(iter(self.report_dfs.keys()))
                tables = self.report_dfs[report_name]

                if not isinstance(tables, (list, tuple)) or len(tables) < 3:
                    Logger.error(f"Report structure invalid for '{report_name}'.")
                    return

                clean_data, orders, deals = tables[0], tables[1], tables[2]

                if deals is None or deals.empty:
                    Logger.warning("No deals data to filter.")
                    return

                # --- 3. Make copies ---
                clean_data_copy = clean_data.copy() if hasattr(clean_data, "copy") else dict(clean_data)
                deals_copy = deals.copy() if hasattr(deals, "copy") else deals

                # --- 4. Normalize clean_data dict ---
                if isinstance(clean_data_copy, pd.DataFrame):
                    clean_data_dict = clean_data_copy.to_dict(orient="records")[0]
                elif isinstance(clean_data_copy, pd.Series):
                    clean_data_dict = clean_data_copy.to_dict()
                else:
                    clean_data_dict = dict(clean_data_copy)

                # --- 5. Merge clean_data into deals ---
                merged_rows = []
                for _, deal_row in (deals_copy.iterrows() if hasattr(deals_copy, "iterrows") else enumerate(deals_copy)):
                    row_data = {}

                    # Copy static metrics
                    for k, v in clean_data_dict.items():
                        row_data[k] = v

                    # Deal-specific Profit
                    profit = 0
                    try:
                        if hasattr(deal_row, "get"):
                            profit = self.safe_float(deal_row.get("Profit", 0))
                        elif isinstance(deal_row, (list, tuple)) and len(deal_row) == 2:
                            profit = self.safe_float(deal_row[1].get("Profit", 0))
                    except Exception:
                        profit = 0
                    row_data["Profit"] = profit

                    # Use clean_data metrics for filtering
                    row_data["Max DD"] = self.safe_float(clean_data_dict.get("Max DD", 0))
                    row_data["RF"]     = self.safe_float(clean_data_dict.get("RF", 0))
                    row_data["PF"]     = self.safe_float(clean_data_dict.get("PF", 0))

                    merged_rows.append(row_data)

                df = pd.DataFrame(merged_rows)

                # --- 6. Force numeric columns to floats ---
                numeric_cols = ["Max DD", "RF", "PF", "Profit"]
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

                # --- 7. Apply filtering ---
                filtered_df = df[
                    (df["Max DD"] <= max_dd) &
                    (df["RF"] >= min_rf) &
                    (df["PF"] >= min_pf) &
                    (df["Max DD"] <= target_dd)
                ]

                Logger.info(f"Filtered df shape: {filtered_df.shape}")

                # --- 8. Keep only desired columns ---
                columns_to_show = [
                    "Profit", "Max DD", "RF", "PF",
                    "Avg Win", "Avg Loss", "Trade Vol",
                    "LotSize", "MaxLots", "MaxSequencesPerDay",
                    "Lot Expo", "Max Hold", "Avg Hold",
                    "Graph", "Overview"
                ]
                filtered_df = filtered_df[[col for col in columns_to_show if col in filtered_df.columns]]

                # --- 9. Populate QTable ---
                self.populate_qtable_from_df(filtered_df)

            except Exception as e:
                Logger.error(f"Failed to apply table filter: {e}")
                QMessageBox.critical(self.ui, "Error", f"Failed to filter table:\n{str(e)}")


            
    def populate_qtable_from_df(self, df):
            table = self.ui.middle_message
            table.clear()
            columns_to_show = [
                    "Profit", "Max DD", "RF", "PF",
                    "Avg Win", "Avg Loss", "Trade Vol",
                    "LotSize", "MaxLots", "MaxSequencesPerDay", "MaxLots",
                    "Lot Expo", "Max Hold", "Avg Hold",
                    "Graph", "Overview"
                ]
            # If df is empty or None -> clear and return
            if df is None or df.empty:
                table.header(columns_to_show)
                table.setRowCount(0)
                # table.setColumnCount(0)
                Logger.info("populate_qtable_from_df: empty df — table cleared.")
                return

            # Ensure column names are strings
            columns = [str(c) for c in df.columns.tolist()]
            table.setRowCount(len(df))
            table.setColumnCount(len(columns))
            table.setHorizontalHeaderLabels(columns)

            # If Graph/Overview expected name variants: handle case-insensitive
            graph_cols = [c for c in columns if c.lower() == "graph"]
            overview_cols = [c for c in columns if c.lower() == "overview"]

            for row_idx, (_, row) in enumerate(df.iterrows()):
                for col_idx, col_name in enumerate(columns):
                    value = row[col_name]
                    if col_name in graph_cols:
                        btn = QPushButton("Open")
                        btn.setMaximumSize(60, 60)
                        # capture the current row index for callback
                        btn.clicked.connect(partial(self.show_graph, row_idx))
                        table.setCellWidget(row_idx, col_idx, btn)
                        continue
                    if col_name in overview_cols:
                        btn = QPushButton("Open")
                        btn.setMaximumSize(60, 60)
                        btn.clicked.connect(partial(self.show_overview, row_idx))
                        table.setCellWidget(row_idx, col_idx, btn)
                        continue

                    item = QTableWidgetItem("" if pd.isna(value) else str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(row_idx, col_idx, item)

            # Stretch headers
            header_widget = table.horizontalHeader()
            header_widget.setSectionResizeMode(QHeaderView.Stretch)
            Logger.info(f"✅ Table populated with {len(df)} rows and {len(columns)} columns.")



                


            