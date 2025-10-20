import os
import pandas as pd
from aiagentfinder.utils.logger import Logger
from aiagentfinder.utils.workerThread import ThreadRunner
from PyQt5.QtCore import Qt, QDate, QItemSelectionModel, QItemSelection
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QFileDialog, QTableWidgetSelectionRange, QTableWidget, QMessageBox


class SetGeneratorController:
    def __init__(self,ui):

        self.ui = ui
        self.runner = ThreadRunner()
        self.main_window = self.ui.parent()
        self.logger = Logger()

        self.optimisation_files = {}

        self.selected_optimization = []
        self.pair_selected = []

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



    def update_pairs_box(self, report_name):
    
        self.ui.pairs_box.clear()
        self.ui.pairs_box.addItems([report_name])

        Logger.info(f"Pairs box updated with report name: {report_name}")


    def show_dataframe_in_table(self, df: pd.DataFrame):
        """
        Populate the QTableWidget with the given DataFrame in a background thread.
        """

        if df is None or df.empty:
            Logger.info("⚠️ No data to display.")
            self.ui.table.clear()
            self.ui.table.setRowCount(0)
            self.ui.table.setColumnCount(0)
            return

        Logger.info(f"📂 Starting to populate table with {len(df)} rows...")

        def task():
            """
            Background thread: Prepare table data.
            We don't touch UI elements here to avoid thread issues.
            """
            try:
                df_copy = df.copy()
                df_copy.columns = [str(col).strip() for col in df_copy.columns]
                df_copy.reset_index(drop=True, inplace=True)

                # Prepare table data as a list of lists
                table_data = []
                for _, row in df_copy.iterrows():
                    table_data.append([("" if pd.isna(val) else str(val)) for val in row])

                headers = df_copy.columns.tolist()
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
        if not hasattr(self.main_window, "report_df") or self.main_window.report_df.empty:
            if hasattr(self.ui, "bottom_message"):
                self.ui.bottom_message.append("⚠️ No data available to filter.")
            return

        print("self.main_window.report_df.head() = ")
        print(self.main_window.report_df.head())

        # ✅ Filter when toggle is ON
        if state:
            df_sorted = self.main_window.report_df.copy()

            print(f"df_sorted before sorting =  {df_sorted.columns}")

            if "POW Score" in df_sorted.columns:
                df_sorted = df_sorted.sort_values(by="POW Score", ascending=False).head(top_n)
                self.show_dataframe_in_table(df_sorted)
                if hasattr(self.ui, "bottom_message"):
                    self.ui.bottom_message.append(f"✅ Showing top {top_n} rows by POW Score.")
            else:
                if hasattr(self.ui, "bottom_message"):
                    self.ui.bottom_message.append("⚠️ 'POW Score' column not found in the data.")
        else:
            # ✅ Toggle off → reset full table
            self.show_dataframe_in_table(self.main_window.report_df)
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
        if not hasattr(self.main_window, "report_df") or self.main_window.report_df.empty:
            if hasattr(self.ui, "bottom_message"):
                self.ui.bottom_message.append("⚠️ No data available to sort.")
            return

        df = self.main_window.report_df.copy()


        print("df columns before handling duplicates:", df.columns.tolist())

        if state:
            df = df.sort_values(by="Total Profit", ascending=False)
            self.show_dataframe_in_table(df)
            if hasattr(self.ui, "bottom_message"):
                self.ui.bottom_message.append(f"✅ Ranked by '{"Total Profit"}' (Descending).")
        else:
            self.show_dataframe_in_table(self.main_window.report_df)
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


