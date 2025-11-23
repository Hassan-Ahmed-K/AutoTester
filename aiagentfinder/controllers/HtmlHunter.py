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

            Logger.info(f"📂 Preparing table for report: {report_name} deals)")
            self.log_to_ui(f"📂 Preparing table for report: {report_name} ({len(deals)} deals)")
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
                        row_data["Max DD"] = (self.safe_float(clean_data.get("Max DD", 0))/100)*profit
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
                    ow_idx = int(row_data)

                    row = self.filtered_df.iloc[row_idx]
                    # Safe float conversion
                    profit = self.safe_float(row_data.get("Profit", 0))
                    max_dd = self.safe_float(row_data.get("Max DD", 0))
                    pf = self.safe_float(row_data.get("PF", 0))
                    rf = self.safe_float(row_data.get("RF", 0))

                    # ---- Your formulas ----
                    avg_win = self.safe_float(row_data.get("Avg Win", 0)) * profit
                    avg_loss = self.safe_float(row_data.get("Avg Loss", 0)) * profit

                    return {
                        "profit": profit,
                        "max_dd": max_dd,
                        "pf": pf,
                        "rf": rf,
                        "avg_win": avg_win,
                        "avg_loss": avg_loss,
                        "title": row_data.get("Name", "Report Graph")
                    }

                except Exception as e:
                    raise Exception(f"Graph Thread Failed: {e}")

            def on_done(m):
                try:
                    x = ["Profit", "Max DD", "PF", "RF", "AvgWin", "AvgLoss"]
                    y = [m["profit"], m["max_dd"], m["pf"], m["rf"], m["avg_win"], m["avg_loss"]]

                    fig = plt.figure(figsize=(6, 4))
                    plt.plot(x, y, marker="o")
                    plt.grid(True)
                    plt.title(m["title"])
                    plt.tight_layout()
                    fig.show()

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





                


            
