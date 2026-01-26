import csv
import os
import shutil
import pandas as pd
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import QFileDialog, QMessageBox,QTableWidgetItem, QHeaderView,QPushButton,QDialog,QLabel,QVBoxLayout,QScrollArea,QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

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
        # self.runner = ThreadRunner()
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
                lambda item: self.show_dataframe_in_table(
                    self.html_lookup[item.text()] if item.text() in self.html_lookup.keys() else {}
                )
            )
        self.ui.btn_filter.clicked.connect(lambda: self.show_dataframe_in_table())

        self.ui.btn_export_sel.clicked.connect(self.export_selected_reports)

    def browse_html_folder(self):
        """Select HTML Reports folder and list XML/HTM report files."""
        try:
            print("self.auto_batch_ui.data_input.text() = ",self.auto_batch_ui.data_input.text())
            data_folder = (self.auto_batch_ui.data_input.text() or "").strip()
            if not data_folder:
                print()
                data_folder = (self.setprocessor_ui.data_folder_input.text() or "").strip()


            print("data_folder = ",data_folder)
            if data_folder != "":
                html_folder = os.path.join(data_folder, "Agent Finder Results")
            else:
                html_folder = ""

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
            self.folder_path = folder_path
            self.report_files = [os.path.join(folder_path, f) for f in files]
            self.report_names = files
            self.report_name = files[0]
            self.file_path = self.report_files[0]


            print("self.report_files = ", self.report_files)

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

        data = []
        for row in rows:
            cols = row.find_all(["td", "th"])
            cols = [ele.get_text(strip=True) for ele in cols]
            if cols:
                data.append(cols)
        
        t1_dict = self.parse_strategy_report(data)

        return t1_dict 

    def parse_strategy_report(self, data):
        data_dict = {}

        for row in data:
            i = 0
            while i < len(row) - 1:
                key = row[i].strip().rstrip(':')
                value = row[i+1].strip()

                # --- Handle Inputs specially ---
                if key == "Inputs" or (key == "" and value.startswith("Inp_")):
                    if "=" in value:
                        inp_key, inp_value = value.split("=", 1)
                        data_dict[inp_key] = inp_value
                # --- Normal key-value ---
                elif key:
                    if key in data_dict:
                        data_dict[key] += f", {value}"  # append multiple values
                    else:
                        data_dict[key] = value
                # --- Empty key but remaining pairs in row ---
                elif key == "" and i+2 < len(row):
                    j = i+1
                    while j < len(row) - 1:
                        k = row[j].strip().rstrip(':')
                        v = row[j+1].strip()
                        if k:
                            data_dict[k] = v
                        j += 2
                    break  # finished with this row
                i += 2

        return data_dict

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
        """Parse and combine all HTML reports by symbol + strategy."""

        if not self.report_files:
            QMessageBox.warning(self.ui, "Warning", "No report files found.")
            return

        Logger.info(f"📂 Parsing {len(self.report_files)} HTML reports...")

        def task():
            html_lookup = {}

            for file_path in self.report_files:
                report_name = os.path.basename(file_path)

                symbol, strategy = self.extract_symbol_strategy(file_path)
                if not symbol or not strategy:
                    Logger.warning(f"Skipping invalid filename: {report_name}")
                    continue

                html_key = f"{symbol}_{strategy}"

                try:
                    content = self.read_html_file(file_path)
                    if not content:
                        continue

                    soup = BeautifulSoup(content, "html.parser")
                    tables = soup.find_all("table")
                    if len(tables) < 2:
                        continue

                    # ---------- TABLE 1 (SUMMARY)
                    summary = self.extract_table_data(tables[0])
                    if not isinstance(summary, dict):
                        summary = {}

                    # ---------- TABLE 2 (ORDERS + DEALS)
                    orders, deals = self.process_table_2(tables[1])
                    orders = pd.DataFrame(orders)
                    deals = pd.DataFrame(deals)

                    try:
                        if not deals.empty and isinstance(deals.columns[0], int):
                            deals.columns = deals.iloc[0]
                            deals = deals.iloc[2:]

                        if not orders.empty and isinstance(orders.columns[0], int):
                            orders.columns = orders.iloc[0]
                            orders = orders.iloc[2:]

                        deals.columns = [str(c).strip() for c in deals.columns]
                        orders.columns = [str(c).strip() for c in orders.columns]

                        orders["Open Time"] = pd.to_datetime(orders["Open Time"], errors="coerce")
                        deals["Time"] = pd.to_datetime(deals["Time"], errors="coerce")

                        merged_df = orders.merge(
                            deals,
                            left_on="Open Time",
                            right_on="Time",
                            how="inner"
                        )
                    except Exception:
                        merged_df = pd.DataFrame()


                    if html_key not in html_lookup:
                        html_lookup[html_key] = {"summary": [], "order_deals": [],"report_names":[],"index":[]}

                    html_lookup[html_key]["summary"].append(summary)
                    html_lookup[html_key]["order_deals"].append(merged_df)
                    # print('html_lookup[html_key]["report_names"] = ', html_lookup[html_key]["report_names"])
                    html_lookup[html_key]["report_names"].append(report_name)
                    # print('html_lookup[html_key]["index"] = ', html_lookup[html_key]["index"])
                    html_lookup[html_key]["index"].append(len(html_lookup[html_key]["report_names"]))



                    print(f"Added HTML entry for {html_key} ({report_name}), order_deals: {len(merged_df)}")


                    Logger.success(f"Parsed & combined: {html_key}")

                except Exception as e:
                    Logger.error(f"Failed parsing {report_name}: {e}")

            return html_lookup

        def on_done(result):
            self.html_lookup = result or {}

            # print("=====================================================")
            # print('self.html_lookup = ', self.html_lookup)
            # print("=====================================================")
            # for html in self.html_lookup:
            #     print("html =", html)
            #     break
            #     print()

            Logger.info(f"🔥 HTML groups loaded: {len(self.html_lookup)}")

            self.ui.grouped_text.clear()
            self.ui.grouped_text.addItems(self.html_lookup.keys())

            # self.save_html_lookup_to_csv()

            # if self.html_lookup:
            #     first_key = next(iter(self.html_lookup))
            #     self.show_dataframe_in_table(self.html_lookup[first_key])
            #     self.ui.grouped_text.setCurrentRow(0)

            # print("self.html_lookup = ", self.html_lookup)


            QMessageBox.information(
                self.ui,
                "Success",
                f"Parsed and combined {len(self.html_lookup)} HTML groups."
            )

        def on_error(err):
            QMessageBox.critical(self.ui, "Error", f"HTML parsing failed:\n{err}")

        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)
    
    def combine_html_entries(self, base_entry, new_entry):
        """
        Combine two HTML entries with the same symbol + strategy.
        - Keeps base summary, fills missing keys from new_entry
        - Concatenates deals DataFrames
        - Prints summary keys that are merged
        """

        print("-----------------------------------------------------------------------")
        print('new_entry.get("summary", {}) = ',new_entry.get("summary", {}))
        print('base_entry.get("summary", {}) = ',base_entry.get("summary", {}))
        print("-----------------------------------------------------------------------")


        if not base_entry:
            return new_entry

        if not new_entry:
            return base_entry

        combined = {
            "summary": dict(base_entry.get("summary", {})),
            "deals": base_entry.get("deals", pd.DataFrame()).copy()
        }

        # ---------- Merge SUMMARY (safe) ----------
        new_summary = new_entry.get("summary", {})

        print('new_entry.get("summary", {}) = ',new_entry.get("summary", {}))
        print('base_entry.get("summary", {}) = ',base_entry.get("summary", {}))

        merged_keys = []

        if isinstance(new_summary, dict):
            for k, v in new_summary.items():
                if k not in combined["summary"] or combined["summary"][k] in ("", None):
                    combined["summary"][k] = v
                    merged_keys.append(k)

        if merged_keys:
            print(f"🟢 Merged summary keys for {new_summary.get('Symbol','Unknown')}:{new_summary.get('Inp_Expert_Title','Unknown')} → {merged_keys}")

        # ---------- Append DEALS ----------
        new_deals = new_entry.get("deals")
        if isinstance(new_deals, pd.DataFrame) and not new_deals.empty:
            combined["deals"] = pd.concat(
                [combined["deals"], new_deals],
                ignore_index=True,
                sort=False
            )
            print(f"🔵 Appended {len(new_deals)} deal rows.")

        return combined
    
    def save_html_lookup_to_csv(self):
        """
        Save only summaries from all merged HTML reports (self.html_lookup) into CSV files.
        Each symbol_strategy will get its own CSV.
        Each HTML summary becomes a separate row.
        """
        if not hasattr(self, "html_lookup") or not self.html_lookup:
            Logger.warning("❌ No HTML reports to save.")
            return

        output_dir = os.path.join(os.getcwd(), "CSV_Reports")
        os.makedirs(output_dir, exist_ok=True)

        for key, entry in self.html_lookup.items():
            try:
                summaries = entry.get("summary", [])
                if not summaries:
                    Logger.warning(f"❌ No summaries for {key}, skipping CSV.")
                    continue

                # Create DataFrame where each summary is a row
                final_df = pd.DataFrame(summaries)

                csv_path = os.path.join(output_dir, f"{key}.csv")
                final_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

                Logger.info(f"💾 Saved CSV (summaries only): {csv_path}")

            except Exception as e:
                Logger.error(f"❌ Failed to save CSV for {key}: {e}")
   
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

    def show_dataframe_in_table(self, report_dict: dict = None):

        # ---------- 1️⃣ Resolve selected report ----------
        selected_item = self.ui.grouped_text.currentItem()

        if not selected_item:
            if self.ui.grouped_text.count() == 0:
                Logger.warning("❌ No report selected and list is empty.")
                return
            self.ui.grouped_text.setCurrentRow(0)
            selected_item = self.ui.grouped_text.item(0)

        report_key = selected_item.text()
        report_dict = self.html_lookup.get(report_key, {})

        if "summary" not in report_dict or not report_dict["summary"]:
            Logger.warning(f"❌ No summary data for '{report_key}'.")
            return

        summaries = report_dict["summary"]
        Logger.info(f"show_dataframe_in_table → {report_key} ({len(summaries)} summaries)")

        # ---------- 2️⃣ Read filters (safe defaults) ----------
        max_dd = self.safe_float(self.ui.txt_drawdown.text()) if self.ui.txt_drawdown.text() else None
        min_rf = self.safe_float(self.ui.txt_recovery.text()) if self.ui.txt_recovery.text() else None
        min_pf = self.safe_float(self.ui.txt_profit.text()) if self.ui.txt_profit.text() else None
        target_dd = self.safe_float(self.ui.txt_target.text()) if self.ui.txt_target.text() else None

        def task():
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
                "Overview": "Overview",
            }

            df = pd.DataFrame(summaries)

            # Ensure all required columns exist
            for col in column_mapping.values():
                if col not in df.columns:
                    df[col] = ""

            # ---------- 3️⃣ Convert numeric columns PROPERLY ----------
            def to_float(val):
                try:
                    return float(str(val).replace("%", "").split()[0])
                except:
                    return 0.0

            numeric_cols = [
                "Equity Drawdown Maximal",
                "Recovery Factor",
                "Profit Factor",
            ]

            for col in numeric_cols:
                df[col] = df[col].apply(to_float)

            # ---------- 4️⃣ APPLY FILTERS USING .loc (THIS FIXES 300000 ISSUE) ----------
            if max_dd is not None:
                df = df.loc[df["Equity Drawdown Maximal"] >= max_dd]

            if target_dd is not None:
                df = df.loc[df["Equity Drawdown Maximal"] >= target_dd]

            if min_rf is not None:
                df = df.loc[df["Recovery Factor"] >= min_rf]

            if min_pf is not None:
                df = df.loc[df["Profit Factor"] >= min_pf]

            # ---------- 5️⃣ Prepare final table ----------
            df = (
                df[list(column_mapping.values())]
                .rename(columns={v: k for k, v in column_mapping.items()})
                .fillna("")
                .reset_index(drop=True)
            )

            df["Graph"] = "Open"
            df["Overview"] = "Open"

            return df.columns.tolist(), df.astype(str).values.tolist()

        # ---------- 6️⃣ UI update ----------
        def on_done(result):
            headers, table_data = result
            table = self.ui.middle_message

            table.clear()
            table.setRowCount(0)
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)

            for r, row in enumerate(table_data):
                table.insertRow(r)
                for c, val in enumerate(row):
                    key = headers[c]

                    if key == "Graph":
                        btn = QPushButton("Open")
                        btn.clicked.connect(lambda _, x=r: self.show_graph(x))
                        table.setCellWidget(r, c, btn)
                        continue

                    if key == "Overview":
                        btn = QPushButton("Open")
                        btn.clicked.connect(lambda _, x=r: self.show_overview(x))
                        table.setCellWidget(r, c, btn)
                        continue

                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    table.setItem(r, c, item)

            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.log_to_ui(f"✅ Showing {len(table_data)} filtered rows")

        def on_error(err):
            Logger.error(f"❌ Table error: {err}")
            QMessageBox.critical(self.ui, "Error", str(err))

        # ---------- 7️⃣ Thread safety ----------
        if hasattr(self, "runner") and getattr(self.runner, "isRunning", lambda: False)():
            self.runner.quit()
            self.runner.wait()

        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)

    def get_graph_folder(self):
        parent_dir = os.path.dirname(self.folder_path)
        graph_dir = os.path.join(parent_dir, "Graph")
        return graph_dir

    def show_graph(self, row_data):
        try:
            # 1️⃣ Identify selected report key
            selected_item = self.ui.grouped_text.currentItem()
            if not selected_item:
                Logger.warning("❌ No report selected.")
                return

            # report_key = selected_item.text()
            # report_name = self.html_lookup[report_key]["report_names"][row_idx]
            # image_name = os.path.splitext(report_name)[0] + ".png"
            # graph_dir = self.get_graph_folder()
            # image_path = os.path.join(graph_dir, image_name)

            row_idx = int(row_data)
            report_key = selected_item.text()
            report_name = self.html_lookup[report_key]["report_names"][row_idx]
            image_name = report_name.split(".")[0]+ ".png"
            graph_dir = self.get_graph_folder()
            image_path = os.path.join(graph_dir, image_name)

            print("======================================================")
            print("row_idx = ", row_idx)
            print("report_key = ", report_key)
            print("report_name = ", report_name)
            print("image_name = ", image_name)
            print("graph_dir = ", graph_dir)
            print("image_path = ", image_path)
            print("======================================================")

            if not os.path.exists(image_path):
                QMessageBox.warning(
                    self.ui,
                    "Image Not Found",
                    f"Graph image not found:\n{image_path}"
                )
                return

            dialog = QDialog(self.ui)
            dialog.setWindowTitle(f"Graph - {report_name}")
            dialog.resize(900, 600)

            layout = QVBoxLayout(dialog)

            label = QLabel()
            label.setAlignment(Qt.AlignCenter)

            pixmap = QPixmap(image_path)
            label.setPixmap(
                pixmap.scaled(
                    880, 560,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )

            layout.addWidget(label)
            dialog.setLayout(layout)
            dialog.exec_()

            Logger.info(f"📈 Graph opened: {image_path}")

        except Exception as e:
            Logger.error(f"❌ Failed to open graph: {e}")
            QMessageBox.critical(self.ui, "Error", str(e))

    def get_overview_folder(self):
        parent_dir = os.path.dirname(self.folder_path)
        overview_dir = os.path.join(parent_dir, "Overview")
        return overview_dir

    def show_overview(self, row_data):
        try:
            selected_item = self.ui.grouped_text.currentItem()
            if not selected_item:
                Logger.warning("❌ No report selected.")
                return

            row_idx = int(row_data)
            report_key = selected_item.text()
            report_name = self.html_lookup[report_key]["report_names"][row_idx]

            base_name = os.path.splitext(report_name)[0]   # report without extension
            overview_dir = self.get_overview_folder()


            # 🔍 collect all overview images for this report
            overview_images = sorted([
                os.path.join(overview_dir, f)
                for f in os.listdir(overview_dir)
                if f.startswith(base_name) and f.lower().endswith(".png")
            ])

            print("======================================================")
            print("row_idx = ", row_idx)
            print("report_key = ", report_key)
            print("report_name = ", report_name)
            print("base_name = ", base_name)
            print("overview_dir = ", overview_dir)
            print("overview_images = ", overview_images)
            print("======================================================")

            if not overview_images:
                QMessageBox.warning(
                    self.ui,
                    "Overview Not Found",
                    f"No overview images found for:\n{base_name}"
                )
                return

            # 🪟 Dialog
            dialog = QDialog(self.ui)
            dialog.setWindowTitle(f"Overview - {report_name}")
            dialog.resize(900, 600)

            scroll = QScrollArea(dialog)
            scroll.setWidgetResizable(True)

            container = QWidget()
            layout = QVBoxLayout(container)

            # 📸 Add all overview images
            for image_path in overview_images:
                label = QLabel()
                label.setAlignment(Qt.AlignCenter)

                pixmap = QPixmap(image_path)
                label.setPixmap(
                    pixmap.scaled(
                        860, 520,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )

                layout.addWidget(label)

            scroll.setWidget(container)

            main_layout = QVBoxLayout(dialog)
            main_layout.addWidget(scroll)
            dialog.setLayout(main_layout)

            dialog.exec_()

            Logger.info(f"🖼️ Overview opened ({len(overview_images)} images)")

        except Exception as e:
            Logger.error(f"❌ Failed to open overview: {e}")
            QMessageBox.critical(self.ui, "Error", str(e))
   
    def apply_table_filter(self):
        try:
            # --- 1️⃣ Read filter inputs safely ---
            max_dd    = self.safe_float(self.ui.txt_drawdown.text()) if self.ui.txt_drawdown.text() else float("inf")
            min_rf    = self.safe_float(self.ui.txt_recovery.text()) if self.ui.txt_recovery.text() else 0
            min_pf    = self.safe_float(self.ui.txt_profit.text()) if self.ui.txt_profit.text() else 0
            target_dd = self.safe_float(self.ui.txt_target.text()) if self.ui.txt_target.text() else float("inf")


            print("max_dd = ",max_dd)
            print("min_rf = ",min_rf)
            print("min_pf = ",min_pf)
            print("target_dd = ",target_dd)

            if not self.html_lookup:
                QMessageBox.warning(self.ui, "No Reports", "No reports loaded.")
                return

            # --- 2️⃣ Selected report ---
            selected_item = self.ui.grouped_text.currentItem()
            if not selected_item:
                QMessageBox.warning(self.ui, "No Report Selected", "Select a report first.")
                return
                   
            report_name = selected_item.text()
            summary, order_deals, report_names,index = self.html_lookup.get(report_name, (None, None, None, None))

            print("summary = ",summary)
            print("order_deals = ",order_deals)
            print("report_names = ",report_names)
            print("index = ",index)

            if deals is None or deals.empty:
                QMessageBox.warning(self.ui, "No Deals", "This report has no deals.")
                return

            # --- 3️⃣ Normalize clean_data ---
            if isinstance(summary, pd.DataFrame):
                clean = summary.to_dict(orient="records")[0]
            elif isinstance(summary, pd.Series):
                clean = summary.to_dict()
            elif isinstance(summary, dict):
                clean = summary
            else:
                clean = {}

            # --- 4️⃣ Merge clean metrics + deal rows ---
            merged_rows = []

            for _, deal_row in deals.iterrows():
                row = dict(clean)

                profit = self.safe_float(deal_row.get("Profit", 0))
                row["Profit"] = profit

                row["Max DD"] = (self.safe_float(clean.get("Max DD", 0)) / 100)
                row["RF"]     = self.safe_float(clean.get("RF", 0))
                row["PF"]     = self.safe_float(clean.get("PF", 0))

                row["Avg Win"]  = self.safe_float(clean.get("Avg Win", 0)) 
                row["Avg Loss"] = self.safe_float(clean.get("Avg Loss", 0)) 

                merged_rows.append(row)

            df = pd.DataFrame(merged_rows)

            # --- 5️⃣ Force numeric columns ---
            numeric_cols = ["Max DD", "RF", "PF", "Profit", "Avg Win", "Avg Loss"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            # --- 6️⃣ Apply filters (ONLY if user entered them) ---
            mask = pd.Series(True, index=df.index)

            if max_dd != float("inf"):
                mask &= df["Max DD"] <= max_dd

            if target_dd != float("inf"):
                mask &= df["Max DD"] <= target_dd

            if min_rf > 0:
                mask &= df["RF"] >= min_rf

            if min_pf > 0:
                mask &= df["PF"] >= min_pf

            filtered_df = df[mask].copy()

            # --- 7️⃣ Columns to show ---
            columns_to_show = [
                "Profit", "Max DD", "RF", "PF",
                "Avg Win", "Avg Loss", "Trade Vol",
                "LotSize", "MaxLots", "MaxSequencesPerDay",
                "Lot Expo", "Max Hold", "Avg Hold"
            ]

            filtered_df = filtered_df[[c for c in columns_to_show if c in filtered_df.columns]]

            # --- 8️⃣ Add action columns ---
            filtered_df["Graph"] = "Open"
            filtered_df["Overview"] = "Open"

            # --- 9️⃣ Render table ---
            self.log_to_ui(f"Filtered {filtered_df.shape[0]} rows")
            self.populate_qtable_from_df(filtered_df)

        except Exception as e:
            Logger.error(f"❌ Filter error: {e}")
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

    def get_selected_folders(self):
        
        selected_export_format = {}      
        parent_dir = os.path.dirname(self.folder_path)

        if self.ui.chk_setfile.isChecked():
            selected_export_format["set"] = parent_dir 

        if self.ui.chk_html.isChecked():
            selected_export_format["htm"] = os.path.join(parent_dir, "HTML Reports")

        if self.ui.chk_csv.isChecked():
            selected_export_format["csv"] = os.path.join(parent_dir, "CSV")

        if self.ui.chk_graph.isChecked():
            selected_export_format["Graph"] = os.path.join(parent_dir, "Graph")

        if self.ui.chk_overview.isChecked():
            selected_export_format["Overview"] = os.path.join(parent_dir, "Overview")

        return selected_export_format


    # def export_selected_reports(self):
    #     try:
    #         Logger.info("Starting export_selected_reports...")

    #         # Validate export folder
    #         if not os.path.isdir(self.export_folder_path):
    #             raise Exception(f"Export folder does not exist: {self.export_folder_path}")

    #         # Get selected report group
    #         selected_item = self.ui.grouped_text.currentItem()

    #         if not selected_item:
    #             if self.ui.grouped_text.count() == 0:
    #                 Logger.warning("❌ No report selected and list is empty.")
    #                 return
    #             self.ui.grouped_text.setCurrentRow(0)
    #             selected_item = self.ui.grouped_text.item(0)

    #         report_key = selected_item.text()
    #         report_dict = self.html_lookup.get(report_key, {})

    #         if not report_dict:
    #             raise Exception("No report data found for selected group.")

    #         # ✅ GET REPORT NAMES CORRECTLY
    #         report_names = report_dict.get("report_names", [])

    #         if not report_names:
    #             raise Exception("No report names found.")

    #         # Get selected table rows
    #         selected_rows = self.get_selected_row_indexes()

    #         if not selected_rows:
    #             raise Exception("No rows selected in table.")

    #         Logger.info(f"Selected rows: {selected_rows}")
    #         Logger.info(f"Available reports: {report_names}")

    #         selected_export_format = self.get_selected_export_formats()
    #         if not selected_export_format:
    #             raise Exception("No export formats selected (checkboxes).")

    #         copied_count = 0

    #         for export_format, src_path in selected_export_format.items():

    #             for row in selected_rows:
    #                 if row >= len(report_names):
    #                     Logger.warning(f"⚠️ Row index {row} out of range")
    #                     continue

    #                 report_name = report_names[row]

    #                 if(export_format in ["set","csv"]):
    #                     report_name = report_names[row].replace("htm", export_format)
    #                 else:
    #                     report_name = report_names[row].replace("htm", "")

    #                     if(export_format == "Graph"):
    #                         report_name = report_names[row].replace("htm", "png")
    #                     elif(export_format == "Overview"):
    #                         report_name = report_names[row].replace("htm", "png")
    #                         overview_images = sorted([
    #                             for f in os.listdir(src_path)
    #                             if f.startswith(report_name) and f.lower().endswith(".png")
    #                         ])

    #                 if not report_name:
    #                     Logger.warning(f"⚠️ Empty report name at row {row}")
    #                     continue
                    
    #                 if(export_format == "Overview"):
    #                     for image in overview_images:
    #                         src = os.path.join(src_path, image)
    #                         dst = os.path.join(self.export_folder_path, image)
    #                         if not os.path.exists(src):
    #                             Logger.warning(f"❌ Source file not found: {src}")
    #                             continue
    #                         Logger.info(f"Copying {image} → {self.export_folder_path}")
    #                         shutil.copy2(src, dst)
    #                         copied_count += 1
    #                 else:
    #                     src = os.path.join(src_path, report_name)
    #                     dst = os.path.join(self.export_folder_path, report_name)

    #                     if not os.path.exists(src):
    #                     Logger.warning(f"❌ Source file not found: {src}")
    #                     continue

    #                 Logger.info(f"Copying {report_name} → {self.export_folder_path}")
    #                 shutil.copy2(src, dst)
    #                 copied_count += 1

    #         QMessageBox.information(
    #             self.ui,
    #             "Export Complete",
    #             f"{copied_count} report(s) exported to:\n{self.export_folder_path}"
    #         )

    #         Logger.info("Export completed successfully.")

    #     except Exception as e:
    #         Logger.error(f"Export failed: {e}")
    #         QMessageBox.critical(self.ui, "Export Error", str(e))


    def export_selected_reports(self):
        try:
            Logger.info("Starting export_selected_reports...")

            if not os.path.isdir(self.export_folder_path):
                os.makedirs(self.export_folder_path)
                Logger.info(f"Created export folder: {self.export_folder_path}")

            selected_item = self.ui.grouped_text.currentItem()
            if not selected_item:
                if self.ui.grouped_text.count() == 0:
                    Logger.warning("❌ No report selected and list is empty.")
                    return
                self.ui.grouped_text.setCurrentRow(0)
                selected_item = self.ui.grouped_text.item(0)

            report_key = selected_item.text()
            report_dict = self.html_lookup.get(report_key, {})
            if not report_dict:
                raise Exception("No report data found for selected group.")

            report_names = report_dict.get("report_names", [])
            if not report_names:
                raise Exception("No report names found.")

            selected_rows = self.get_selected_row_indexes()
            if not selected_rows:
                raise Exception("No rows selected in table.")

            Logger.info(f"Selected rows: {selected_rows}")
            Logger.info(f"Available reports: {report_names}")

            selected_export_format = self.get_selected_folders()
            if not selected_export_format:
                raise Exception("No export formats selected (checkboxes).")

            copied_count = 0

            def get_files_for_format(base_name, export_format, src_path):
                files = []

                export_format_lower = export_format.lower()

                # if export_format_lower in ["set", "csv"]:
                #     ext = "csv" if export_format_lower == "csv" else "set"
                #     files.append(base_name.replace(".htm", f".{ext}"))

                if export_format_lower in ["set", "csv"]:
                    if export_format_lower == "csv":
                        ext = "csv"
                        files.append(base_name.replace(".htm", f".{ext}"))
                    else: 
                        parts = base_name.replace(".htm", "").split("_")
                        if len(parts) > 4:
                            parts = parts[1:]
                        new_name = "_".join(parts) + ".set"
                        files.append(new_name)

                elif export_format_lower == "htm":
                    files.append(base_name)

                elif export_format_lower in ["graph", "overview"]:
                    prefix = base_name.replace(".htm", "")
                    files = sorted([
                        f for f in os.listdir(src_path)
                        if f.startswith(prefix) and f.lower().endswith(".png")
                    ])
                return files

            for export_format, src_path in selected_export_format.items():
                if not os.path.exists(src_path):
                    Logger.warning(f"⚠️ Source folder does not exist: {src_path}")
                    continue

                for row in selected_rows:
                    if row >= len(report_names):
                        Logger.warning(f"⚠️ Row index {row} out of range")
                        continue

                    base_name = report_names[row]
                    print(base_name)
                    print(export_format)
                    print(src_path)
                    files_to_copy = get_files_for_format(base_name, export_format, src_path)

                    print(files_to_copy)

                    if not files_to_copy:
                        Logger.warning(f"⚠️ No files found for {export_format} at row {row}")
                        continue

                    for file_name in files_to_copy:
                        src = os.path.join(src_path, file_name)
                        dst = os.path.join(self.export_folder_path, file_name)

                        print(src)
                        print(dst)

                        if not os.path.exists(src):
                            Logger.warning(f"❌ Source file not found: {src}")
                            continue

                        Logger.info(f"Copying {file_name} → {self.export_folder_path}")
                        shutil.copy2(src, dst)
                        copied_count += 1

            QMessageBox.information(
                self.ui,
                "Export Complete",
                f"{copied_count} file(s) exported to:\n{self.export_folder_path}"
            )
            Logger.info("Export completed successfully.")

        except Exception as e:
            Logger.error(f"Export failed: {e}")
            QMessageBox.critical(self.ui, "Export Error", str(e))




    def get_selected_row_indexes(self):
        return [
            index.row()
            for index in self.ui.middle_message.selectionModel().selectedRows()
        ]

    
    def extract_symbol_strategy(self, html_path):
        name = os.path.basename(html_path).replace(".htm", "")
        parts = name.split("_")

        # Safety
        if len(parts) < 2:
            return None, None

        symbol = parts[0].upper()   
        strategy = parts[2].lower()        

        return symbol, strategy
            


            