import os
import pandas as pd
import json
from aiagentfinder.utils.logger import Logger
from aiagentfinder.utils.workerThread import ThreadRunner
from PyQt5.QtCore import Qt, QDate, QItemSelectionModel, QItemSelection
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QFileDialog, QTableWidgetSelectionRange, QTableWidget, QMessageBox
import re
from datetime import datetime
import random
import numpy as np


class SetGeneratorController:
    def __init__(self,ui):

        self.ui = ui
        self.runner = ThreadRunner()
        self.main_window = self.ui.parent()
        self.logger = Logger()

        self.optimisation_files = {}

        self.selected_optimization = []
        self.pair_selected = []
        self.report_df = pd.DataFrame()
        self.title = ""
        self.symbol = ""

        self.lotSize = None
        self.report_file = ""

        # Load dynamic mapping
        self.config_mapping = self.load_mapping()

        # Sorting state
        self.sort_column = "custom_score"
        self.sort_ascending = False

        Logger.info("Set Generator Controller Initialized")


        # In your setup
        self.ui.toggle_top_10.toggled.connect(lambda checked, btn=self.ui.toggle_top_10: self.filter_10(checked, btn))
        self.ui.toggle_top_100.toggled.connect(lambda checked, btn=self.ui.toggle_top_100: self.filter_100(checked, btn))
        self.ui.deselect_btn.clicked.connect(self.deselect_all_rows)
        self.ui.toggle_result.toggled.connect(lambda checked: self.filter_by_profit(checked))
        self.ui.toggle_selected.toggled.connect(self.filter_selected_rows)
        self.ui.select_files_btn.clicked.connect(self.select_optimisation_files)
        self.ui.table.itemSelectionChanged.connect(self.update_pass_number)
        self.ui.opt_files.itemSelectionChanged.connect(self.on_opt_files_selection)
        # self.ui.pairs_box.itemSelectionChanged.connect(self.on_pairs_box_selection)
        self.ui.table.cellClicked.connect(self.toggle_row_selection)
        self.ui.table.mousePressEvent = self.table_mouse_press_event
        self.ui.generate_set_btn.clicked.connect(self.generate_set_file)
        # self.ui.toggle_Generate_magic.toggled.connect(self.on_generate_magic)
        self.ui.toggle_Multiplier.toggled.connect(self.on_multiplier)

        self.ui.pairs_box.itemClicked.connect(self.on_pair_clicked)
        self.ui.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

        self.toggle_group = [
            self.ui.toggle_result,
            self.ui.toggle_selected,
            self.ui.toggle_top_10,
            self.ui.toggle_top_100,
        ]

        # Connect each toggle to its own handler
        for toggle in self.toggle_group:
            toggle.toggled.connect(lambda checked, t=toggle: self.ensure_exclusive_toggle(t, checked))


    def update_pairs_box(self, report_files):

        if not report_files:
            self.clear_pairs_and_table()
            return

        report_names = [
            os.path.splitext(os.path.basename(f))[0]
            for f in self.main_window.report_files
        ]

        self.ui.pairs_box.clear()
        self.ui.pairs_box.addItems(report_names)

        self.report_file = os.path.basename(
            self.main_window.report_files[self.main_window.selected_report_index]
        )

        # Get dataframe safely
        self.report_df = self.main_window.report_dfs.get(self.report_file, pd.DataFrame())

        # Update UI
        print('------------------------------------------------------------------')
        print(self.report_file)
        self.title = self.main_window.report_properties[self.report_file]['Title'].split(",")[0]
        self.symbol = self.title.split()[1]
        print('------------------------------------------------------------------')

        if self.ui.pairs_box.count() > 0:
            item = self.ui.pairs_box.item(self.main_window.selected_report_index)
            item.setSelected(True)
            self.ui.pairs_box.setCurrentItem(item)

        self.calculate_estimated_profits(self.report_df)

        # Default sort when loading a new pair
        if "custom_score" in self.report_df.columns:
            self.report_df["custom_score"] = pd.to_numeric(self.report_df["custom_score"], errors="coerce").fillna(0)
            self.report_df = self.report_df.sort_values(by="custom_score", ascending=False)
            self.sort_column = "custom_score"
            self.sort_ascending = False

        self.show_dataframe_in_table(self.report_df)

        Logger.info(f"Pairs box updated with: {report_names}")


    def clear_pairs_and_table(self):
        self.ui.pairs_box.clear()
        self.report_df = pd.DataFrame()
        self.show_dataframe_in_table(self.report_df)  # shows empty table
        Logger.info("Pairs box + table cleared due to no report files.")

    def show_dataframe_in_table(self, df: pd.DataFrame):
        """
        Populate the QTableWidget with the given DataFrame in a background thread.
        """

        if df is None or df.empty:
            # Logger.info("⚠️ No data to display.")
            # self.ui.table.clear()
            # self.ui.table.setRowCount(0)
            # self.ui.table.setColumnCount(0)
            # return

            print(df.columns)
            
            Logger.info("⚠️ No data to display.")
            default_headers = [ "Pass No", "Bk Recovery", "Fwd Recovery", "Est Bk Weekly Profit",
            "Est Fwd Weekly Profit", "Bk Trades", "Fwd Trades",
            "Multiplier", "Total Profit", "Custom Score"]  # ← customize this list
            self.ui.headers = getattr(self.ui, "headers", default_headers)

            # Clear old content but keep table visible
            self.ui.table.clearContents()
            self.ui.table.setRowCount(0)

            # Create columns with headers
            self.ui.table.setColumnCount(len(self.ui.headers))
            self.ui.table.setHorizontalHeaderLabels(self.ui.headers)

            Logger.info(f"🧱 Showing skeleton headers: {self.ui.headers}")
            return

        Logger.info(f"📂 Starting to populate table with {len(df)} rows...")

        def task():
            """
            Background thread: Prepare table data.
            We don't touch UI elements here to avoid thread issues.
            """
            try:

                # df_copy.columns = [str(col).strip() for col in df_copy.columns]

                                    # --- Column mapping ---
                column_mapping = {
                    "Pass No": "Pass",
                    "Bk Recovery": "Recovery Factor",
                    "Fwd Recovery": "forward_Recovery Factor",
                    "Est Bwd Weekly Profit": "Estimated_Backward_Weekly_Profit",
                    "Est Fwd Weekly Profit": "Estimated_Forward_Weekly_Profit",
                    "BK Trades": "Trades",
                    "Fwd Trades": "forward_Trades",
                    "Multiplier": "multiplier",
                    "Total Profit": "Total_Profit",
                    "Custom Score": "custom_score"
                }

                df_copy = df.copy()
                
                # --- Respect current sort state ---
                if self.sort_column in df_copy.columns:
                    df_copy[self.sort_column] = pd.to_numeric(df_copy[self.sort_column], errors="coerce").fillna(0)
                    df_copy = df_copy.sort_values(by=self.sort_column, ascending=self.sort_ascending)

                df_copy.reset_index(drop=True, inplace=True)

                



                for col in column_mapping.values():
                    if col not in df_copy.columns:
                        df_copy[col] = ""

                filtered_df = df_copy[list(column_mapping.values())].rename(
                    columns={v: k for k, v in column_mapping.items()}
                ).fillna("").reset_index(drop=True)



                # Prepare table data as a list of lists
                table_data = []
                for _, row in filtered_df.iterrows():
                    formatted_row = []
                    for val in row:
                        if pd.isna(val) or val == "":
                            formatted_row.append("")
                        else:
                            try:
                                # Try to format as float with max 2 decimal places
                                fval = float(val)
                                formatted_row.append(f"{round(fval, 2):g}")
                            except (ValueError, TypeError):
                                formatted_row.append(str(val))
                    table_data.append(formatted_row)

                headers = filtered_df.columns.tolist()
                return headers, table_data

            except Exception as e:
                raise e

        def on_done(result):
            """
            Runs in the main thread. Populate the QTableWidget.
            """
            if not result:
                Logger.error("❌ No table data returned from thread.")
                return

            headers, table_data = result

            # Clear and set up table
            self.ui.table.clear()
            # self.ui.table.clearContents()
            self.ui.table.setRowCount(0)
            self.ui.table.setColumnCount(len(headers))
            self.ui.table.setHorizontalHeaderLabels(headers)

            # Populate table
            for row_idx, row_values in enumerate(table_data):
                self.ui.table.insertRow(row_idx)
                for col_idx, value in enumerate(row_values):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.ui.table.setItem(row_idx, col_idx, item)

            # Resize columns
            header_widget = self.ui.table.horizontalHeader()
            header_widget.setSectionResizeMode(QHeaderView.Stretch)
        

            Logger.info(f"✅ Table populated successfully with {len(table_data)} rows and {len(headers)} columns.")

        def on_error(err):
            Logger.error(f"❌ Failed to populate table: {err}")
            QMessageBox.critical(self.ui, "Error", f"Failed to populate table:\n{str(err)}")

        # Run the task in background using your ThreadRunner
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)

    def deselect_all_rows(self):
        """Clears all selected rows in the table."""
        self.ui.table.clearSelection()
        Logger.info("Selected rows cleared in the table.")

    def filter_rows(self, top_n, state):
        """
        Show top N rows based on Custom Score when toggle is active.
        Reset to full data when toggle is turned off.
        """
        # ✅ Ensure report_df exists
        if not hasattr(self, "report_df") or self.report_df.empty:
            if hasattr(self.ui, "bottom_message"):
                self.ui.bottom_message.append("⚠️ No data available to filter.")
            return

        print("self.report_df.head() = ")
        print(self.report_df.head())

        # ✅ Filter when toggle is ON
        if state:
            df_sorted = self.report_df.copy()

            print(f"df_sorted before sorting =  {df_sorted.columns}")

            if "custom_score" in df_sorted.columns:
                df_sorted["custom_score"] = pd.to_numeric(df_sorted["custom_score"], errors="coerce").fillna(0)
                df_sorted = df_sorted.sort_values(by="custom_score", ascending=False).head(top_n)
                self.show_dataframe_in_table(df_sorted)
                if hasattr(self.ui, "bottom_message"):
                    self.ui.bottom_message.append(f"✅ Showing top {top_n} rows by Custom Score.")
            elif "Custom" in df_sorted.columns:
                df_sorted["Custom"] = pd.to_numeric(df_sorted["Custom"], errors="coerce").fillna(0)
                df_sorted = df_sorted.sort_values(by="Custom", ascending=False).head(top_n)
                self.show_dataframe_in_table(df_sorted)
                if hasattr(self.ui, "bottom_message"):
                    self.ui.bottom_message.append(f"✅ Showing top {top_n} rows by Custom Score.")
            else:
                if hasattr(self.ui, "bottom_message"):
                    self.ui.bottom_message.append("⚠️ 'Custom Score' column not found in the data.")
        else:
            # ✅ Toggle off → reset full table
            self.show_dataframe_in_table(self.report_df)
            if hasattr(self.ui, "bottom_message"):
                self.ui.bottom_message.append("🔄 Showing all rows again.")

    def filter_10(self, checked, sender_button):
        if checked:
            print(f"Toggled ON: {sender_button.text()}")
            self.filter_rows(10, True)
        else:
            print(f"Toggled OFF: {sender_button.text()}")
            self.filter_rows(100, False)

    def filter_100(self, checked, sender_button):
        if checked:
            print(f"Toggled ON: {sender_button.text()}")
            self.filter_rows(100, True)
        else:
            print(f"Toggled OFF: {sender_button.text()}")
            self.filter_rows(100, False)
   
    def filter_by_profit(self, state):
        """
        Toggle to sort and display rows by Total Profit.
        When turned ON, show DataFrame sorted by Total Profit (descending).
        When turned OFF, reset to full report_df.
        """
        if not hasattr(self, "report_df") or self.report_df.empty:
            if hasattr(self.ui, "bottom_message"):
                self.ui.bottom_message.append("⚠️ No data available to sort.")
            return

        df = self.report_df.copy()

        print(df.columns)


        print("df columns before handling duplicates:", df.columns.tolist())

        if state:
            df = df.sort_values(by="Total_Profit", ascending=False)
            self.show_dataframe_in_table(df)
            if hasattr(self.ui, "bottom_message"):
                self.ui.bottom_message.append(f"✅ Ranked by '{"Total Profit"}' (Descending).")
        else:
            self.show_dataframe_in_table(self.report_df)
            if hasattr(self.ui, "bottom_message"):
                self.ui.bottom_message.append("🔄 Showing original unranked data.")

    def filter_selected_rows(self, checked):
        """
        Show only selected rows if toggle is checked, else show all rows.
        """
        for row in range(self.ui.table.rowCount()):
            # Check if the row is selected
            row_selected = any(
                self.ui.table.item(row, col) is not None and self.ui.table.item(row, col).isSelected()
                for col in range(self.ui.table.columnCount())
            )
            # Hide row if toggle is ON and row is not selected
            self.ui.table.setRowHidden(row, checked and not row_selected)

    def select_optimisation_files(self):
        """
        Opens a file dialog (main thread) and processes selected .set files in a background thread.
        """

        parent_widget = getattr(self, "ui", None)

        # --- Step 1: File dialog (must be main thread) ---
        files, _ = QFileDialog.getOpenFileNames(
            parent_widget,
            "Select Optimisation Files",
            self.main_window.data_folder,
            "SET Files (*.set)"
        )

        if not files:
            return

        Logger.info(f"📂 {len(files)} optimisation file(s) selected.")

        # --- Step 2: Process files in background ---
        def task():
            """
            Background thread: add files to dictionary with unique keys.
            """
            new_items = []
            for file_path in files:
                base_name = os.path.basename(file_path)
                unique_name = base_name
                counter = 1

                while unique_name in self.optimisation_files:
                    name_part, ext = os.path.splitext(base_name)
                    unique_name = f"{name_part}_{counter}{ext}"
                    counter += 1

                # Store in dictionary
                self.optimisation_files[unique_name] = file_path
                new_items.append(unique_name)

            return new_items

        def on_done(result):
            """
            Runs in main thread: add items to QListWidget.
            """
            for name in result:
                self.ui.opt_files.addItem(name)
            Logger.info(f"✅ {len(result)} file(s) added to optimisation list.")

        def on_error(err):
            Logger.error(f"❌ Error processing optimisation files: {err}")
            QMessageBox.critical(self.ui, "Error", f"Failed to process optimisation files:\n{str(err)}")

        # --- Step 3: Run background thread ---
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)

    def update_pass_number(self):
        """
        Updates the Pass Number input based on table selection.
        """
        selected_items = self.ui.table.selectedItems()
        
        if not selected_items:
            self.ui.pass_number.setText("")  # No selection
            return

        # Get all unique selected rows
        selected_rows = sorted(set(item.row() for item in selected_items))
        
        if len(selected_rows) == 1:
            # Only one row selected → get Pass No from that row
            row = selected_rows[0]
            pass_no_item = self.ui.table.item(row, 0)  # assuming Pass No is column 0
            if pass_no_item:
                self.ui.pass_number.setText(pass_no_item.text())
            else:
                self.ui.pass_number.setText("")
        else:
            # Multiple rows selected
            self.ui.pass_number.setText("Multiple Selection")

    def on_opt_files_selection(self):
        self.selected_optimization = [item.text() for item in self.ui.opt_files.selectedItems()]
        file_path = self.optimisation_files[self.selected_optimization[0]]
        self.lotSize =  self.extract_lot_size(file_path)

        print("Selected files:", self.selected_optimization)

    def on_header_clicked(self, logical_index):
        """
        Handles sorting the table when a header is clicked (Excel-like behavior).
        """
        if self.report_df.empty:
            return

        header_text = self.ui.table.horizontalHeaderItem(logical_index).text()
        
        # Map UI header back to internal dataframe column name
        column_mapping = {
            "Pass No": "Pass",
            "Bk Recovery": "Recovery Factor",
            "Fwd Recovery": "forward_Recovery Factor",
            "Est Bwd Weekly Profit": "Estimated_Backward_Weekly_Profit",
            "Est Fwd Weekly Profit": "Estimated_Forward_Weekly_Profit",
            "BK Trades": "Trades",
            "Fwd Trades": "forward_Trades",
            "Multiplier": "multiplier",
            "Total Profit": "Total_Profit",
            "Custom Score": "custom_score"
        }

        internal_col = column_mapping.get(header_text)
        if not internal_col or internal_col not in self.report_df.columns:
            return

        # Toggle sort order if clicking the same column
        if self.sort_column == internal_col:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = internal_col
            self.sort_ascending = False  # Default to descending for new columns

        # Update the table
        self.show_dataframe_in_table(self.report_df)
        
        self.log_to_ui(f"📊 Sorted by {header_text} ({'Ascending' if self.sort_ascending else 'Descending'})")

    def toggle_row_selection(self, row, column):
        """
        Toggle selection of a single row in QTableWidget without affecting other rows.
        """
        selection_model = self.ui.table.selectionModel()

        # Create selection for the row
        top_left = self.ui.table.model().index(row, 0)
        bottom_right = self.ui.table.model().index(row, self.ui.table.columnCount() - 1)
        selection = QItemSelection(top_left, bottom_right)

        # Toggle the row's selection
        selection_model.select(selection, QItemSelectionModel.Toggle)

    def table_mouse_press_event(self, event):
        index = self.ui.table.indexAt(event.pos())
        if not index.isValid():
            return  # Click outside any row

        row = index.row()
        selection_model = self.ui.table.selectionModel()

        # Check if row is already selected
        row_selected = False
        for sel_range in self.ui.table.selectedRanges():
            if sel_range.topRow() <= row <= sel_range.bottomRow():
                row_selected = True
                break

        # Create selection for the whole row
        top_left = self.ui.table.model().index(row, 0)
        bottom_right = self.ui.table.model().index(row, self.ui.table.columnCount() - 1)
        selection = QItemSelection(top_left, bottom_right)

        # Toggle selection
        if row_selected:
            selection_model.select(selection, QItemSelectionModel.Deselect)
        else:
            selection_model.select(selection, QItemSelectionModel.Select)

        event.accept()

    def log_to_ui(self, message: str):
        """
        Append a message to the bottom_message QTextEdit and scroll to the bottom.
        """
        if hasattr(self.ui, "bottom_message") and self.ui.bottom_message is not None:
            # Append message with newline
            self.ui.bottom_message.append(message)
            
            # Ensure the last message is visible
            self.ui.bottom_message.verticalScrollBar().setValue(
                self.ui.bottom_message.verticalScrollBar().maximum()
            )
        else:
            print("⚠️ bottom_message widget not found. Message:", message)

    def on_pair_clicked(self, item):
        index = self.ui.pairs_box.row(item)

        if (index == self.main_window.selected_report_index):
            return

        self.main_window.selected_report_index = index
        print(f"🟢 Clicked item: {item.text()} | Index: {index}")

        self.report_file = os.path.basename(self.main_window.report_files[index])
        self.report_df = self.main_window.report_dfs.get(self.report_file, pd.DataFrame())

        print('------------------------------------------------------------------')
        print(self.report_file)
        self.title = self.main_window.report_properties[self.report_file]['Title'].split(",")[0]
        self.symbol = self.title.split()[1]
        print('------------------------------------------------------------------')

        self.calculate_estimated_profits(self.report_df)
        Logger.info(f"Selected report filename: {self.report_file}")

        self.show_dataframe_in_table(self.report_df)

    

        #, forward_fraction: str = "1/3", total_months: int = 12

    def calculate_estimated_profits(self, df: pd.DataFrame): 
        """
        Safely calculates estimated forward and backward weekly profits based on report dates.
        """
        try:
            # --- Step 1: Get report dates safely ---
            start_date, end_date, forward_fraction = self.get_report_dates()

            # --- Validate and parse forward ratio ---
            try:
                fwd_ratio = float(eval(str(forward_fraction)))  # handles '1/3' or numeric values
            except Exception:
                print(f"⚠️ Invalid forward fraction '{forward_fraction}', defaulting to 1/3.")
                fwd_ratio = 1/3

            # --- Step 2: Calculate total months safely ---
            if start_date.isValid() and end_date.isValid():
                start_dt = datetime(start_date.year(), start_date.month(), start_date.day())
                end_dt = datetime(end_date.year(), end_date.month(), end_date.day())

                # total months difference
                total_months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
                if total_months <= 0:
                    print("⚠️ Invalid or zero total months — setting to 1 to avoid division by zero.")
                    total_months = 1
            else:
                print("⚠️ Invalid start or end date — setting total months to 1.")
                total_months = 1

            # --- Step 3: Split forward/backward periods ---
            forward_months = total_months * fwd_ratio
            backward_months = total_months - forward_months

            # Prevent zero division
            if forward_months <= 0: forward_months = 1
            if backward_months <= 0: backward_months = 1

            # --- Convert to weeks (approx 4 weeks per month) ---
            forward_weeks = forward_months * 4
            backward_weeks = backward_months * 4

            # --- Step 4: Ensure profit columns exist ---
            if "Profit" not in df.columns or "forward_Profit" not in df.columns:
                raise KeyError("DataFrame must contain 'Profit' and 'forward_Profit' columns.")

            df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce").fillna(0)
            df["forward_Profit"] = pd.to_numeric(df["forward_Profit"], errors="coerce").fillna(0)

            # --- Step 5: Compute weekly estimated profits ---
            df["Estimated_Backward_Weekly_Profit"] = df["Profit"] / backward_weeks
            df["Estimated_Forward_Weekly_Profit"] = df["forward_Profit"] / forward_weeks

            # --- Step 6: Total profit ---

            df["Profit"] = pd.to_numeric(df["Profit"], errors="coerce")
            df["forward_Profit"] = pd.to_numeric(df["forward_Profit"], errors="coerce")

            df["Total_Profit"] = df["Profit"] + df["forward_Profit"]

            print("Total_Profit calculation completed.")

            df['multiplier'] = np.where(
                df['Total_Profit'] != 0,
                (1000 / df['Total_Profit']).round(2),
                0
            )


            print("--------------------------------------------------------")
            print(df.columns)
            print("--------------------------------------------------------")

        except Exception as e:
            print(f"❌ Error in calculate_estimated_profits: {e}")
            # return df

    def get_report_dates(self):
        """
        Safely extract start_date, end_date, and forward_period from report_properties.
        If any error occurs, default values are used.
        """
        try:
            # --- Validate report index and get key safely ---
            report_files = getattr(self.main_window, "report_files", [])
            selected_index = getattr(self.main_window, "selected_report_index", None)

            if not report_files or selected_index is None or selected_index >= len(report_files):
                raise IndexError("Invalid or missing report index.")

            report_key = os.path.basename(report_files[selected_index])

            # --- Get report data dictionary ---
            report_data = self.main_window.report_properties.get(report_key, {})
            if not isinstance(report_data, dict):
                raise ValueError("Report data is not a valid dictionary.")

            # --- Extract title safely ---
            title = report_data.get("Title", "")
            if not title:
                raise ValueError("Title not found in report data.")

            # --- Extract dates using regex ---
            date_match = re.search(r"(\d{4}\.\d{2}\.\d{2})-(\d{4}\.\d{2}\.\d{2})", title)
            if date_match:
                start_str, end_str = date_match.groups()
                start_qdate = QDate.fromString(start_str, "yyyy.MM.dd")
                end_qdate = QDate.fromString(end_str, "yyyy.MM.dd")

                # Handle invalid date parsing
                if not start_qdate.isValid() or not end_qdate.isValid():
                    raise ValueError("Invalid date format in title.")
            else:
                raise ValueError("Date range not found in title.")

            # --- Get forward period safely ---
            forward_period = report_data.get("forward_period", 1/3)
            try:
                forward_period = float(forward_period)
            except (TypeError, ValueError):
                forward_period = 1/3

            return start_qdate, end_qdate, forward_period

        except Exception as e:
            # --- Catch any unexpected error and fallback ---
            print(f"⚠️ Error while reading report dates: {e}")
            return QDate(), QDate(), 1/3
        
    def ensure_exclusive_toggle(self, active_toggle, checked):
        """
        Ensure only one toggle stays ON at a time.
        When one is turned ON, all others turn OFF with animation.
        """
        if checked:
            for toggle in self.toggle_group:
                if toggle is not active_toggle:
                    toggle.blockSignals(True)
                    toggle.setChecked(False)
                    toggle.blockSignals(False)

                    # 🔄 Force re-animation if supported
                    if hasattr(toggle, "animate"):
                        toggle.animate(False)
                    elif hasattr(toggle, "update"):
                        toggle.update()

    def load_mapping(self):
        """Loads mapping from mapping.json or returns default mapping."""
        mapping_path = os.path.join(os.getcwd(), "mapping.json")
        default_mapping = {
            "EmaTimeframe": "forward_EmaTimeframe",
            "EmaPeriods": "forward_EmaPeriods",
            "UseRSICriteria": "forward_UseRSICriteria",
            "RsiTimeframe": "forward_RsiTimeframe",
            "RsiPeriod": "forward_RsiPeriod",
            "RsiSellLevel": "forward_RsiSellLevel",
            "Multiplier": "multiplier"
        }
        if os.path.exists(mapping_path):
            try:
                with open(mapping_path, 'r') as f:
                    data = json.load(f)
                    Logger.info(f"✅ Loaded dynamic mapping from {mapping_path}")
                    return data
            except Exception as e:
                Logger.error(f"❌ Error loading mapping.json: {e}")
        
        Logger.info("⚠️ mapping.json not found, using default internal mapping.")
        return default_mapping

    def parse_set_file(self, path):
        """Parses a .set file into a dictionary of key-value pairs."""
        params = {}
        try:
            with open(path, "r", encoding="utf-16") as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines, parse Key=Value
                    if "=" in line and not line.startswith(";"):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            key, val = parts
                            key_stripped = key.strip()
                            # Skip UI separators (stage0, stage1, etc.)
                            if not key_stripped.lower().startswith("stage"):
                                params[key_stripped] = val.strip()
        except Exception as e:
            Logger.error(f"❌ Error parsing template SET file {path}: {e}")
        return params

    def generate_set_file(self):
        """
        Generates individual .set files using a selected SET file as a template
        and overlaying values from the report DataFrame based on mapping.json.
        """
        # --- Step 1: Gather selected rows from table ---
        selected_rows = []
        headers = [self.ui.table.horizontalHeaderItem(i).text() for i in range(self.ui.table.columnCount())]
        
        for sel_range in self.ui.table.selectedRanges():
            for row in range(sel_range.topRow(), sel_range.bottomRow() + 1):
                row_data = {}
                for col in range(self.ui.table.columnCount()):
                    header = headers[col]
                    cell = self.ui.table.item(row, col)
                    row_data[header] = cell.text() if cell else ""
                selected_rows.append(row_data)

        if not selected_rows:
            QMessageBox.warning(self.ui, "Warning", "No rows selected to generate .set file.")
            return

        # --- Step 2: Get Template File ---
        selected_opt_files = getattr(self, "selected_optimization", [])
        template_path = None
        ea_name = self.title  # Fallback
        if selected_opt_files:
            template_path = self.optimisation_files.get(selected_opt_files[0])
            ea_name = selected_opt_files[0].replace(".set", "")
            Logger.info(f"Using template: {selected_opt_files[0]}")

        # --- Step 3: Save Dialog ---
        suggested_name = self.report_file.replace('.forward', '').replace('.xml', '')
        save_path, _ = QFileDialog.getSaveFileName(
            self.ui,
            "Save SET files (Prefix)",
            os.path.join(self.main_window.base_process_folder, suggested_name),
            "SET Files (*.set)"
        )
        if not save_path:
            return
        
        base_path = save_path.replace(".set", "")

        # --- Step 4: Background Thread ---
        def task():
            try:
                # 1. Parse Template if available
                template_params = {}
                if template_path:
                    template_params = self.parse_set_file(template_path)

                # 2. Prepare Data
                selected_df = pd.DataFrame(selected_rows)
                result_df = self.report_df.merge(
                    selected_df,
                    how="left",
                    left_on="Pass",        # column in report_df
                    right_on="Pass No",    # column in selected_rows
                    indicator=True         # adds a column showing join status
                )

                # Only keep rows that were selected (matched in selected_df)
                result_df = result_df[result_df["_merge"] == "both"]

                # 3. Pre-calculate Min/Max ranges for all mapped parameters
                param_ranges = {}
                config_mapping_flat = {}
                for section, fields in self.config_mapping.items():
                    if isinstance(fields, dict):
                        for k, v in fields.items(): config_mapping_flat[k] = v
                    else:
                        config_mapping_flat[section] = fields

                for ea_key, csv_col in config_mapping_flat.items():
                    if csv_col in result_df.columns:
                        numeric_vals = pd.to_numeric(result_df[csv_col], errors='coerce').dropna()
                        if not numeric_vals.empty:
                            param_ranges[ea_key] = (numeric_vals.min(), numeric_vals.max())

                # Special range for LotSize
                lot_vals = []
                base_lot = float(self.lotSize or 0.01)
                for _, row in result_df.iterrows():
                    if self.ui.toggle_Multiplier.isChecked():
                        mult = float(row.get("multiplier", 1.0))
                        lot_vals.append(base_lot * mult)
                    else:
                        lot_vals.append(base_lot)
                if lot_vals:
                    param_ranges["LotSize"] = (min(lot_vals), max(lot_vals))

                # 4. Generate files for each pass
                for _, row in result_df.iterrows():
                    pass_no = row.get("Pass")
                    file_path = f"{base_path}_{pass_no}.set"

                    # Start with template values
                    final_params = template_params.copy()

                    # Overlay values from CSV using config_mapping (Nested)
                    for section, fields in self.config_mapping.items():
                        if isinstance(fields, dict):
                            for ea_key, csv_col in fields.items():
                                if csv_col in row:
                                    final_params[ea_key] = str(row[csv_col])
                                elif "||" in str(csv_col) or str(csv_col) != str(ea_key):
                                    # Treat as literal if it has "||" or is different from the key name
                                    final_params[ea_key] = str(csv_col)
                        else:
                            if fields in row:
                                final_params[section] = str(row[fields])
                            elif "||" in str(fields) or str(fields) != str(section):
                                final_params[section] = str(fields)

                    # Special handling for LotSize current value
                    if self.ui.toggle_Multiplier.isChecked():
                        multiplier = float(row.get("multiplier", 1.0))
                        final_params["LotSize"] = f"{base_lot * multiplier:.2f}"
                    else:
                        final_params["LotSize"] = f"{base_lot:.2f}"

                    # --- Special Fallbacks for General & Licensing ---
                    # Use API Key from UI if not in template/CSV
                    if not final_params.get("apiKey") or final_params.get("apiKey") == "":
                        final_params["apiKey"] = self.ui.api_key.text().strip()
                    
                    # Auto-generate descriptions if missing
                    if not final_params.get("StrategyDescription"):
                        final_params["StrategyDescription"] = f"{self.symbol}_Pass_{pass_no}"
                    if not final_params.get("TradeComment"):
                        final_params["TradeComment"] = f"{self.symbol}_Pass_{pass_no}"

                    # Write the file
                    with open(file_path, "w", encoding="utf-16") as f:
                        f.write(f"; saved on {datetime.now().strftime('%Y.%m.%d %H:%M:%S')}\n")
                        f.write(f"; this file contains input parameters for testing/optimizing {ea_name} expert advisor\n")
                        f.write("; to use it in the strategy tester, click Load in the context menu of the Inputs tab\n")
                        f.write(f"; Symbol={self.symbol} | Pass={pass_no}\n;\n")

                        written_keys = set()

                        for section_name, fields in self.config_mapping.items():
                            if isinstance(fields, dict):
                                f.write(f";~~~~~~~~~{section_name}~~~~~~~~~\n")
                                for ea_key in fields.keys():
                                    if ea_key in final_params:
                                        new_val = str(final_params[ea_key])
                                        original_str = template_params.get(ea_key, "")
                                        
                                        if "||" in new_val:
                                            # Already a literal optimization string
                                            f.write(f"{ea_key}={new_val}\n")
                                        elif ea_key in param_ranges:
                                            # Standard 5-part format: current||start||step||stop||Y/N
                                            p_min, p_max = param_ranges[ea_key]
                                            
                                            # If min == max, reset min to 0 as requested
                                            if p_min == p_max:
                                                p_min = 0
                                            
                                            # Try to get step from template, otherwise default
                                            step = "1"
                                            if "||" in original_str:
                                                parts_orig = original_str.split("||")
                                                if len(parts_orig) >= 3:
                                                    step = parts_orig[2]
                                            
                                            flag = "Y" if p_min != p_max else "N"
                                            f.write(f"{ea_key}={new_val}||{p_min}||{step}||{p_max}||{flag}\n")
                                        elif "||" in original_str:
                                            # Fallback: maintain template structure but update current value
                                            parts = original_str.split("||")
                                            parts[0] = new_val
                                            f.write(f"{ea_key}={'||'.join(parts)}\n")
                                        else:
                                            f.write(f"{ea_key}={new_val}\n")
                                        
                                        written_keys.add(ea_key)
                                f.write("\n")

                        remaining_keys = set(final_params.keys()) - written_keys
                        if remaining_keys:
                            f.write(";~~~~~~~~~Other Parameters~~~~~~~~~\n")
                            for k in sorted(remaining_keys):
                                val = str(final_params[k])
                                original_str = template_params.get(k, "")
                                
                                if "||" in val:
                                    f.write(f"{k}={val}\n")
                                elif k in param_ranges:
                                    p_min, p_max = param_ranges[k]
                                    if p_min == p_max:
                                        p_min = 0
                                        
                                    step = "1"
                                    if "||" in original_str:
                                        parts_orig = original_str.split("||")
                                        if len(parts_orig) >= 3:
                                            step = parts_orig[2]
                                    
                                    flag = "Y" if p_min != p_max else "N"
                                    f.write(f"{k}={val}||{p_min}||{step}||{p_max}||{flag}\n")
                                elif "||" in original_str:
                                    parts = original_str.split("||")
                                    parts[0] = val
                                    f.write(f"{k}={'||'.join(parts)}\n")
                                else:
                                    f.write(f"{k}={val}\n")
                            f.write("\n")

                return base_path

            except Exception as e:
                raise RuntimeError(f"Error generating .set files: {str(e)}")

        def on_done(result):
            self.log_to_ui(f"✅ Dynamic .set files generated successfully at:\n{result}_*.set")

        def on_error(err):
            self.log_to_ui(f"❌ Failed to generate .set files: {err}")
            QMessageBox.critical(self.ui, "Error", str(err))

        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)

    def generate_magic_string(self, count):
        values = []

        for _ in range(count):
            n = random.randint(1, 8)
            first = random.randint(1, 9)
            rest = ''.join(str(random.randint(0, 9)) for _ in range(n - 1))
            num = str(first) + rest
            values.append(num)

        return "MAGIC_NUMBER=" + "||".join(values) + "||N"

    def read_set_file(self, path):
        with open(path, encoding="utf-16") as f:
            data = f.read()
            return data

    def extract_lot_size(self, path):
            data = self.read_set_file(path)
            for line in data.splitlines():
                line = line.strip()                
                if line.startswith("LotSize="):
                    first_value = line.split("=")[1].split("||")[0]
                    return first_value
                
            return None

    def on_multiplier(self, state):
        print("Multiplier toggled:", state)
        # your logic here
