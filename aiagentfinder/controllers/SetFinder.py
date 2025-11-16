import os
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from aiagentfinder.utils.logger import Logger
from aiagentfinder.utils.workerThread import ThreadRunner
from PyQt5.QtCore import Qt, QDate
import re

class SetFinderController:
    def __init__(self, ui):
        self.ui = ui
        self.runner = ThreadRunner()
        self.main_window = self.ui.parent()

        # self.file_path = None
        self.doc_properties = {}



        self.ui.htm_dir_btn.clicked.connect(self.browse_report_directory)
        self.ui.toggle_btn.stateChanged.connect(self.on_toggle_trade_filter)
        self.ui.start_button.clicked.connect(self.read_all_xml_tables)
        self.ui.reset_button.clicked.connect(self.reset_all_fields)
        # self.ui.report_dir_input.textChanged.connect(self.read_xml)


    def on_toggle_trade_filter(self, state):
        """Show/hide inputs based on toggle state."""
        # return
        if state == Qt.Checked:
            self.ui.target_dd_widget.hide()
            self.ui.risk_trade_widget.show()
            self.ui.max_consec_loss_widget.show()
            self.ui.filter_row.setStretch(
            self.ui.filter_row.indexOf(self.ui.dynamic_container), 2
        )
        else:
            self.ui.target_dd_widget.show()
            self.ui.risk_trade_widget.hide()
            self.ui.max_consec_loss_widget.hide()
            self.ui.filter_row.setStretch(
            self.ui.filter_row.indexOf(self.ui.dynamic_container), 1
        )
         
    def browse_report_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self.ui,
            "Select Report Directory",
            os.getcwd()
        )

        if not dir_path:
            return

        # Find all XML files in the selected directory
        report_files = [
            f for f in os.listdir(dir_path)
            if f.lower().endswith(".xml")
        ]

        if not report_files:
            QMessageBox.warning(
                self.ui,
                "No Report Files Found",
                "The selected folder does not contain any .xml files.\n"
                "Please select a valid folder containing report files."
            )
            return

        # ✅ Store all report files (with full paths) in a list
        self.main_window.report_files = [
            os.path.join(dir_path, f) for f in report_files
        ]

        # Optionally, also store just the file names
        self.main_window.report_names = report_files

        # Set first report file as default selection
        self.main_window.report_name = report_files[0]
        self.main_window.file_path = self.main_window.report_files[0]
        self.ui.report_dir_input.setText(dir_path)

        Logger.info(f"📂 Report directory selected: {dir_path}")
        Logger.info(f"📄 Total reports found: {len(self.main_window.report_files)}")
        Logger.info(f"📄 Report files: {self.main_window.report_files}")
        Logger.info(f"📄 Default report file: {self.main_window.file_path}")

        self.read_all_xml_reports()
        
    def read_all_xml_reports(self):
        """Parses all XML report files in a background thread and stores them in self.main_window.report_dfs."""

        # Ensure we have report files
        if not hasattr(self.main_window, "report_files") or not self.main_window.report_files:
            Logger.error("❌ No XML report files found to process.")
            QMessageBox.warning(self.ui, "Warning", "No XML report files found to process.")
            return

        self.ui.start_button.setText("Reading XML Reports...")
        self.ui.start_button.setEnabled(False)
        Logger.info(f"📂 Starting XML parsing for {len(self.main_window.report_files)} files...")

        def task():
            report_dfs = {}  # dictionary to store all DataFrames
            report_props = {}  # 🟢 ADDED (line 23) — store all DocumentProperties per report

            for file_path in self.main_window.report_files:
                try:
                    Logger.info(f"📄 Parsing XML file: {file_path}")
                    tree = ET.parse(file_path)
                    root = tree.getroot()

                    namespaces = {
                        'o': 'urn:schemas-microsoft-com:office:office',
                        'ss': 'urn:schemas-microsoft-com:office:spreadsheet'
                    }

                    # Extract document properties
                    doc_props_dict = {}
                    doc_props = root.find('o:DocumentProperties', namespaces)
                    if doc_props is not None:
                        for child in doc_props:
                            tag_name = child.tag.split('}')[-1]
                            value = child.text.strip() if child.text else ""
                            doc_props_dict[tag_name] = value
                        Logger.info(f"📑 Extracted DocumentProperties from {os.path.basename(file_path)}: {doc_props_dict}")  # 🟢 ADDED (line 44)
                    else:
                        Logger.warning(f"No DocumentProperties found in {file_path}")

                    # 🟢 ADDED (line 47) — Store the properties for use in populate_inputs_from_doc_props
                    report_name = os.path.basename(file_path)
                    report_props[report_name] = doc_props_dict

                    # ✅ Example of converting XML to DataFrame (customize this as needed)
                    data = []
                    for row in root.findall('.//ss:Row', namespaces):
                        row_data = [cell.text for cell in row.findall('.//ss:Data', namespaces)]
                        if row_data:
                            data.append(row_data)

                    df = pd.DataFrame(data)
                    report_dfs[report_name] = df

                    Logger.info(f"✅ Parsed {report_name} with {len(df)} rows.")

                except Exception as e:
                    Logger.error(f"❌ Error parsing {file_path}: {e}")

            # 🟢 ADDED (line 66) — Return both DataFrames and DocumentProperties
            return {"dataframes": report_dfs, "properties": report_props}

        def on_done(result):
            # 🟢 MODIFIED (line 71) — Handle new return type (dict of dicts)
            if not result or not isinstance(result, dict):
                Logger.error("❌ Invalid result returned from XML thread.")
                QMessageBox.warning(self.ui, "Warning", "XML reading completed, but no valid data was returned.")
                self.ui.start_button.setText("Start")
                self.ui.start_button.setEnabled(True)
                return

            report_dfs = result.get("dataframes", {})
            report_props = result.get("properties", {})  # 🟢 ADDED (line 80)

            if not report_dfs:
                Logger.error("❌ No valid DataFrames extracted.")
                QMessageBox.warning(self.ui, "Warning", "No tables found in XML reports.")
                return

            # ✅ Store parsed data and properties
            self.main_window.report_dfs = report_dfs
            self.main_window.report_properties = report_props  # 🟢 ADDED (line 88)

            Logger.info(f"📘 Successfully parsed {len(report_dfs)} reports.")
            Logger.info(f"📂 Reports stored: {list(report_dfs.keys())}")
            Logger.info(f"🧾 DocumentProperties stored for: {list(report_props.keys())}")  # 🟢 ADDED (line 91)


            self.ui.start_button.setText("Populating Data...")
            self.load_report_properties()


            self.ui.start_button.setText("Start")
            self.ui.start_button.setEnabled(True)
            QMessageBox.information(self.ui, "Success", f"✅ Parsed {len(report_dfs)} XML reports successfully!")

        def on_error(err):
            Logger.error(f"❌ Failed to process XML reports: {err}")
            self.ui.start_button.setText("Start")
            self.ui.start_button.setEnabled(True)
            QMessageBox.critical(self.ui, "Error", f"❌ XML Reading Failed:\n{str(err)}")

        # Run the task in a background thread
        Logger.debug("🚀 Starting background thread for all XML reports reading...")
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)

    def load_report_properties(self):
        """
        Load stored report properties into the UI input fields
        based on the selected report.
        """

        print("Hassan")

        try:
            # --- Step 1: Get the selected report key ---
            if not hasattr(self.main_window, "selected_report_index") or self.main_window.selected_report_index is None:
                print("⚠️ No report selected.")
                return

            if self.main_window.selected_report_index < 0 or self.main_window.selected_report_index >= len(self.main_window.report_files):
                print("⚠️ Invalid report index.")
                return

            report_key = os.path.basename(self.main_window.report_files[self.main_window.selected_report_index])

            # --- Step 2: Get the report data from main_window.report_properties ---
            print("report_key = ", report_key)
            print("self.main_window.report_file = ", self.main_window.report_files)
            print("self.main_window.report_propertiese = ", self.main_window.report_properties)
            report_data = self.main_window.report_properties.get(report_key)

            print("report_data = ", report_data)


            if not report_data:
                print(f"⚠️ No properties found for report: {report_key}")
                return
            
            print("report_data = ", report_data)

            title = report_data.get("Title", "")
            
            date_match = re.search(r"(\d{4}\.\d{2}\.\d{2})-(\d{4}\.\d{2}\.\d{2})", title)
            if date_match:
                start_str, end_str = date_match.groups()
                start_qdate = QDate.fromString(start_str, "yyyy.MM.dd")
                end_qdate = QDate.fromString(end_str, "yyyy.MM.dd")
                if start_qdate.isValid():
                    self.ui.start_date_input.setDate(start_qdate)
                if end_qdate.isValid():
                    self.ui.end_date_input.setDate(end_qdate)


            if "forward_period" in report_data:
                index = self.ui.account_dropdown.findText(report_data["forward_period"])
                if index >= 0:
                    self.ui.account_dropdown.setCurrentIndex(index)

            deposit_value = report_data.get("Deposit", "")
            if deposit_value:
                # Extract numeric part (e.g. "10000" from "10000 USD")
                deposit_numeric = re.findall(r"[\d\.]+", deposit_value)
                if deposit_numeric:
                    self.ui.balance_input.setText(deposit_numeric[0])

            if "target_dd" in report_data:
                self.ui.trade_input.setValue(float(report_data["target_dd"]))

            if "risk_trade" in report_data:
                self.ui.risk_trade_input.setText(str(report_data["risk_trade"]))

            if "max_consec_loss" in report_data:
                self.ui.max_consec_loss_input.setText(str(report_data["max_consec_loss"]))

            print(f"✅ Report '{report_key}' properties loaded successfully.")

        except Exception as e:
            print(f"❌ Error loading report properties: {e}")

    def populate_inputs_from_doc_props(self):
        """Populate UI inputs using extracted DocumentProperties data."""
        props = self.doc_properties

        if not props:
            print("No document properties to populate.")
            return

        # === Populate fields ===
        try:
            # Extract start and end dates from the Title (if available)
            title = props.get("Title", "")
            if title:
                import re
                # Try to find date range (e.g., 2023.12.23-2024.03.23)
                match = re.search(r"(\d{4}\.\d{2}\.\d{2})-(\d{4}\.\d{2}\.\d{2})", title)
                if match:
                    
                    start_str, end_str = match.groups()
                    start_date = QDate.fromString(start_str.replace('.', '-'), "yyyy-MM-dd")
                    end_date = QDate.fromString(end_str.replace('.', '-'), "yyyy-MM-dd")
                    if start_date.isValid():
                        self.ui.start_date_input.setDate(start_date)
                    if end_date.isValid():
                        self.ui.end_date_input.setDate(end_date)

            # Fill other inputs
            deposit = props.get("Deposit", "").split()[0] if "Deposit" in props else ""
            leverage = props.get("Leverage", "")
            condition = props.get("Condition", "")

            # Assign values to inputs
            if deposit:
                self.ui.balance_input.setText(deposit)
            if leverage:
                self.ui.trade_input.setValue(float(leverage))
            if condition:
                self.ui.max_consec_loss_input.setText(condition)

            print("✅ UI fields populated successfully.")

        except Exception as e:
            print(f"Error populating inputs: {e}")

    def read_all_xml_tables(self):
        """
        Reads all XML files in self.main_window.report_files, extracts tabular data,
        and stores each file's DataFrame in self.main_window.report_df as {filename: DataFrame}.
        Runs in a background thread and logs progress to UI.
        """

        def log_to_ui(message):
            Logger.info(message)
            self.ui.log_text.append(message)
            self.ui.log_text.verticalScrollBar().setValue(
                self.ui.log_text.verticalScrollBar().maximum()
            )

        # --- Guard clause ---
        if not hasattr(self.main_window, "report_files") or not self.main_window.report_files:
            log_to_ui("❌ No report files found. Please select a valid directory first.")
            return

        # --- Update UI state ---
        self.ui.start_button.setText("Processing Reports...")
        self.ui.start_button.setEnabled(False)
        log_to_ui(f"🚀 Starting XML table extraction for {len(self.main_window.report_files)} files...")

        # ============================
        # TASK (Background thread)
        # ============================
        def task():
            ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
            report_dfs = {}

            for file_path in self.main_window.report_files:
                try:
                    file_name = os.path.basename(file_path)
                    log_to_ui(f"📂 Reading XML file: {file_name}")
                    tree = ET.parse(file_path)
                    root = tree.getroot()

                    rows = []
                    for row in root.findall('.//ss:Row', ns):
                        cells = [
                            (cell.find('ss:Data', ns).text if cell.find('ss:Data', ns) is not None else '')
                            for cell in row.findall('ss:Cell', ns)
                        ]
                        rows.append(cells)

                    if not rows:
                        log_to_ui(f"⚠️ No rows found in {file_name}. Skipping...")
                        continue

                    # --- Convert to DataFrame ---
                    df = pd.DataFrame(rows)

                    
                    # --- Set header ---
                    if len(df) > 1:
                        df.columns = df.iloc[0]
                        df = df[1:].reset_index(drop=True)
                    else:
                        Logger.warning(f"⚠️ {file_name} contains only one row. Using default headers.")

                    # --- Merge duplicate columns ---
                    trades_cols = [c for c in ['Bk Trades', 'Fwd Trades'] if c in df.columns]
                    if trades_cols:
                        df['Trades'] = df[trades_cols].fillna(0).astype(float).sum(axis=1)

                    profit_cols = [c for c in ['Total Profit', 'Est Bk Weekly Profit'] if c in df.columns]
                    if profit_cols:
                        df['Profit'] = df[profit_cols].fillna(0).astype(float).sum(axis=1)


                    report_dfs[file_name] = df
                    Logger.info(f"✅ Processed {file_name} ({len(df)} rows)")

                    # Optionally save each CSV
                    


                except Exception as e:
                    Logger.error(f"❌ Error processing {file_path}: {str(e)}")
                    log_to_ui(f"❌ Error in {file_name}: {str(e)}")

            return report_dfs

        # ============================
        # CALLBACKS (Main thread)
        # ============================
        def on_done(result):
            if not result or not isinstance(result, dict):
                Logger.error("❌ Invalid result returned from XML thread.")
                QMessageBox.warning(self.ui, "Warning", "XML reading completed, but no valid data was returned.")
                self.ui.start_button.setText("Start")
                self.ui.start_button.setEnabled(True)
                return

            merged_dfs = {}
            processed = set()

            for report_name, df in result.items():
                if report_name in processed:
                    continue

                if ".forward.xml" in report_name:
                    base_name = report_name.replace(".forward.xml", ".xml")
                else:
                    base_name = report_name

                forward_name = base_name.replace(".xml", ".forward.xml")

                df_main = result.get(base_name, pd.DataFrame())
                df_forward = result.get(forward_name, pd.DataFrame())

                if not df_forward.empty:
                    # Prefix all forward columns except Pass
                    Logger.error(f"Forward file found: {forward_name}, prefixing columns.")
                    df_forward = df_forward.rename(
                        columns={col: f"forward_{col}" for col in df_forward.columns if col != "Pass"}
                    )

                # Merge both if available
                if not df_main.empty and not df_forward.empty:
                    try:
                        combined_df = pd.merge(df_main, df_forward, on="Pass", how="inner")
                        Logger.info(f"🔗 Merged {base_name} and {forward_name} on 'Pass' column with forward prefix.")
                    except Exception as e:
                        Logger.error(f"❌ Failed to merge {base_name} and {forward_name}: {e}")
                        combined_df = pd.concat([df_main, df_forward], ignore_index=True)
                elif not df_main.empty:
                    combined_df = df_main
                else:
                    combined_df = df_forward

                cols_to_convert = [
                    'forward_Forward Result',
                    'forward_Back Result',
                    'forward_Recovery Factor',
                    'Recovery Factor'
                ]

                # Convert to numeric (non-numeric -> NaN)
                for col in cols_to_convert:
                    combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')

                # Replace NaN with 0 in only these columns
                combined_df[cols_to_convert] = combined_df[cols_to_convert].fillna(0)

                # Compute score
                combined_df['custom_score'] = (
                    0.6 * combined_df['forward_Forward Result'] +
                    0.4 * combined_df['forward_Back Result'] +
                    5 * (combined_df['forward_Recovery Factor'] + combined_df['Recovery Factor'])
                )


                merged_dfs[os.path.basename(base_name)] = combined_df
                processed.update({base_name, forward_name})

                
                

                combined_df.to_csv(f"{os.path.splitext(base_name)[0]}_table.csv", index=False, encoding='utf-8-sig')
                log_to_ui(f"💾 Saved CSV: {os.path.splitext(base_name)[0]}_table.csv")

            # ✅ Store merged DataFrames in main window

            Logger.info(f" merged.keys() =  {merged_dfs.keys()}")
            self.main_window.report_dfs = merged_dfs

            # ✅ Remove all ".forward.xml" entries from report_files list
            if hasattr(self.main_window, "report_files"):
                before_count = len(self.main_window.report_files)
                self.main_window.report_files = [
                    f for f in self.main_window.report_files if not f.endswith(".forward.xml")
                ]
                Logger.info(f"🧹 Removed forward XML files. Report files reduced from {before_count} → {len(self.main_window.report_files)}")

            Logger.info(f"📘 Successfully parsed and merged {len(merged_dfs)} reports.")
            Logger.info(f"📂 Final merged report keys: {list(merged_dfs.keys())}")

            self.ui.reset_button.show()
            self.ui.start_button.hide()
            self.ui.start_button.setText("Start")
            self.ui.start_button.setEnabled(True)

            QMessageBox.information(self.ui, "Success", f"✅ Parsed and merged {len(merged_dfs)} XML reports successfully!")


        def on_error(err):
            log_to_ui(f"❌ Error while processing XML reports: {err}")
            self.ui.start_button.setText("Start")
            self.ui.start_button.setEnabled(True)
            

        # ============================
        # Run in Background Thread
        # ============================
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)

    def reset_all_fields(self):
        """
        Resets all user input fields, selections, and logs to their default states.
        """
        try:
            Logger.info("Initiating reset process for all input fields...")

            self.main_window.report_name = None  # Used for saving reports (Value Set in SetFinder and Used in Set Generator )
            self.report_df = pd.DataFrame()  # Used for saving reports (Value Set in SetFinder and Used in Set Generator )
            self.file_path = None

            self.main_window.report_dfs = {}
            self.main_window.report_files = []
            self.main_window.report_properties = {}
            self.main_window.selected_report_index = 0

            # --- Reset date fields ---
            self.ui.start_date_input.setDate(QDate.currentDate())
            self.ui.end_date_input.setDate(QDate.currentDate())

            # --- Reset dropdowns ---
            self.ui.account_dropdown.setCurrentIndex(0)

            # --- Clear line edits ---
            self.ui.report_dir_input.clear()
            self.ui.balance_input.clear()
            self.ui.risk_trade_input.clear()
            self.ui.max_consec_loss_input.clear()

            # --- Reset numeric input ---
            self.ui.trade_input.setValue(0)

            # --- Reset toggle state ---
            self.ui.toggle_btn.setChecked(False)

            # --- Clear logs ---
            self.ui.log_text.clear()

            # --- Reset Start/Reset buttons ---
            self.ui.start_button.setText("Start")
            self.ui.reset_button.hide()
            self.ui.start_button.show()

        

            Logger.info("✅ All input fields successfully reset.")
            self.ui.log_text.append("✅ All fields have been reset to default values.")

        except Exception as e:
            Logger.error(f"Error while resetting UI fields: {e}")
            QMessageBox.critical(
                self.ui,
                "Reset Error",
                f"❌ Failed to reset input fields.\nError: {str(e)}"
            )


    def compute_custom_score(self, forward_result, back_result, forward_recovery, back_recovery):
        """
        Compute a custom score based on forward/backward results and recovery factors.
        """
        try:
            score = (0.6 * forward_result) + (0.4 * back_result) + (5 * (forward_recovery + back_recovery))
            return score
        except Exception as e:
            Logger.errors(f"❌ Error computing custom score: {e}")
            return 0



