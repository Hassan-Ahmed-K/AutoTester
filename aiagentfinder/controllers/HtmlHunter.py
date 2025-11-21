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
        self.ui.grouped_text.itemClicked.connect(lambda item: self.show_table(item.text()))

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

    def read_all_html_reports(self):
        """Parse all XML/HTM report files in a background thread."""
        if not self.report_files:
            Logger.error("❌ No report files found to process.")
            QMessageBox.warning(self.ui, "Warning", "No report files found to process.")
            return

        Logger.info(f"📂 Starting parsing for {len(self.report_files)} files...")

        def parse_html_report(file_path,out_dir=None):
            """Parse MT5 HTML/XML report into pandas DataFrames (robust, encoding-safe)."""

            try:
                
                with open(file_path, "rb") as f:
                    raw = f.read()

                detected = chardet.detect(raw)
                encoding = detected["encoding"]

                try:
                    content = raw.decode(encoding, errors="replace")
                except:
                    # fallback encodings MT4/MT5 use
                    for enc in ["utf-16", "utf-16le", "utf-16be", "latin-1"]:
                        try:
                            content = raw.decode(enc, errors="replace")
                            break
                        except:
                            continue

                
                soup = BeautifulSoup(content, "html.parser")

                tables = soup.find_all("table")
                tbodies = soup.find_all("tbody")

                elements = tbodies if tbodies else tables

                if not elements:
                    Logger.warning(f"⚠ No tables found in HTML: {file_path}")
                    return {}

                table_dfs = {}
                table_index = 0
                report_base = os.path.splitext(os.path.basename(file_path))[0]
                save_dir = out_dir if out_dir else os.path.dirname(file_path)
                os.makedirs(save_dir, exist_ok=True)
                
                for table in elements:
    
                    rows = []

                    for tr in table.find_all("tr"):
                        cells = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"])]

                        if cells and any(cells):  
                            rows.append(cells)

                    if len(rows) > 1:
                        df = pd.DataFrame(rows)
                        csv_name = f"{report_base}_table_{table_index}.csv"
                        csv_path = os.path.join(save_dir, csv_name)
                        # Save with BOM to help Excel detect UTF-8
                        df.to_csv(csv_path, index=False , header=False)
                        Logger.success(f"Saved CSV: {csv_path}")
                        table_dfs[f"table_{table_index}"] = df
                        table_index += 1

                return table_dfs

            except Exception as e:
                Logger.error(f"HTML parse error ({file_path}): {e}")
                return {}


        def task():
            dfs = {}

            for file_path in self.report_files:
                report_name = os.path.basename(file_path)
                ext = report_name.lower()

                if ext.endswith((".htm", ".html", ".xml.htm")):
                    Logger.info(f"🔍 Parsing HTML report: {report_name}")
                    html_tables = parse_html_report(file_path)

                    if html_tables:
                        dfs[report_name] = html_tables
                        Logger.success(f"Parsed HTML report: {report_name} ({len(html_tables)} tables)")
                    else:
                        Logger.warning(f"No tables found in HTML report: {report_name}")
                    continue


          
            return {"dataframes": dfs}

        
       

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
    
            Logger.info(f"📂 Report dataframes: {self.report_dfs}") 
            Logger.info(f"📘 Successfully parsed {len(self.report_dfs)} reports.")
            QMessageBox.information(self.ui, "Success",
                                    f"✅ Parsed {len(self.report_dfs)} XML/HTML reports successfully!")
            self.fill_table_threaded()
        def on_error(err):
            Logger.error(f"❌ Parsing failed: {err}")
            QMessageBox.critical(self.ui, "Error", f"❌ Parsing Failed:\n{err}")

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
        

        # ------------------------- CLEANERS -------------------------
    def _clean_number_str(self, s: str):
        if s is None:
            return ""
        s = str(s).strip()
        s = s.replace("\xa0", " ").replace("\u200b", "")
        return s

    def _extract_first_number(self, s: str):
        if s is None:
            return None
        s = str(s).replace("\xa0", "").replace(" ", "").replace(",", "")
        match = re.search(r"-?\d*\.?\d+", s)
        if not match:
            return None
        try:
            return float(match.group())
        except:
            return None
        
    
    def _extract_summary_metrics_from_df(self, df: pd.DataFrame) -> dict:
            metrics = {}

            if df is None or df.empty:
                return metrics

            for i in range(len(df)):
                row = df.iloc[i].astype(str).tolist()
                text = " ".join(row).lower()

                # Total Net Profit
                if "total net profit" in text:
                    m = re.search(r"total net profit.*?(-?\d[\d\s]*\.\d+)", text)
                    if m:
                        metrics["Profit"] = m.group(1).replace(" ", "")

                # Profit Factor
                if "profit factor" in text:
                    m = re.search(r"profit factor.*?(\d+\.\d+)", text)
                    if m:
                        metrics["PF"] = m.group(1)

                # Recovery Factor
                if "recovery factor" in text:
                    m = re.search(r"recovery factor.*?(\d+\.\d+)", text)
                    if m:
                        metrics["RF"] = m.group(1)

                # Average profit trade
                if "average profit trade" in text:
                    m = re.search(r"average profit trade.*?(-?\d+\.\d+)", text)
                    if m:
                        metrics["Avg Win"] = m.group(1)

                # Average loss trade
                if "average loss trade" in text:
                    m = re.search(r"average loss trade.*?(-?\d+\.\d+)", text)
                    if m:
                        metrics["Avg Loss"] = m.group(1)

                # Total trades
                if "total trades" in text:
                    m = re.search(r"total trades.*?(\d+)", text)
                    if m:
                        metrics["Trade Vol"] = m.group(1)

                # Balance DD Max
                if "balance drawdown maximal" in text:
                    m = re.search(r"balance drawdown maximal.*?(\d+\.\d+)", text)
                    if m:
                        metrics["Max DD"] = m.group(1)

                # Equity DD Max
                if "equity drawdown maximal" in text:
                    m = re.search(r"equity drawdown maximal.*?(\d+\.\d+)", text)
                    if m:
                        metrics["Max Drawdown"] = m.group(1)

                # Max holding time
                if "maximal position holding time" in text:
                    m = re.search(r"(\d{1,3}:\d{2}:\d{2})", text)
                    if m:
                        metrics["Max Hold"] = m.group(1)

                # Avg holding time
                if "average position holding time" in text:
                    m = re.search(r"(\d{1,3}:\d{2}:\d{2})", text)
                    if m:
                        metrics["Avg Hold"] = m.group(1)

            Logger.debug(f"Extracted summary metrics: {metrics}")
            return metrics

    
    def _normalize_orders_df(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy().fillna("")
        header_idx = None
        keywords = {"open time", "order", "symbol", "type", "volume", "price"}

        for i in range(min(5, len(df))):
            if sum(1 for kw in keywords if any(kw in str(cell).lower() for cell in df.iloc[i])) >= 2:
                header_idx = i
                break

        if header_idx is not None:
            df2 = df.iloc[header_idx+1:].copy()
            df2.columns = [str(x).strip() for x in df.iloc[header_idx]]
            df2.reset_index(drop=True, inplace=True)
            return df2

        df.reset_index(drop=True, inplace=True)
        Logger.debug(f"Normalized orders dataframe:\n{df}")
        return df


    def _extract_order_metrics_from_df(self, df: pd.DataFrame) -> dict:
        metrics = {}
        if df is None or df.empty:
            return metrics

        df2 = self._normalize_orders_df(df)

        vol_col = None
        for c in df2.columns:
            if "vol" in c.lower() or "lot" in c.lower():
                vol_col = c
                break

        volumes = []
        if vol_col:
            for v in df2[vol_col].astype(str):
                if "/" in v:
                    left = v.split("/")[0]
                    n = self._extract_first_number(left)
                else:
                    n = self._extract_first_number(v)

                if n is not None:
                    volumes.append(n)

        if volumes:
            metrics["Lot Size"] = volumes[0]
            metrics["Peak Lot Size"] = max(volumes)
            metrics["Max Lots"] = max(volumes)
            metrics["Lot Expo"] = sum(volumes)
        else:
            metrics["Lot Size"] = ""
            metrics["Peak Lot Size"] = ""
            metrics["Max Lots"] = ""
            metrics["Lot Expo"] = ""
        Logger.debug(f"Extracted order metrics: {metrics}")
        return metrics
    
    def get_report_metrics(self, report_key: str) -> dict:
        result = {k: "" for k in [
            "Max Drawdown", "Min Recovery Factor", "Min Profit Factor", "Target DD",
            "Profit", "Max DD", "RF", "PF", "Avg Win", "Avg Loss", "Trade Vol",
            "Lot Size", "Peak Lot Size", "Max Sq No", "Max Lots", "Lot Expo",
            "Max Hold", "Avg Hold"
        ]}

        parsed = self.report_dfs.get(report_key, {})
        summary = parsed.get("table_0")
        orders = parsed.get("table_1")
     
        sum_m = self._extract_summary_metrics_from_df(summary)
        ord_m = self._extract_order_metrics_from_df(orders)

        result.update(sum_m)
        result.update(ord_m)

        result["Min Recovery Factor"] = result["RF"]
        result["Min Profit Factor"] = result["PF"]
        result["Target DD"] = result["Max DD"]

        return result
    
    # def fill_metrics_table(self, table_widget, metrics: dict, columns: list):
    #     table_widget.clear()
    #     table_widget.setRowCount(1)
    #     table_widget.setColumnCount(len(columns))
    #     table_widget.setHorizontalHeaderLabels(columns)

    #     for col, key in enumerate(columns):
    #         value = str(metrics.get(key, ""))
    #         item = QTableWidgetItem(value)
    #         item.setTextAlignment(Qt.AlignCenter)
    #         table_widget.setItem(0, col, item)

    #     table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    # def fill_input_fields(self, metrics: dict):
    #     try:
    #         self.ui.txt_drawdown.setText(str(metrics.get("Max Drawdown", "")))
    #         self.ui.txt_recovery.setText(str(metrics.get("Min Recovery Factor", "")))
    #         self.ui.txt_profit.setText(str(metrics.get("Min Profit Factor", "")))
    #         self.ui.txt_target.setText(str(metrics.get("Target DD", "")))
    #     except Exception as e:
    #         Logger.warning(f"Input fields not set: {e}")


    # def run_metrics_thread(self, report_key: str):

    #         METRICS_TO_TABLE = [
    #             "Profit", "Max DD", "RF", "PF", "Avg Win", "Avg Loss", "Trade Vol",
    #             "Lot Size", "Peak Lot Size", "Max Sq No", "Max Lots", "Lot Expo",
    #             "Max Hold", "Avg Hold"
    #         ]

    #         def task():
    #             return self.get_report_metrics(report_key)

    #         def on_done(metrics):
    #             # Populate input fields
    #             self.fill_input_fields(metrics)

    #             # Populate metrics table
    #             self.fill_metrics_table(
    #                 self.ui.middle_message,
    #                 metrics,
    #                 METRICS_TO_TABLE
    #             )

    #             Logger.success("Metrics updated.")

    #         def on_error(err):
    #             QMessageBox.critical(self.ui, "Error", f"Metrics failed:\n{err}")

    #         self.runner = ThreadRunner(self.ui)
    #         self.runner.on_result = on_done
    #         self.runner.on_error = on_error
    #         self.runner.run(task)
    


    def show_table(self, report_key: str):
       

        columns= [
            "Profit", "Max DD", "RF", "PF", "Avg Win", "Avg Loss", "Trade Vol",
            "Lot Size", "Peak Lot Size", "Max Sq No", "Max Lots", "Lot Expo",
            "Max Hold", "Avg Hold", "Graph", "Overview"
        ]

        def task():
            return self.get_report_metrics(report_key)

        def on_done(metrics):

            # -------------------- INPUT FIELDS --------------------
            try:
                self.ui.txt_drawdown.setText(str(metrics.get("Max Drawdown", "")))
                self.ui.txt_recovery.setText(str(metrics.get("Min Recovery Factor", "")))
                self.ui.txt_profit.setText(str(metrics.get("Min Profit Factor", "")))
                self.ui.txt_target.setText(str(metrics.get("Target DD", "")))
            except Exception as e:
                Logger.warning(f"Input fields failed: {e}")

            # -------------------- TABLE FILL --------------------
            table = self.ui.middle_message
            headers = columns
            table.clear()
            table.setRowCount(1)
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)

            row_idx = 0

            for col_idx, key in enumerate(headers):

                # --- GRAPH BUTTON ---
                if key == "Graph":
                    btn = QPushButton("open")
                    btn.clicked.connect(partial(self.show_graph, key))
                    table.setCellWidget(row_idx, col_idx, btn)
                    continue

                
                if key == "Overview":
                    btn = QPushButton("open")
                    btn.clicked.connect(partial(self.show_overview, key))
                    table.setCellWidget(row_idx, col_idx, btn)
                    continue

                # --- NORMAL VALUE ---
                value = str(metrics.get(key, ""))
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_idx, col_idx, item)

            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            Logger.success("Metrics updated.")

        def on_error(err):
            QMessageBox.critical(self.ui, "Error", f"Metrics failed:\n{err}")

        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)



    def fill_table_threaded(self):
            """Fill the main table with all report metrics using a ThreadRunner."""
            
            if not self.report_dfs:
                Logger.warning("No reports to display.")
                return

            columns = [
                "Profit", "Max DD", "RF", "PF", "Avg Win", "Avg Loss", "Trade Vol",
                "Lot Size", "Peak Lot Size", "Max Sq No", "Max Lots", "Lot Expo",
                "Max Hold", "Avg Hold","Graph","Overview"
            ]

            def task():
                """Collect metrics for all reports in background."""
                data = []
                for report_key in self.report_dfs.keys():
                    metrics = self.get_report_metrics(report_key)
                    row = [metrics.get(col, "") for col in columns]
                    data.append(row)
                return data

            def on_done(data):
                table_widget = self.ui.middle_message
                table_widget.clear()
                table_widget.setColumnCount(len(columns))
                table_widget.setHorizontalHeaderLabels(columns)
                table_widget.setRowCount(len(data))

                for row_idx, row in enumerate(data):

                    for col_idx, col_name in enumerate(columns):

                        if col_name == "Graph":
                            btn = QPushButton("Open")
                            btn.clicked.connect(partial(self.show_graph, row_idx))
                            table_widget.setCellWidget(row_idx, col_idx, btn)
                            continue

                        if col_name == "Overview":
                            btn = QPushButton("Open")
                            btn.clicked.connect(partial(self.show_overview, row_idx))
                            table_widget.setCellWidget(row_idx, col_idx, btn)
                            continue

                        # Normal text column
                        value = str(row[col_idx])
                        item = QTableWidgetItem(value)
                        item.setTextAlignment(Qt.AlignCenter)
                        table_widget.setItem(row_idx, col_idx, item)

                table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                Logger.info(f"✅ Filled table with {len(data)} reports including buttons.")

            def on_error(err):
                Logger.error(f"❌ Failed to fill table: {err}")
                QMessageBox.critical(self.ui, "Error", f"❌ Failed to fill table:\n{err}")

            # Run using ThreadRunner
            self.runner = ThreadRunner(self.ui)
            self.runner.on_result = on_done
            self.runner.on_error = on_error
            self.runner.run(task)
    
    def show_graph(self, row_index):

        report_key = list(self.report_dfs.keys())[row_index]

        def task():
            # Heavy processing in background
            return self.get_report_metrics(report_key)

        def on_done(metrics):
            Logger.info(f"Opening graph for: {report_key}")
            
 

            x = ["Profit", "Max DD", "RF", "PF"]
            y = [
                float(metrics.get("Profit", 0) or 0),
                float(metrics.get("Max DD", 0) or 0),
                float(metrics.get("RF", 0) or 0),
                float(metrics.get("PF", 0) or 0)
            ]

            fig = plt.figure(figsize=(6,4))
            plt.plot(x, y, marker="o")
            plt.title(report_key)
            plt.grid(True)
            plt.tight_layout()

            fig.show()   # ✔ DOES NOT start event loop, safe
            self.active_runners.remove(runner)

        def on_error(err):
            QMessageBox.critical(self.ui, "Graph Error", f"Failed to generate graph:\n{err}")
            self.active_runners.remove(runner)


        runner = ThreadRunner(self.ui)
        if not hasattr(self, "active_runners"):
            self.active_runners = []

        self.active_runners.append(runner)

        runner.on_result = on_done
        runner.on_error = on_error
        runner.run(task)

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




