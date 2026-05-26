import os
import shutil
import pandas as pd
import traceback
from aiagentfinder.utils.ThreadRunnerV2 import ThreadRunnerV2
from aiagentfinder.utils import Logger 
from PyQt5.QtWidgets import QLineEdit, QFileDialog,QListWidget,QTableWidget, QTableWidgetItem, QHeaderView,QLabel,QToolTip,QMessageBox,QInputDialog
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm
from PyQt5.QtCore import Qt
import numpy as np


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
        self.ui.export_profile_button.clicked.connect(self.export_files)



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
            self.ui.portfolio_stats.clear()
            return

        df = merged_df.copy()

        # ✅ Correct date parsing (IMPORTANT)
        df["DATE"] = pd.to_datetime(df["DATE"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["DATE"])

        df["MONTH_NUM"] = df["DATE"].dt.month

        # Detect BALANCE columns (per file)
        balance_cols = [c for c in df.columns if c.startswith("BALANCE_")]

        month_name_map = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
            5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
            9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }

        # Monthly portfolio value (table values)
        month_summary = (
            df.sort_values("DATE")
            .groupby("MONTH_NUM")["AVG_BALANCE"]
            .last()
            .dropna()
        )

        if month_summary.empty:
            self.ui.portfolio_stats.clear()
            return

        headers = [month_name_map[m] for m in month_summary.index] + ["Total"]

        table = self.ui.portfolio_stats
        table.clear()
        table.setRowCount(1)
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        # Fill month cells with FILE-BASED tooltips
        for col_idx, (month_num, value) in enumerate(month_summary.items()):
            item = QTableWidgetItem(str(round(value, 2)))
            item.setTextAlignment(Qt.AlignCenter)

            month_df = df[df["MONTH_NUM"] == month_num].sort_values("DATE")

            # Build tooltip per file
            tooltip_lines = []

            
            for col in balance_cols:
                start = month_df[col].iloc[0]
                end = month_df[col].iloc[-1]
                pnl = round(end - start, 2)
                color = "#22c55e" if pnl >= 0 else "#ef4444"

                file_name = col.replace("BALANCE_", "")
                # tooltip_lines.append(
                #     f"{file_name}\n"
                #     f"  Start: {round(start, 2)}\n"
                #     f"  End:   {round(end, 2)}\n"
                #     f"  PnL:   {pnl}\n"
                # )

                tooltip_lines.append(
                    f"<b>{file_name}</b><br>"
                    f"Start: {round(start, 2)}<br>"
                    f"End: {round(end, 2)}<br>"
                    f"PnL: <span style='color:{color}'>{pnl}</span><br><br>"
                )

            item.setToolTip("\n".join(tooltip_lines))
            table.setItem(0, col_idx, item)

        # Total column
        total_item = QTableWidgetItem(str(round(month_summary.sum(), 2)))
        total_item.setTextAlignment(Qt.AlignCenter)
        table.setItem(0, len(headers) - 1, total_item)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.resizeRowsToContents()

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
        self.ui.drawdown_analysis.setSortingEnabled(False)  # Disable while filling
        self.ui.drawdown_analysis.clear()
        self.ui.drawdown_analysis.setColumnCount(len(headers))
        self.ui.drawdown_analysis.setRowCount(len(df))
        self.ui.drawdown_analysis.setHorizontalHeaderLabels(headers)

        # Fill rows
        for row in range(len(df)):
            # Date (using EditRole for correct sorting)
            date_str = str(df["DATE"].iloc[row])
            date_item = QTableWidgetItem(date_str)
            self.ui.drawdown_analysis.setItem(row, 0, date_item)

            # DD Total → SUM_EQUITY (numeric sort)
            dd_value = df["SUM_EQUITY"].iloc[row] if "SUM_EQUITY" in df else 0.0
            dd_item = QTableWidgetItem()
            dd_item.setData(Qt.EditRole, float(round(dd_value, 2)))
            self.ui.drawdown_analysis.setItem(row, 1, dd_item)

            # Static value "15" in column #
            num_item = QTableWidgetItem()
            num_item.setData(Qt.EditRole, 15)
            self.ui.drawdown_analysis.setItem(row, 2, num_item)

            # Equity values for each file (numeric sort)
            col_index = 3
            for col in equity_cols:
                val = df[col].iloc[row]
                val_item = QTableWidgetItem()
                val_item.setData(Qt.EditRole, float(round(val, 2)))
                self.ui.drawdown_analysis.setItem(row, col_index, val_item)
                col_index += 1

        # Enable interactive sorting (Excel-like)
        self.ui.drawdown_analysis.setSortingEnabled(True)
        
        # Sort by Date & Time (column 0) ascending by default
        self.ui.drawdown_analysis.sortByColumn(0, Qt.AscendingOrder)

        # Stretch all columns to fill width
        header = self.ui.drawdown_analysis.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.ui.drawdown_analysis.resizeRowsToContents()

        self.log_to_ui(f"Drawdown table updated (rows with SUM_EQUITY ≥ {draw_threshold}). Default sort: DD Total.")

    def on_show_graph_clicked(self):
        if self.merged_df is None or self.merged_df.empty:
            self.log_to_ui("merged_df is empty.")
            return

        # --- Popup selection ---
        options = ["Equity", "Balance", "Both"]
        choice, ok = QInputDialog.getItem(
            self.ui, "Select Data to Plot", "Show:", options, 0, False
        )
        if not ok:
            self.log_to_ui("Graph cancelled by user.")
            return

        df = self.merged_df.copy()
        if "DATE" not in df.columns:
            self.log_to_ui("❌ No DATE column found.")
            return
        
        # Ensure DATE is datetime and sorted
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
        df = df.dropna(subset=["DATE"]).sort_values("DATE").reset_index(drop=True)

        # --- Select columns ---
        equity_cols = [c for c in df.columns if c.startswith("EQUITY_")] if choice in ["Equity", "Both"] else []
        balance_cols = [c for c in df.columns if c.startswith("BALANCE_")] if choice in ["Balance", "Both"] else []

        if not equity_cols and not balance_cols:
            self.log_to_ui("❌ No columns found to plot for selection.")
            return

        # --- Prepare colors ---
        total_lines = len(equity_cols) + len(balance_cols)
        color_map = plt.get_cmap("tab20")
        colors = [color_map(i % 20) for i in range(total_lines)]

        # Set style for a more premium dark look
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(13, 7), facecolor='#121212')
        ax.set_facecolor('#121212')

        # Plot Equity
        equity_handles = []
        for col, color in zip(equity_cols, colors[:len(equity_cols)]):
            line, = ax.plot(df["DATE"], df[col], label=col.replace("EQUITY_", ""), color=color, linewidth=1.5, alpha=0.9)
            equity_handles.append(line)

        # Plot Balance
        balance_handles = []
        for col, color in zip(balance_cols, colors[len(equity_cols):]):
            line, = ax.plot(df["DATE"], df[col], label=col.replace("BALANCE_", ""), color=color, linewidth=1.5, alpha=0.9, linestyle='--')
            balance_handles.append(line)

        # Title and labels
        ax.set_title({
            "Equity": "Equity Curve Comparison",
            "Balance": "Balance Curve Comparison",
            "Both": "Equity & Balance Comparison"
        }[choice], color='white', fontsize=14, pad=20)
        ax.set_xlabel("Date / Time", color='#bbbbbb')
        ax.set_ylabel("Value", color='#bbbbbb')
        ax.grid(True, alpha=0.15, color='gray', linestyle=':')

        # Customize ticks
        ax.tick_params(colors='#888888', labelsize=9)

        # --- Legends ---
        if equity_handles:
            legend_equity = ax.legend(handles=equity_handles, title="Equity", loc="upper left", fontsize=7, framealpha=0.1)
            ax.add_artist(legend_equity)

        if balance_handles:
            ax.legend(handles=balance_handles, title="Balance", loc="upper right", fontsize=7, framealpha=0.1)

        # --- Interactive Hover Detection ---
        # Map handles to column names and set picker radius for easier selection
        handle_to_col = {}
        for col, line in zip(equity_cols, equity_handles):
            handle_to_col[line] = col
            line.set_picker(10)
        for col, line in zip(balance_cols, balance_handles):
            handle_to_col[line] = col
            line.set_picker(10)

        # Pre-calculate numeric dates for fast searching
        x_data_numeric = mdates.date2num(df["DATE"].tolist())
        
        v_line = ax.axvline(x=df["DATE"].iloc[0], color='white', linestyle='-', alpha=0.3, visible=False)
        
        # Tooltip annotation
        annot = ax.annotate("", xy=(0,0), xytext=(15, 15),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round4,pad=0.5", fc="#1e1e1e", ec="#444444", alpha=0.9),
                            color="white", fontsize=8, fontfamily='monospace')
        annot.set_visible(False)

        def hover(event):
            hovered_lines = []
            if event.inaxes == ax:
                # Check if mouse is near any specific line(s)
                for line in equity_handles + balance_handles:
                    cont, _ = line.contains(event)
                    if cont:
                        hovered_lines.append(line)
                
                if hovered_lines:
                    # Highlight all active lines and dim others
                    for line in equity_handles + balance_handles:
                        if line in hovered_lines:
                            line.set_alpha(1.0)
                            line.set_linewidth(2.5)
                        else:
                            line.set_alpha(0.15)
                            line.set_linewidth(1.0)
                    
                    # Fast search for nearest date index
                    idx = np.searchsorted(x_data_numeric, event.xdata)
                    if idx >= len(x_data_numeric): idx = len(x_data_numeric) - 1
                    if idx > 0 and abs(event.xdata - x_data_numeric[idx-1]) < abs(event.xdata - x_data_numeric[idx]):
                        idx -= 1
                    
                    target_date = df["DATE"].iloc[idx]
                    
                    # Build multi-line tooltip text for all hovered lines
                    tooltip_lines = [f"DATE: {target_date.strftime('%Y-%m-%d %H:%M')}"]
                    tooltip_lines.append("-" * 35)
                    
                    for line in hovered_lines:
                        col_name = handle_to_col[line]
                        val = df[col_name].iloc[idx]
                        clean_name = col_name.replace("EQUITY_", "").replace("BALANCE_", "")[:25]
                        tooltip_lines.append(f"{clean_name:<25}: {val:>10.2f}")

                    annot.set_text("\n".join(tooltip_lines))
                    
                    # Anchor tooltip to the first hovered line's value
                    first_col = handle_to_col[hovered_lines[0]]
                    annot.xy = (target_date, df[first_col].iloc[idx])
                    
                    v_line.set_xdata([target_date, target_date])
                    v_line.set_visible(True)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return

            # Reset visibility and styles if no line is hovered
            if not hovered_lines:
                needs_redraw = False
                if v_line.get_visible():
                    v_line.set_visible(False)
                    annot.set_visible(False)
                    needs_redraw = True
                
                for line in equity_handles + balance_handles:
                    if line.get_alpha() != 0.9 or line.get_linewidth() != 1.5:
                        line.set_alpha(0.9)
                        line.set_linewidth(1.5)
                        needs_redraw = True
                
                if needs_redraw:
                    fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)

        plt.tight_layout()
        plt.show()
        self.log_to_ui(f"Interactive graph displayed: {choice}")

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

    def export_files(self):
        # Source directories
        csv_dir = self.ui.csv_input.text().strip()
        htm_dir = self.ui.htm_input.text().strip()
        set_dir = self.ui.set_input.text().strip()

        # Ask for export folder
        export_dir = QFileDialog.getExistingDirectory(self.ui, "Select Export Folder")
        if not export_dir:
            print("Export cancelled.")
            return

        # Selected CSVs from QListWidget (lowercase)
        selected_csv_files = [item.text().lower() for item in self.ui.csv_list.selectedItems()]

        # Generic copy helper (case-insensitive)
        def copy_matching_files(selected_files, src_dir, extensions=None):
            if not os.path.isdir(src_dir):
                print(f"Source folder not found: {src_dir}")
                return

            for f in os.listdir(src_dir):
                fname_lower = os.path.splitext(f)[0].lower()  # strip extension

                # Skip by extension if needed
                if extensions and not f.lower().endswith(tuple(extensions)):
                    continue

                if fname_lower in selected_files or selected_files == ["*"]:
                    src_path = os.path.join(src_dir, f)
                    dst_path = os.path.join(export_dir, f)
                    try:
                        shutil.copy2(src_path, dst_path)
                        print(f"Copied: {f}")
                    except Exception as e:
                        print(f"Error copying {f}: {e}")


        copy_matching_files(selected_csv_files, csv_dir, extensions=[".csv"])

        copy_matching_files(selected_csv_files, htm_dir, extensions=[".htm"])

        copy_matching_files(selected_csv_files, set_dir, extensions=[".set"])

        print(f"All selected files copied to {export_dir}")



