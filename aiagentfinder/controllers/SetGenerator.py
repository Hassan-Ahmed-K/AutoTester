import os
import pandas as pd
from aiagentfinder.utils.logger import Logger
from aiagentfinder.utils.workerThread import ThreadRunner
from PyQt5.QtCore import Qt, QDate, QItemSelectionModel, QItemSelection
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QFileDialog, QTableWidgetSelectionRange, QTableWidget, QMessageBox
import re
from datetime import datetime


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
        self.ui.pairs_box.itemSelectionChanged.connect(self.on_pairs_box_selection)
        self.ui.table.cellClicked.connect(self.toggle_row_selection)
        self.ui.table.mousePressEvent = self.table_mouse_press_event
        self.ui.generate_set_btn.clicked.connect(self.generate_set_file)

        # --- Inside your __init__ or setup function ---
        self.ui.pairs_box.itemClicked.connect(self.on_pair_clicked)

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
    
        
        report_names = [
            os.path.splitext(os.path.basename(f))[0]  # extract filename without extension
            for f in self.main_window.report_files
        ]
        self.ui.pairs_box.clear()
        self.ui.pairs_box.addItems(report_names)
        report_file = os.path.basename(self.main_window.report_files[self.main_window.selected_report_index])
        self.report_df = self.main_window.report_dfs.get(report_file, pd.DataFrame())

        self.calculate_estimated_profits(self.report_df)
        print(self.report_df)
        self.show_dataframe_in_table(self.report_df)

        Logger.info(f"Pairs box updated with report name: {report_names}")

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
            
            Logger.info("⚠️ No data to display.")
            default_headers = [ "Pass No", "Bk Recovery", "Fwd Recovery", "Est Bk Weekly Profit",
            "Est Fwd Weekly Profit", "Bk Trades", "Fwd Trades",
            "Multiplier", "Total Profit", "POW Score"]  # ← customize this list
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
                    "Multiplier": "Profit Factor",
                    "Total Profit": "Total_Profit",
                    "POW Score": "Custom"
                }

                df_copy = df.copy()
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
                    table_data.append([("" if pd.isna(val) else str(val)) for val in row])

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
        Show top N rows based on POW Score when toggle is active.
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

            if "Custom" in df_sorted.columns:
                df_sorted = df_sorted.sort_values(by="Custom", ascending=False).head(top_n)
                self.show_dataframe_in_table(df_sorted)
                if hasattr(self.ui, "bottom_message"):
                    self.ui.bottom_message.append(f"✅ Showing top {top_n} rows by POW Score.")
            else:
                if hasattr(self.ui, "bottom_message"):
                    self.ui.bottom_message.append("⚠️ 'POW Score' column not found in the data.")
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
            "",
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
        selected = [item.text() for item in self.ui.opt_files.selectedItems()]
        print("Selected files:", selected)

    def on_pairs_box_selection(self):
        selected = [item.text() for item in self.ui.pairs_box.selectedItems()]
        print("Selected pairs:", selected)

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

    def generate_set_file(self):
        """
        Generate a .set file containing selected table rows, selected optimization files,
        and selected pairs, running the file writing in a background thread.
        """
        # --- Step 1: Get selected table rows ---
        selected_rows = []
        for sel_range in self.ui.table.selectedRanges():
            for row in range(sel_range.topRow(), sel_range.bottomRow() + 1):
                row_data = [self.ui.table.item(row, col).text() if self.ui.table.item(row, col) else ""
                            for col in range(self.ui.table.columnCount())]
                selected_rows.append(row_data)

        # --- Step 2: Get selected optimization files ---
        selected_opt_files = [name for name in self.selected_optimization if name in self.optimisation_files]

        # --- Step 3: Get selected pairs ---
        selected_pairs = self.pair_selected

        if not (selected_rows or selected_opt_files or selected_pairs):
            self.log_to_ui("⚠️ Nothing selected to generate .set file!")
            return

        # --- Step 4: Ask for save location (main thread) ---
        save_path, _ = QFileDialog.getSaveFileName(
            self.ui,
            "Save SET file",
            self.main_window.file_path or "",
            "SET Files (*.set)"
        )
        if not save_path:
            return
        
        if save_path.lower().endswith(".xml"):
            save_path = save_path[:-4] + ".set"

        # Ensure .set extension
        if not save_path.lower().endswith(".set"):
            save_path += ".set"

        # --- Step 5: Define background task to write file ---
        def task():
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("# --- Selected Table Rows ---\n")
                for row in selected_rows:
                    f.write(", ".join(row) + "\n")

                f.write("\n# --- Selected Optimization Files ---\n")
                for name in selected_opt_files:
                    f.write(name + "\n")  # Only name shown
                    # Full path still available in self.optimisation_files[name]

                f.write("\n# --- Selected Pairs ---\n")
                for pair in selected_pairs:
                    f.write(pair + "\n")
            return save_path  # Return path for logging

        # --- Step 6: Define callback after thread finishes ---
        def on_done(result):
            self.log_to_ui(f"💾 .set file generated successfully:\n{result}")

        def on_error(err):
            self.log_to_ui(f"❌ Failed to generate .set file:\n{str(err)}")
            QMessageBox.critical(self.ui, "Error", f"Failed to generate .set file:\n{str(err)}")

        # --- Step 7: Run background thread ---
        self.runner = ThreadRunner(self.ui)
        self.runner.on_result = on_done
        self.runner.on_error = on_error
        self.runner.run(task)

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
        self.main_window.selected_report_index = index
        print(f"🟢 Clicked item: {item.text()} | Index: {index}")

        report_file = os.path.basename(self.main_window.report_files[index])
        self.report_df = self.main_window.report_dfs.get(report_file, pd.DataFrame())
        self.calculate_estimated_profits(self.report_df)
        Logger.info(f"Selected report filename: {report_file}")

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
            df["Total_Profit"] = df["Profit"] + df["forward_Profit"]

            return df

        except Exception as e:
            print(f"❌ Error in calculate_estimated_profits: {e}")
            return df

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
