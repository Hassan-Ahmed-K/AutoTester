import os
import pandas as pd
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from aiagentfinder.utils import Logger
from aiagentfinder.utils.workerThread import ThreadRunner
from bs4 import BeautifulSoup
import chardet
class HtmlHunterController:
    def __init__(self, ui):
        self.ui = ui
        self.runner = ThreadRunner()
        self.auto_batch_ui = self.ui.parent().autoBatch_page
        self.setfinder_ui = self.ui.parent().setFinder_page


        # Internal storage for reports
        self.report_files = []          
        self.report_names = []          
        self.report_name = None         
        self.file_path = None           
        self.report_dfs = {}            
        self.report_properties = {}     

        # Connect buttons
        self.ui.btn_html.clicked.connect(self.browse_html_folder)
        self.ui.btn_export.clicked.connect(self.browse_export_folder)

    def browse_html_folder(self):
        """Select HTML Reports folder and list XML/HTM report files."""
        try:
            data_folder = (self.auto_batch_ui.data_input.text() or "").strip()
            if not data_folder:
                data_folder = (self.setfinder_ui.data_input.text() or "").strip()
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

        def parse_html_report(file_path):
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

             
                for table in elements:
    
                    rows = []

                    for tr in table.find_all("tr"):
                        cells = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"])]

                        if cells and any(cells):  
                            rows.append(cells)

                    if len(rows) > 1:
                        df = pd.DataFrame(rows)
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

            print("report_dfs:", self.report_dfs)

            Logger.info(f"📘 Successfully parsed {len(self.report_dfs)} reports.")
            QMessageBox.information(self.ui, "Success",
                                    f"✅ Parsed {len(self.report_dfs)} XML/HTML reports successfully!")

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
                data_folder = (self.setfinder_ui.data_input.text() or "").strip()
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
            
        


    




