
import os
import pandas as pd
from aiagentfinder.utils.ThreadRunnerV2 import ThreadRunnerV2
from aiagentfinder.utils import Logger 
from PyQt5.QtWidgets import QLineEdit, QFileDialog,QListWidget, QTableWidgetItem, QHeaderView
import matplotlib.pyplot as plt



class SetCompareController:
    def __init__(self, ui):
        self.ui = ui
        self.main_window = self.ui.parent()
        self.runner = ThreadRunnerV2(self.main_window)
        self.logger = Logger()

        self.selected_set_files = set()

        self.csv_files = set()
        self.htm_files = set()
        self.set_files = set()

        self.csv_dir = ""
        self.htm_dir = ""
        self.set_dir = ""

        # self.ui.compare_button.clicked.connect(self.on_compare_button_clicked)
        self.ui.csv_input.textChanged.connect(self.on_csv_input_changed)
        self.ui.htm_input.textChanged.connect(self.on_htm_input_changed)
        self.ui.set_input.textChanged.connect(self.on_set_input_changed)
        self.ui.csv_browse.clicked.connect(lambda: self.browse_folder(self.ui.csv_input))
        self.ui.htm_browse.clicked.connect(lambda: self.browse_folder(self.ui.htm_input))
        self.ui.set_browse.clicked.connect(lambda: self.browse_folder(self.ui.set_input))
        self.ui.compare_button.clicked.connect(self.on_compare_button_clicked)
        self.ui.deselect_button.clicked.connect(self.on_deselect_button_clicked)
        self.ui.show_graph_button.clicked.connect(self.on_show_graph_clicked)



        # self.ui.draw_input.textChanged.connect(self.on_draw_input_changed)


    def browse_folder(self, target_input: QLineEdit):
        try:
            # Default path logic
            start_dir = getattr(self.main_window, "data_folder", "")
            self.logger.debug(f"Starting folder browse. Default: {start_dir}")

            dialog = QFileDialog(self.main_window, "Select Folder")
            dialog.setFileMode(QFileDialog.Directory)
            dialog.setOption(QFileDialog.ShowDirsOnly, True)

            # Apply default folder if available
            if start_dir:
                dialog.setDirectory(start_dir)
                self.logger.debug(f"Dialog default directory set to: {start_dir}")

            if dialog.exec_():
                folder = dialog.selectedFiles()[0]
                target_input.setText(folder)
                self.logger.info(f"User selected folder: {folder}")
            else:
                self.logger.info("Folder selection canceled by user.")

        except Exception as e:
            self.logger.error("Error in browse_folder", e)

    def on_csv_input_changed(self):
        self.refresh_selected_set_files()

    def on_htm_input_changed(self):
        self.refresh_selected_set_files()

    def on_set_input_changed(self):
        self.refresh_selected_set_files()

    def on_deselect_button_clicked(self):
        if hasattr(self.ui, "csv_list") and self.ui.csv_list is not None:
            self.ui.csv_list.clearSelection()

    def log_to_ui(self, message: str):
        """
        Append a message to the bottom_message QTextEdit and scroll to the bottom.
        """
        if hasattr(self.ui, "message_log") and self.ui.message_log is not None:
            # Append message with newline
            self.ui.message_log.append(message)
            
            # Ensure the last message is visible
            self.ui.message_log.verticalScrollBar().setValue(
                self.ui.message_log.verticalScrollBar().maximum()
            )
        else:
            print("⚠️ bottom_message widget not found. Message:", message)

    def update_csv_list_widget(self):
        """Update the CSV QListWidget with current CSV files."""
        try:
            self.ui.csv_list.clear()
            self.logger.debug("Cleared CSV list widget.")

            for f in self.csv_files:
                try:
                    name_without_ext = os.path.splitext(os.path.basename(f))[0]
                    self.ui.csv_list.addItem(name_without_ext)
                    self.logger.debug(f"Added to CSV list widget: {name_without_ext}")
                except Exception as inner_e:
                    self.logger.error(f"Failed to add file to CSV list widget: {f}", inner_e)

            # Allow multiple selection
            self.ui.csv_list.setSelectionMode(QListWidget.MultiSelection)
            self.logger.debug("Set CSV list widget selection mode to MultiSelection.")

            # Select all items by default
            self.ui.csv_list.selectAll()
            self.logger.info("All CSV files selected in the list widget.")

        except Exception as e:
            self.logger.error("Failed to update CSV list widget.", e)

    def on_compare_button_clicked(self):
        """
        Trigger CSV compare in background thread.
        """
        items = self.ui.csv_list.selectedItems()
        if not items:
            QMessageBox.warning(self.ui, "No files", "Select at least one CSV from the list.")
            return

        selected_names = [it.text() for it in items]

        # disable UI buttons
        self.ui.compare_button.setEnabled(False)
        self.ui.show_graph_button.hide()
        self.ui.export_profile_button.hide()
        self.log_to_ui("Compare started...")

        # ---- task to run in background ----
        def task(worker=None):
            try:
                csv_data_map = {}
                file_suffixes = []

                for name in selected_names:
                    if worker and getattr(worker, "_stop", False):
                        return {"error": "STOPPED"}

                    file_name = f"{name}.csv"
                    csv_file = os.path.join(self.csv_dir, file_name)

                    # read CSV (tab separated, fallback UTF-16)
                    try:
                        try:
                            df = pd.read_csv(csv_file, sep="\t")
                        except UnicodeDecodeError:
                            df = pd.read_csv(csv_file, sep="\t", encoding="utf-16")
                    except Exception as e:
                        return {"error": f"Failed reading {csv_file}: {e}"}

                    # clean column names
                    df.columns = [c.strip().replace("<", "").replace(">", "") for c in df.columns]

                    if "DATE" not in df.columns:
                        continue  # skip file

                    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
                    df = df.dropna(subset=["DATE"])
                    if df.empty:
                        continue

                    # convert numeric columns
                    for col in df.columns:
                        if col == "DATE":
                            continue
                        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")

                    suffix = os.path.splitext(file_name)[0]
                    df = df.rename(columns={c: f"{c}_{suffix}" for c in df.columns if c != "DATE"})

                    csv_data_map[file_name] = df
                    file_suffixes.append(suffix)

                if not csv_data_map:
                    return {"error": "NO_VALID_CSV"}

                # merge inner on DATE
                dfs = list(csv_data_map.values())
                merged_df = dfs[0].copy()
                for df in dfs[1:]:
                    merged_df = pd.merge(merged_df, df, on="DATE", how="inner")

                merged_df = merged_df.sort_values("DATE").reset_index(drop=True)

                # ensure numeric
                for col in merged_df.columns:
                    if col != "DATE":
                        merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce")

                # compute equity aggregates
                equity_cols = [c for c in merged_df.columns if c.startswith("EQUITY_")]
                if equity_cols:
                    merged_df["AVG_EQUITY"] = merged_df[equity_cols].mean(axis=1)
                    merged_df["SUM_EQUITY"] = merged_df[equity_cols].sum(axis=1)

                # compute balance aggregates
                balance_cols = [c for c in merged_df.columns if c.startswith("BALANCE_")]
                if balance_cols:
                    merged_df["AVG_BALANCE"] = merged_df[balance_cols].mean(axis=1)
                    merged_df["SUM_BALANCE"] = merged_df[balance_cols].sum(axis=1)

                # save merged CSV
                # out_path = os.path.join(self.csv_dir, "merged_output.csv")
                # try:
                #     merged_df.to_csv(out_path, index=False)
                # except Exception as e:
                #     return {"df": merged_df, "out_path": out_path, "files": file_suffixes, "save_error": str(e)}

                return {"df": merged_df, "files": file_suffixes}

            except Exception as exc:
                return {"error": traceback.format_exc()}

        # ---- callback to update UI ----
        def handle_compare_result(result):
            self.ui.compare_button.setEnabled(True)

            if not isinstance(result, dict):
                self.log_to_ui(f"Unexpected result: {result}")
                return

            if "error" in result:
                self.log_to_ui(f"Compare failed: {result['error']}")
                self.ui.drawdown_analysis.clear()
                self.ui.portfolio_stats.clear()
                return

            merged_df = result.get("df")
            files = result.get("files", [])

            if merged_df is None or merged_df.empty:
                self.log_to_ui("Merged dataframe is empty after merge.")
                self.ui.drawdown_analysis.clear()
                self.ui.portfolio_stats.clear()
                return

            self.merged_df = merged_df

            # show buttons
            self.ui.show_graph_button.show()
            self.ui.export_profile_button.show()

            # update tables
            try:
                self.show_drawdown_table(merged_df)
                self.show_monthly_portfolio_stats(merged_df)
            except Exception as e:
                self.log_to_ui(f"Table update failed: {e}")

            self.log_to_ui("Compare process completed.")

        # ---- run task in thread ----
        self.runner = ThreadRunnerV2(parent=self.ui)
        self.runner.on_result = handle_compare_result
        self.runner.run(task, show_dialog=True)

    def show_monthly_portfolio_stats(self, merged_df):
        if merged_df is None or merged_df.empty:
            self.log_to_ui("merged_df is empty.")
            self.ui.portfolio_stats.clear()
            return

        df = merged_df.copy()

        # Ensure DATE is datetime
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

        # Extract Month number + name (so order stays correct)
        df["MONTH_NUM"] = df["DATE"].dt.month
        df["MONTH_NAME"] = df["DATE"].dt.strftime("%b")

        # Get the last balance entry for each month
        month_summary = (
            df.sort_values("DATE")
            .groupby("MONTH_NUM")["AVG_BALANCE"]
            .last()
        )

        # Map month numbers → names
        month_summary.index = month_summary.index.map({
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
            5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
            9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        })

        # Remove missing months
        month_summary = month_summary.dropna()

        # Compute total
        total_balance = month_summary.sum()

        # Table headers
        headers = list(month_summary.index) + ["Total"]

        # Setup table
        self.ui.portfolio_stats.clear()
        self.ui.portfolio_stats.setRowCount(1)
        self.ui.portfolio_stats.setColumnCount(len(headers))
        self.ui.portfolio_stats.setHorizontalHeaderLabels(headers)

        # Fill the row with month balances
        for col_idx, value in enumerate(month_summary.values):
            self.ui.portfolio_stats.setItem(
                0, col_idx, QTableWidgetItem(str(round(value, 2)))
            )

        # Add final Total column
        self.ui.portfolio_stats.setItem(
            0, len(headers) - 1, QTableWidgetItem(str(round(total_balance, 2)))
        )

        # Stretch to full width
        header = self.ui.portfolio_stats.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.ui.portfolio_stats.resizeRowsToContents()

        # UI log instead of print
        self.log_to_ui("Monthly portfolio stats updated (clean & sorted).")

    def show_drawdown_table(self, merged_df):

        if merged_df is None or merged_df.empty:
            self.log_to_ui("merged_df is empty.")
            self.ui.drawdown_analysis.clear()
            return

        df = merged_df.copy()

        # Detect EQUITY columns
        equity_cols = [col for col in df.columns if col.startswith("EQUITY_")]

        # Build nicer headers based on file names
        file_headers = [col.replace("EQUITY_", "") for col in equity_cols]

        # Add SUM_EQUITY if missing
        if "SUM_EQUITY" not in df.columns and equity_cols:
            df["SUM_EQUITY"] = df[equity_cols].sum(axis=1)

        # 🔹 Apply filter based on draw_input value
        draw_threshold = int(self.ui.draw_input.text())  # QDoubleSpinBox value
        df = df[df["SUM_EQUITY"] >= draw_threshold]

        if df.empty:
            self.log_to_ui(f"No rows match the filter (SUM_EQUITY ≥ {draw_threshold}).")
            self.ui.drawdown_analysis.clear()
            return

        # FINAL HEADERS
        headers = ["Date & Time", "DD Total", "#"] + file_headers

        # Setup table
        self.ui.drawdown_analysis.clear()
        self.ui.drawdown_analysis.setColumnCount(len(headers))
        self.ui.drawdown_analysis.setRowCount(len(df))
        self.ui.drawdown_analysis.setHorizontalHeaderLabels(headers)

        # Fill rows
        for row in range(len(df)):
            # Date
            self.ui.drawdown_analysis.setItem(
                row, 0, QTableWidgetItem(str(df["DATE"].iloc[row]))
            )

            # DD Total → SUM_EQUITY
            dd_value = df["SUM_EQUITY"].iloc[row] if "SUM_EQUITY" in df else ""
            self.ui.drawdown_analysis.setItem(
                row, 1, QTableWidgetItem(str(round(dd_value, 2)) if dd_value != "" else "")
            )

            # Static value "15" in column #
            self.ui.drawdown_analysis.setItem(
                row, 2, QTableWidgetItem("15")
            )

            # Equity values for each file
            col_index = 3
            for col in equity_cols:
                val = df[col].iloc[row]
                self.ui.drawdown_analysis.setItem(
                    row, col_index, QTableWidgetItem(str(round(val, 2)))
                )
                col_index += 1

        # Stretch all columns to fill width
        header = self.ui.drawdown_analysis.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.ui.drawdown_analysis.resizeRowsToContents()

        self.log_to_ui(f"Drawdown table updated (rows with SUM_EQUITY ≥ {draw_threshold}).")

    def on_show_graph_clicked(self):
        if self.merged_df is None or self.merged_df.empty:
            self.log_to_ui("merged_df is empty.")
            return

        df = self.merged_df.copy()

        # Ensure DATE is datetime
        if "DATE" in df.columns:
            df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

        # Detect EQUITY columns
        equity_cols = [c for c in df.columns if c.startswith("EQUITY_")]

        if not equity_cols:
            self.log_to_ui("❌ No EQUITY_ columns found.")
            return


        plt.figure(figsize=(12, 6))

        for col in equity_cols:
            plt.plot(df["DATE"], df[col], label=col.replace("EQUITY_", ""))

        plt.title("Equity Curve Comparison")
        plt.xlabel("Date / Time")
        plt.ylabel("Equity")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()

        self.log_to_ui("Graph displayed successfully.")

    def refresh_selected_set_files(self):
        """Refresh list of valid files based on all 3 input folders."""
        try:
            self.csv_dir = self.ui.csv_input.text().strip()
            self.htm_dir = self.ui.htm_input.text().strip()
            self.set_dir = self.ui.set_input.text().strip()

            self.logger.info(f"CSV Dir: {self.csv_dir}")
            self.logger.info(f"HTM Dir: {self.htm_dir}")
            self.logger.info(f"SET Dir: {self.set_dir}")

            self.selected_set_files = set()

            # If SET folder empty, bounce
            if not os.path.isdir(self.set_dir):
                self.logger.warning(f"SET folder not found: {self.set_dir}")
                return

            def matches_set_file(f, set_files):
                try:
                    f_lower = f.lower()
                    for s in set_files:
                        name_without_ext = os.path.splitext(s)[0].lower()
                        if name_without_ext in f_lower:
                            return True
                    return False
                except Exception as e_inner:
                    self.logger.error(f"Error matching file: {f}", e_inner)
                    return False

            try:
                # All SET files
                set_files = set(os.listdir(self.set_dir))
                self.logger.debug(f"SET files found: {set_files}")
            except Exception as e:
                set_files = []
                self.logger.error("Error reading SET folder", e)
                return

            # Check CSV files
            try:
                if os.path.isdir(self.csv_dir):
                    for f in os.listdir(self.csv_dir):
                        if matches_set_file(f, set_files):
                            self.selected_set_files.add(f)
                            self.csv_files.add(f)
                            self.logger.debug(f"Selected CSV file: {f}")
                else:
                    self.logger.warning(f"CSV folder not found: {self.csv_dir}")
            except Exception as e:
                self.logger.error("Error scanning CSV folder", e)

            # Update CSV list widget
            try:
                self.update_csv_list_widget()
            except Exception as e:
                self.logger.error("Error updating CSV list widget", e)

            # Check HTM files
            try:
                if os.path.isdir(self.htm_dir):
                    for f in os.listdir(self.htm_dir):
                        if matches_set_file(f, set_files):
                            self.selected_set_files.add(f)
                            self.htm_files.add(f)
                            self.logger.debug(f"Selected HTM file: {f}")
                else:
                    self.logger.warning(f"HTM folder not found: {self.htm_dir}")
            except Exception as e:
                self.logger.error("Error scanning HTM folder", e)

            self.logger.info(f"Total Selected files: {self.selected_set_files}")

        except Exception as e:
            self.logger.error("Unexpected error in refresh_selected_set_files", e)



