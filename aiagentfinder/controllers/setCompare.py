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
                    # Rename columns to include suffix, EXCEPT DATE
                    df = df.rename(columns={c: f"{c}_{suffix}" for c in df.columns if c != "DATE"})

                    csv_data_map[file_name] = df
                    file_suffixes.append(suffix)

                if not csv_data_map:
                    return {"error": "NO_VALID_CSV"}

                # Set DATE as index for all dataframes to allow outer join
                for fn, df in csv_data_map.items():
                    df.set_index("DATE", inplace=True)

                # Outer join all dataframes on DATE index
                merged_df = pd.concat(csv_data_map.values(), axis=1)
                merged_df = merged_df.sort_index()

                # Forward-fill to propagate last known balance/equity, then backward-fill
                merged_df = merged_df.ffill().bfill()
                merged_df = merged_df.reset_index() # DATE is back as a column

                # Ensure all columns are numeric
                for col in merged_df.columns:
                    if col != "DATE":
                        merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce")

                # Compute aggregates
                equity_cols = [c for c in merged_df.columns if c.startswith("EQUITY_")]
                balance_cols = [c for c in merged_df.columns if c.startswith("BALANCE_")]

                # Average and Sum
                if equity_cols:
                    merged_df["AVG_EQUITY"] = merged_df[equity_cols].mean(axis=1)
                    merged_df["SUM_EQUITY"] = merged_df[equity_cols].sum(axis=1)
                if balance_cols:
                    merged_df["AVG_BALANCE"] = merged_df[balance_cols].mean(axis=1)
                    merged_df["SUM_BALANCE"] = merged_df[balance_cols].sum(axis=1)

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
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
        df = df.dropna(subset=["DATE"])

        df["PERIOD"] = df["DATE"].dt.to_period("M")
        periods = sorted(df["PERIOD"].unique())

        # Detect BALANCE columns (per file)
        balance_cols = [c for c in df.columns if c.startswith("BALANCE_")]

        if not balance_cols or not periods:
            self.ui.portfolio_stats.clear()
            return

        # Calculate monthly profit for each strategy
        strategy_profits = {}  # col -> {period: profit}
        strategy_start_end = {}  # col -> {period: (start, end)}

        for col in balance_cols:
            initial_balance = df[col].iloc[0]
            monthly_last_balances = df.groupby("PERIOD")[col].last()
            
            profits = {}
            start_end = {}
            prev_bal = initial_balance
            for period in periods:
                last_bal = monthly_last_balances.get(period, prev_bal)
                profits[period] = last_bal - prev_bal
                start_end[period] = (prev_bal, last_bal)
                prev_bal = last_bal
            
            strategy_profits[col] = profits
            strategy_start_end[col] = start_end

        # Portfolio profit per period
        portfolio_profits = {}
        for period in periods:
            portfolio_profits[period] = sum(strategy_profits[col][period] for col in balance_cols)

        headers = [p.strftime("%b %y") for p in periods] + ["Total"]

        table = self.ui.portfolio_stats
        table.clear()
        table.setRowCount(1)
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        # Fill month cells with FILE-BASED tooltips
        for col_idx, period in enumerate(periods):
            value = portfolio_profits[period]
            item = QTableWidgetItem(str(round(value, 2)))
            item.setTextAlignment(Qt.AlignCenter)

            # Build tooltip per file
            tooltip_lines = []
            for col in balance_cols:
                pnl = strategy_profits[col][period]
                start, end = strategy_start_end[col][period]
                color = "#22c55e" if pnl >= 0 else "#ef4444"
                file_name = col.replace("BALANCE_", "")

                tooltip_lines.append(
                    f"<b>{file_name}</b><br>"
                    f"Start: {round(start, 2)}<br>"
                    f"End: {round(end, 2)}<br>"
                    f"PnL: <span style='color:{color}'>{'+' if pnl >= 0 else ''}{round(pnl, 2)}</span><br><br>"
                )

            item.setToolTip("\n".join(tooltip_lines))
            table.setItem(0, col_idx, item)

        # Total column (sum of all monthly profits)
        total_profit = sum(portfolio_profits.values())
        total_item = QTableWidgetItem(str(round(total_profit, 2)))
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

        if not equity_cols:
            self.ui.drawdown_analysis.clear()
            return

        # 🔹 Resample to 30-minute intervals first - keep last record in each bucket, forward/backward fill
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
        df = df.dropna(subset=["DATE"])
        df = df.set_index("DATE")
        df = df.resample("30min").last().ffill().bfill()
        df = df.reset_index()

        # Calculate running loss (drawdown) for each strategy: cummax - current_equity
        loss_cols = []
        for col in equity_cols:
            loss_col_name = f"LOSS_{col.replace('EQUITY_', '')}"
            df[loss_col_name] = df[col].cummax() - df[col]
            loss_cols.append(loss_col_name)

        # Calculate combined drawdown (DD Total)
        df["DD_TOTAL"] = df[loss_cols].sum(axis=1)

        # Count active drawdowns (loss > 0)
        df["ACTIVE_COUNT"] = (df[loss_cols] > 0.0).sum(axis=1)

        # 🔹 Apply filter based on draw_input value
        draw_input_text = self.ui.draw_input.text().strip()
        try:
            draw_threshold = float(draw_input_text) if draw_input_text else 0.0
        except ValueError:
            draw_threshold = 1000.0  # fallback

        df = df[df["DD_TOTAL"] >= draw_threshold]

        if df.empty:
            self.log_to_ui(f"No rows match the filter (DD Total ≥ {draw_threshold}).")
            self.ui.drawdown_analysis.clear()
            return

        # FINAL HEADERS: Date & Time, DD Total, #, plus each strategy
        headers = ["Date & Time", "DD Total", "#"] + file_headers

        # Setup table
        self.ui.drawdown_analysis.setSortingEnabled(False)  # Disable while filling
        self.ui.drawdown_analysis.clear()
        self.ui.drawdown_analysis.setColumnCount(len(headers))
        self.ui.drawdown_analysis.setRowCount(len(df))
        self.ui.drawdown_analysis.setHorizontalHeaderLabels(headers)

        # Fill rows
        for row in range(len(df)):
            # Date & Time (using EditRole for correct sorting)
            date_str = str(df["DATE"].iloc[row])
            date_item = QTableWidgetItem(date_str)
            self.ui.drawdown_analysis.setItem(row, 0, date_item)

            # DD Total (numeric sort)
            dd_value = df["DD_TOTAL"].iloc[row]
            dd_item = QTableWidgetItem()
            dd_item.setData(Qt.EditRole, float(round(dd_value, 2)))
            self.ui.drawdown_analysis.setItem(row, 1, dd_item)

            # Number of active drawdowns (numeric sort)
            active_val = int(df["ACTIVE_COUNT"].iloc[row])
            active_item = QTableWidgetItem()
            active_item.setData(Qt.EditRole, active_val)
            self.ui.drawdown_analysis.setItem(row, 2, active_item)

            # Loss values for each file (numeric sort)
            col_index = 3
            for loss_col in loss_cols:
                val = df[loss_col].iloc[row]
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

        self.log_to_ui(f"Drawdown table updated (DD Total ≥ {draw_threshold}, sampled every 30 min). Rows: {len(df)}.")

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
            self.csv_files = set()
            self.htm_files = set()

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
            self.log_to_ui("Export cancelled.")
            return

        # Selected CSVs from QListWidget (lowercase)
        selected_csv_names = [item.text().lower() for item in self.ui.csv_list.selectedItems()]

        if not selected_csv_names:
            self.log_to_ui("No CSV files selected for export.")
            return

        # 1. Copy CSV files
        if os.path.isdir(csv_dir):
            for f in os.listdir(csv_dir):
                if f.lower().endswith(".csv"):
                    fname_lower = os.path.splitext(f)[0].lower()
                    if fname_lower in selected_csv_names:
                        shutil.copy2(os.path.join(csv_dir, f), os.path.join(export_dir, f))
                        self.log_to_ui(f"Copied CSV: {f}")

        # 2. Copy HTM files
        if os.path.isdir(htm_dir):
            for f in os.listdir(htm_dir):
                if f.lower().endswith((".htm", ".html")):
                    fname_lower = os.path.splitext(f)[0].lower()
                    if fname_lower in selected_csv_names:
                        shutil.copy2(os.path.join(htm_dir, f), os.path.join(export_dir, f))
                        self.log_to_ui(f"Copied HTM: {f}")

        # 3. Copy SET files
        if os.path.isdir(set_dir):
            for f in os.listdir(set_dir):
                if f.lower().endswith(".set"):
                    set_name_lower = os.path.splitext(f)[0].lower()
                    # Check if this set_name_lower is a substring of any selected CSV name
                    matched = False
                    for csv_name in selected_csv_names:
                        if set_name_lower in csv_name:
                            matched = True
                            break
                    if matched:
                        shutil.copy2(os.path.join(set_dir, f), os.path.join(export_dir, f))
                        self.log_to_ui(f"Copied SET: {f}")

        self.log_to_ui(f"All selected files copied to {export_dir}")



