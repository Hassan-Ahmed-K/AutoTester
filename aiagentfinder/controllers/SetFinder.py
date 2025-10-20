import os
import pandas as pd
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from aiagentfinder.utils.logger import Logger
from aiagentfinder.utils.workerThread import ThreadRunner
from PyQt5.QtCore import Qt, QDate


class SetFinderController:
    def __init__(self, ui):
        self.ui = ui
        self.runner = ThreadRunner()
        self.main_window = self.ui.parent()


        # self.file_path = None
        self.doc_properties = {}


        self.ui.htm_dir_btn.clicked.connect(self.browse_report_directory)
        self.ui.toggle_btn.stateChanged.connect(self.on_toggle_trade_filter)
        self.ui.start_button.clicked.connect(self.read_xml_table_data)
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

        # Check for .htm or .xml files
        report_files = [
            f for f in os.listdir(dir_path)
            if f.lower().endswith((".htm", ".html", ".xml"))
        ]

        if not report_files:
            QMessageBox.warning(
                self.ui,
                "No Report Files Found",
                "The selected folder does not contain any .htm or .xml files.\n"
                "Please select a valid folder containing report files."
            )
            return

        self.main_window.report_name = report_files[0]
        self.ui.report_dir_input.setText(dir_path)
        self.main_window.file_path = os.path.join(dir_path, report_files[0])
        Logger.info(f"📄 Report file selected: {self.main_window.file_path}")
        Logger.info(f"📄 Report file self.ui.report_name: {self.main_window.report_name}")

        # ✅ Just start async read — do not unpack result here
        self.read_xml()

    def read_xml(self):
        """Parses the selected XML file (self.file_path) in a background thread."""

        if not self.main_window.file_path or not os.path.exists(self.main_window.file_path):
            Logger.error("❌ No valid XML file selected.")
            return

        Logger.info(f"📂 Starting XML parsing for: {self.main_window.file_path}")
        self.ui.start_button.setText("Reading XML...")
        self.ui.start_button.setEnabled(False)

        def task():
            try:
                Logger.debug(f"Parsing XML file: {self.main_window.file_path}")
                tree = ET.parse(self.main_window.file_path)
                root = tree.getroot()

                namespaces = {
                    'o': 'urn:schemas-microsoft-com:office:office',
                    'ss': 'urn:schemas-microsoft-com:office:spreadsheet'
                }

                doc_props_dict = {}
                doc_props = root.find('o:DocumentProperties', namespaces)

                if doc_props is not None:
                    Logger.info("Extracting DocumentProperties...")
                    for child in doc_props:
                        tag_name = child.tag.split('}')[-1]
                        value = child.text.strip() if child.text else ""
                        doc_props_dict[tag_name] = value
                        Logger.debug(f"{tag_name}: {value}")
                else:
                    Logger.warning("No DocumentProperties found in XML.")

                return root, doc_props_dict

            except Exception as e:
                Logger.error(f"XML reading error: {e}")
                raise

        def on_done(result):
            if not result or not isinstance(result, tuple):
                Logger.error("❌ Invalid result returned from XML thread.")
                QMessageBox.warning(self.ui, "Warning", "XML reading completed, but no valid data was returned.")
                self.ui.start_button.setText("Start")
                self.ui.start_button.setEnabled(True)
                return

            root, doc_props_dict = result
            self.doc_properties = doc_props_dict

            Logger.info("✅ XML DocumentProperties extracted successfully.")
            Logger.info(f"📘 Keys found: {', '.join(doc_props_dict.keys()) or 'None'}")

            # ✅ Now populate inputs here (safe place)
            self.populate_inputs_from_doc_props()

            self.ui.start_button.setText("Start")
            self.ui.start_button.setEnabled(True)

            Logger.info("XML reading completed successfully.")

        def on_error(err):
            Logger.error(f"❌ Failed to read XML file: {err}")
            self.ui.start_button.setText("Start")
            self.ui.start_button.setEnabled(True)
            QMessageBox.critical(self.ui, "Error", f"❌ XML Reading Failed:\n{str(err)}")

        Logger.debug("🚀 Starting background thread for XML reading...")
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)

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

    def read_xml_table_data(self):
        """
        Reads the selected XML file (self.file_path) and extracts tabular data
        from <ss:Row> elements in a separate thread. The data is logged, displayed in the UI,
        and saved as a CSV file.
        """

        # --- Utility function to log to both Logger and UI ---
        def log_to_ui(message):
            Logger.info(message)
            self.ui.log_text.append(message)
            self.ui.log_text.verticalScrollBar().setValue(
                self.ui.log_text.verticalScrollBar().maximum()
            )

        # --- Guard clause ---
        if not self.main_window.file_path or not os.path.exists(self.main_window.file_path):
            log_to_ui("❌ No valid XML file path found. Please select a valid report file first.")
            return

        # --- Update UI button states ---
        self.ui.start_button.setText("Processing...")
        self.ui.start_button.setEnabled(False)
        log_to_ui(f"🚀 Starting XML table extraction thread for: {self.main_window.file_path}")

        # ============================
        # TASK (runs in background)
        # ============================
        def task():
            """Reads XML, processes table, merges duplicate columns, shows empty cells if no value, and saves CSV."""
            try:
                # --- Step 1: Read XML ---
                log_to_ui(f"📂 Reading XML file: {self.main_window.file_path}")
                tree = ET.parse(self.main_window.file_path)
                root = tree.getroot()

                ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
                rows = []

                for row in root.findall('.//ss:Row', ns):
                    cells = [
                        (cell.find('ss:Data', ns).text if cell.find('ss:Data', ns) is not None else '')
                        for cell in row.findall('ss:Cell', ns)
                    ]
                    rows.append(cells)

                if not rows:
                    log_to_ui("⚠️ No rows found in XML file.")
                    Logger.warning("XML file appears to be empty.")
                    return None

                # --- Step 2: Convert rows to DataFrame ---
                df = pd.DataFrame(rows)

                # --- Step 3: Set first row as header ---
                if len(df) > 1:
                    new_header = df.iloc[0]
                    df = df[1:]
                    df.columns = new_header
                    df.reset_index(drop=True, inplace=True)
                    Logger.info("✅ Header successfully set from the first row.")
                else:
                    Logger.warning("⚠️ XML file contains only one row. Using generic column names.")

                # --- Step 4: Merge duplicate columns ---

                # Merge Trades
                trades_cols = [c for c in ['Bk Trades', 'Fwd Trades'] if c in df.columns]
                if trades_cols:
                    df['Trades'] = df[trades_cols].fillna(0).astype(float).sum(axis=1)
                    Logger.info(f"✅ Merged Trades columns: {trades_cols}")

                # Merge Profit
                profit_cols = [c for c in ['Total Profit', 'Est Bk Weekly Profit'] if c in df.columns]
                if profit_cols:
                    df['Profit'] = df[profit_cols].fillna(0).astype(float).sum(axis=1)
                    Logger.info(f"✅ Merged Profit columns: {profit_cols}")

                # --- Step 5: Define final column mapping ---
                column_mapping = {
                    "Pass No": "Pass",
                    "Bk Recovery": "Recovery Factor",
                    "Fwd Recovery": "Sharpe Ratio",
                    "Total Profit": "Profit",                       # merged column
                    "Est Fwd Weekly Profit": "Expected Payoff",
                    "Est Bwd Weekly Profit": "Expected Payoff",
                    "Trades": "Trades", 
                    "Multiplier": "Profit Factor",
                    "POW Score": "Custom"
                }

                # --- Step 6: Add missing columns ---
                df_copy = df.copy()
                for col in column_mapping.values():
                    if col not in df_copy.columns:
                        df_copy[col] = ""

                # --- Step 7: Filter, rename, and replace NaN with empty string ---
                filtered_df = df_copy[list(column_mapping.values())].rename(
                    columns={v: k for k, v in column_mapping.items()}
                )
                filtered_df.reset_index(drop=True, inplace=True)
                filtered_df = filtered_df.fillna("")  # replace any remaining NaN with empty string

                Logger.info(f"✅ Filtered DataFrame with {len(filtered_df.columns)} columns.")
                Logger.info(f"Headers: {filtered_df.columns.tolist()}")
                Logger.info("\n" + filtered_df.head().to_string(index=False))

                # --- Step 8: Save to CSV ---
                output_csv = os.path.join(os.path.dirname(self.main_window.file_path), "xml_retrieved_table.csv")
                filtered_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
                log_to_ui(f"💾 Table data saved successfully to: {output_csv}")
                Logger.info(f"🧾 CSV saved. Total rows: {len(filtered_df)}")

                return filtered_df

            except Exception as e:
                Logger.error(f"❌ Error processing XML: {str(e)}")
                log_to_ui(f"❌ Error: {str(e)}")
                return None



        # ============================
        # CALLBACKS (main thread)
        # ============================
        def on_done(result):
            if result is not None:
                log_to_ui("✅ XML table extraction completed successfully.")
                self.ui.start_button.hide()
                self.ui.reset_button.show()
                self.main_window.report_df = result
                Logger.info(f"Report name set to: {self.main_window.report_name}")
                Logger.info(f"Report DataFrame set with {len(self.main_window.report_df)} rows.")
            else:
                log_to_ui("⚠️ No data extracted from XML file.")
            self.ui.start_button.setText("Start")
            self.ui.start_button.setEnabled(True)

        def on_error(err):
            log_to_ui(f"❌ Error while reading XML table data: {err}")
            self.ui.start_button.setText("Start")
            self.ui.start_button.setEnabled(True)

        # ============================
        # Run in background thread
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


