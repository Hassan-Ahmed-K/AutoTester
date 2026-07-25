import os
import shutil
import pandas as pd
import traceback
from aiagentfinder.utils.ThreadRunnerV2 import ThreadRunnerV2
from aiagentfinder.utils import Logger 
from PyQt5.QtWidgets import QLineEdit, QFileDialog,QListWidget,QTableWidget, QTableWidgetItem, QHeaderView,QLabel,QToolTip,QMessageBox,QInputDialog, QDialog, QVBoxLayout, QTextBrowser, QPushButton, QFrame
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cm as cm
from PyQt5.QtCore import Qt, QPoint, QRect, QTimer, QObject
from PyQt5.QtGui import QCursor
import numpy as np


class ScrollableToolTip(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.resize(580, 320)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #444444;
            }
            QTextBrowser {
                background-color: #1e1e1e;
                color: #cccccc;
                border: none;
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
            }
            QScrollBar:vertical {
                border: none;
                background: #1e1e1e;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #444444;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555555;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.browser = QTextBrowser(self)
        layout.addWidget(self.browser)
        
        # Prevent the tooltip window from taking window focus or stealing keyboard focus
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)


class DetailDialog(QDialog):
    def __init__(self, title, html_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(650, 550)
        
        # Style sheet to match the app dark mode and make it look clean
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #cccccc;
            }
            QTextBrowser {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3a3a3a;
                font-family: Consolas, "Courier New", monospace;
                font-size: 13px;
                padding: 10px;
            }
            QPushButton {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #444444;
                padding: 6px 14px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3b3b3b;
                border-color: #555555;
            }
            QPushButton:pressed {
                background-color: #1b1b1b;
            }
            QScrollBar:vertical {
                border: none;
                background: #1e1e1e;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #444444;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #555555;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
        """)
        
        layout = QVBoxLayout(self)
        self.browser = QTextBrowser(self)
        self.browser.setHtml(html_content)
        layout.addWidget(self.browser)
        
        close_btn = QPushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class SetCompareController(QObject):
    def __init__(self, ui):
        super().__init__()
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
        
        # Connect portfolio_stats cell clicked to show detailed breakdown dialog
        self.ui.portfolio_stats.cellClicked.connect(self.on_portfolio_cell_clicked)
        
        # Setup scrollable hover tooltip
        from PyQt5.QtCore import QEvent
        self.scroll_tip = ScrollableToolTip(self.main_window)
        self.tip_timer = QTimer(self.main_window)
        self.tip_timer.setInterval(200)
        self.tip_timer.timeout.connect(self.check_tip_hover)
        self.ui.portfolio_stats.viewport().installEventFilter(self)
        self.ui.portfolio_stats.setMouseTracking(True)
        self.ui.portfolio_stats.viewport().setMouseTracking(True)



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

    def on_portfolio_cell_clicked(self, row, col):
        item = self.ui.portfolio_stats.item(row, col)
        if not item:
            return
        html_content = item.data(Qt.UserRole)
        if not html_content:
            return
        
        # Get column header text for the dialog title
        header_item = self.ui.portfolio_stats.horizontalHeaderItem(col)
        title = f"Monthly Breakdown - {header_item.text()}" if header_item else "Monthly Breakdown"
        
        dialog = DetailDialog(title, html_content, self.main_window)
        dialog.exec_()

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if obj == self.ui.portfolio_stats.viewport():
            if event.type() == QEvent.MouseMove:
                pos = event.pos()
                item = self.ui.portfolio_stats.itemAt(pos)
                if item:
                    html_content = item.data(Qt.UserRole)
                    if html_content:
                        self.scroll_tip.browser.setHtml(html_content)
                        # Position popup near cursor but not if cursor is already inside the tooltip
                        cursor_pos = QCursor.pos()
                        if not self.scroll_tip.geometry().contains(cursor_pos):
                            global_pos = self.ui.portfolio_stats.viewport().mapToGlobal(pos)
                            self.scroll_tip.move(global_pos + QPoint(15, 15))
                        if not self.scroll_tip.isVisible():
                            self.scroll_tip.show()
                            self.tip_timer.start()
                        return False
        return super().eventFilter(obj, event)

    def check_tip_hover(self):
        if not self.scroll_tip.isVisible():
            self.tip_timer.stop()
            return
            
        cursor_pos = QCursor.pos()
        
        # Check if cursor is over the table viewport
        viewport = self.ui.portfolio_stats.viewport()
        vp_rect = viewport.rect()
        vp_global_topleft = viewport.mapToGlobal(vp_rect.topLeft())
        vp_global_rect = QRect(vp_global_topleft, vp_rect.size())
        
        # Check if cursor is over the tooltip window
        tip_rect = self.scroll_tip.rect()
        tip_global_topleft = self.scroll_tip.mapToGlobal(tip_rect.topLeft())
        tip_global_rect = QRect(tip_global_topleft, tip_rect.size())
        
        if not (vp_global_rect.contains(cursor_pos) or tip_global_rect.contains(cursor_pos)):
            self.scroll_tip.hide()
            self.tip_timer.stop()

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

                    # Keep the last entry for duplicate timestamps to resolve InvalidIndexError during concat
                    df = df.groupby("DATE", as_index=False).last()

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

            # Build tooltip per file as a beautiful HTML table
            html_lines = [
                "<table style='width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 12px; color: #cccccc;'>",
                "  <thead>",
                "    <tr style='border-bottom: 2px solid #444444; text-align: left;'>",
                "      <th style='padding: 6px; color: #ffffff;'>Strategy / File</th>",
                "      <th style='padding: 6px; text-align: right; color: #ffffff;'>Start</th>",
                "      <th style='padding: 6px; text-align: right; color: #ffffff;'>End</th>",
                "      <th style='padding: 6px; text-align: right; color: #ffffff;'>PnL</th>",
                "    </tr>",
                "  </thead>",
                "  <tbody>"
            ]

            for idx, col in enumerate(balance_cols):
                pnl = strategy_profits[col][period]
                start, end = strategy_start_end[col][period]
                color = "#22c55e" if pnl >= 0 else "#ef4444"
                pnl_str = f"+{round(pnl, 2)}" if pnl >= 0 else f"{round(pnl, 2)}"
                bg_color = "#252525" if idx % 2 == 0 else "#1e1e1e"
                file_name = col.replace("BALANCE_", "")

                html_lines.append(
                    f"    <tr style='background-color: {bg_color}; border-bottom: 1px solid #2d2d2d;'>"
                    f"      <td style='padding: 6px; font-weight: bold;'>{file_name}</td>"
                    f"      <td style='padding: 6px; text-align: right;'>{round(start, 2)}</td>"
                    f"      <td style='padding: 6px; text-align: right;'>{round(end, 2)}</td>"
                    f"      <td style='padding: 6px; text-align: right; color: {color}; font-weight: bold;'>{pnl_str}</td>"
                    f"    </tr>"
                )

            html_lines.append("  </tbody>")
            html_lines.append("</table>")

            item.setData(Qt.UserRole, "\n".join(html_lines))
            table.setItem(0, col_idx, item)

        # Total column (sum of all monthly profits)
        total_profit = sum(portfolio_profits.values())
        total_item = QTableWidgetItem(str(round(total_profit, 2)))
        total_item.setTextAlignment(Qt.AlignCenter)

        # Build tooltip for the Total column showing total breakdown per strategy
        total_html_lines = [
            "<table style='width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 12px; color: #cccccc;'>",
            "  <thead>",
            "    <tr style='border-bottom: 2px solid #444444; text-align: left;'>",
            "      <th style='padding: 6px; color: #ffffff;'>Strategy / File</th>",
            "      <th style='padding: 6px; text-align: right; color: #ffffff;'>Initial</th>",
            "      <th style='padding: 6px; text-align: right; color: #ffffff;'>Final</th>",
            "      <th style='padding: 6px; text-align: right; color: #ffffff;'>Total PnL</th>",
            "    </tr>",
            "  </thead>",
            "  <tbody>"
        ]

        for idx, col in enumerate(balance_cols):
            start = strategy_start_end[col][periods[0]][0]
            end = strategy_start_end[col][periods[-1]][1]
            pnl = end - start
            color = "#22c55e" if pnl >= 0 else "#ef4444"
            pnl_str = f"+{round(pnl, 2)}" if pnl >= 0 else f"{round(pnl, 2)}"
            bg_color = "#252525" if idx % 2 == 0 else "#1e1e1e"
            file_name = col.replace("BALANCE_", "")

            total_html_lines.append(
                f"    <tr style='background-color: {bg_color}; border-bottom: 1px solid #2d2d2d;'>"
                f"      <td style='padding: 6px; font-weight: bold;'>{file_name}</td>"
                f"      <td style='padding: 6px; text-align: right;'>{round(start, 2)}</td>"
                f"      <td style='padding: 6px; text-align: right;'>{round(end, 2)}</td>"
                f"      <td style='padding: 6px; text-align: right; color: {color}; font-weight: bold;'>{pnl_str}</td>"
                f"    </tr>"
            )

        total_html_lines.append("  </tbody>")
        total_html_lines.append("</table>")

        total_item.setData(Qt.UserRole, "\n".join(total_html_lines))
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
            dd_item.setTextAlignment(Qt.AlignCenter)
            self.ui.drawdown_analysis.setItem(row, 1, dd_item)

            # Number of active drawdowns (numeric sort)
            active_val = int(df["ACTIVE_COUNT"].iloc[row])
            active_item = QTableWidgetItem()
            active_item.setData(Qt.EditRole, active_val)
            active_item.setTextAlignment(Qt.AlignCenter)
            self.ui.drawdown_analysis.setItem(row, 2, active_item)

            # Loss values for each file (numeric sort)
            col_index = 3
            for loss_col in loss_cols:
                val = df[loss_col].iloc[row]
                val_item = QTableWidgetItem()
                val_item.setData(Qt.EditRole, float(round(val, 2)))
                val_item.setTextAlignment(Qt.AlignCenter)
                self.ui.drawdown_analysis.setItem(row, col_index, val_item)
                col_index += 1

        # Enable interactive sorting (Excel-like)
        self.ui.drawdown_analysis.setSortingEnabled(True)
        
        # Sort by Date & Time (column 0) ascending by default
        self.ui.drawdown_analysis.sortByColumn(0, Qt.AscendingOrder)

        # Ensure columns are interactive and resize to contents for readability
        header = self.ui.drawdown_analysis.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.ui.drawdown_analysis.resizeColumnsToContents()
        self.ui.drawdown_analysis.resizeRowsToContents()

        # Set specific initial widths for the first three columns
        self.ui.drawdown_analysis.setColumnWidth(0, 160)  # Date & Time
        self.ui.drawdown_analysis.setColumnWidth(1, 100)  # DD Total
        self.ui.drawdown_analysis.setColumnWidth(2, 50)   # #

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

        # --- Prepare colors and line styling ---
        total_lines = len(equity_cols) + len(balance_cols)
        color_map = plt.get_cmap("tab20")
        colors = [color_map(i % 20) for i in range(total_lines)]

        # Use thin semi-transparent lines if there are many files to avoid clutter
        use_clutter_mode = len(equity_cols) > 8 or len(balance_cols) > 8
        default_alpha = 0.22 if use_clutter_mode else 0.85
        default_lw = 1.0 if use_clutter_mode else 1.5

        from matplotlib.gridspec import GridSpec
        from matplotlib.lines import Line2D

        # Set style for a more premium dark look
        plt.style.use('dark_background')

        # --- Layout: [Equity Panel | Chart | Balance Panel] ---
        # Panels are shown only if they have data
        has_equity = len(equity_cols) > 0
        has_balance = len(balance_cols) > 0

        if has_equity and has_balance:
            width_ratios = [1.0, 2.4, 1.0]
            fig = plt.figure(figsize=(22, 9), facecolor='#121212')
            gs = GridSpec(1, 3, figure=fig, width_ratios=width_ratios, wspace=0.03)
            ax_leq = fig.add_subplot(gs[0, 0])   # left: equity legend
            ax     = fig.add_subplot(gs[0, 1])   # center: chart
            ax_lbal = fig.add_subplot(gs[0, 2])  # right: balance legend
            ax_leq.set_facecolor('#0d0d0d')
            ax_leq.set_axis_off()
            ax_lbal.set_facecolor('#0d0d0d')
            ax_lbal.set_axis_off()
        elif has_equity:
            width_ratios = [2.6, 1.0]
            fig = plt.figure(figsize=(19, 9), facecolor='#121212')
            gs = GridSpec(1, 2, figure=fig, width_ratios=width_ratios, wspace=0.03)
            ax     = fig.add_subplot(gs[0, 0])
            ax_leq = fig.add_subplot(gs[0, 1])
            ax_leq.set_facecolor('#0d0d0d')
            ax_leq.set_axis_off()
            ax_lbal = None
        else:  # balance only
            width_ratios = [2.6, 1.0]
            fig = plt.figure(figsize=(19, 9), facecolor='#121212')
            gs = GridSpec(1, 2, figure=fig, width_ratios=width_ratios, wspace=0.0)
            ax     = fig.add_subplot(gs[0, 0])
            ax_lbal = fig.add_subplot(gs[0, 1])
            ax_lbal.set_facecolor('#0d0d0d')
            ax_lbal.set_axis_off()
            ax_leq = None

        ax.set_facecolor('#121212')

        # Plot Individual Equity Curves
        equity_handles = []
        for col, color in zip(equity_cols, colors[:len(equity_cols)]):
            line, = ax.plot(df["DATE"], df[col], label=col.replace("EQUITY_", ""), color=color, linewidth=default_lw, alpha=default_alpha)
            equity_handles.append(line)

        # Plot Individual Balance Curves
        balance_handles = []
        for col, color in zip(balance_cols, colors[len(equity_cols):]):
            line, = ax.plot(df["DATE"], df[col], label=col.replace("BALANCE_", ""), color=color, linewidth=default_lw, alpha=default_alpha, linestyle='--')
            balance_handles.append(line)

        # avg lines intentionally not plotted
        avg_handles = {}

        # Title and labels
        ax.set_title({
            "Equity": "Equity Curve Comparison",
            "Balance": "Balance Curve Comparison",
            "Both": "Equity & Balance Comparison"
        }[choice], color='white', fontsize=14, pad=16)
        ax.set_xlabel("Date / Time", color='#bbbbbb')
        ax.set_ylabel("Value", color='#bbbbbb')
        ax.grid(True, alpha=0.15, color='gray', linestyle=':')
        ax.tick_params(colors='#888888', labelsize=9)
        # Give the curves breathing room so they don't stick to the edges
        ax.margins(x=0.02, y=0.06)
        for spine in ax.spines.values():
            spine.set_edgecolor('#333333')

        def _build_legend(panel_ax, handles_list, labels_list, title, avg_handle=None, avg_label=None, is_dashed=False):
            """Render a legend into a blank axes panel with 2 columns."""
            if panel_ax is None:
                return
            # Avg entry first
            all_h = []
            all_l = []
            if avg_handle is not None:
                avg_color = "#00f2fe" if not is_dashed else "#ff8c00"
                all_h.append(Line2D([0], [0], color=avg_color, lw=3.0,
                                    linestyle='--' if is_dashed else '-', solid_capstyle='round'))
                all_l.append(avg_label)
            for h, l in zip(handles_list, labels_list):
                max_chars = 25
                display_l = l[:max_chars] + "…" if len(l) > max_chars else l
                all_h.append(Line2D([0], [0], color=h.get_color(), lw=2.0,
                                    linestyle='--' if is_dashed else '-', solid_capstyle='round'))
                all_l.append(display_l)

            # Use 2 columns so long lists fit; switch at 15 entries
            ncols = 2 if len(all_l) > 20 else 1
            leg = panel_ax.legend(
                all_h, all_l,
                title=title,
                loc="upper left",
                bbox_to_anchor=(0.01, 0.99),
                fontsize=7,
                title_fontsize=9,
                frameon=False,
                labelcolor='#cccccc',
                borderpad=0.3,
                labelspacing=0.5,
                handlelength=2.5,
                handletextpad=0.5,
                ncol=ncols,
                columnspacing=0.8,
            )
            leg.get_title().set_color('#00f2fe' if not is_dashed else '#ff8c00')
            leg.get_title().set_fontweight('bold')

        # --- Render Equity Legend (left panel) ---
        eq_labels = [c.replace("EQUITY_", "") for c in equity_cols]
        _build_legend(
            ax_leq if has_equity and has_balance else (ax_leq if has_equity else None),
            equity_handles, eq_labels,
            title="— Equity",
            is_dashed=False,
        )

        # --- Render Balance Legend (right panel) ---
        bal_labels = [c.replace("BALANCE_", "") for c in balance_cols]
        _build_legend(
            ax_lbal if has_balance else None,
            balance_handles, bal_labels,
            title="-- Balance",
            is_dashed=True,
        )

        # --- Interactive Hover Detection ---
        # Map handles to column names and set picker radius for easier selection
        handle_to_col = {}
        for col, line in zip(equity_cols, equity_handles):
            handle_to_col[line] = col
            line.set_picker(10)
        for col, line in zip(balance_cols, balance_handles):
            handle_to_col[line] = col
            line.set_picker(10)

        # ── Performance: downsample display df to max 800 pts ─────────────────
        MAX_DISPLAY_PTS = 800
        if len(df) > MAX_DISPLAY_PTS:
            step = max(1, len(df) // MAX_DISPLAY_PTS)
            df_plot = df.iloc[::step].reset_index(drop=True)
        else:
            df_plot = df

        # Re-plot using downsampled data (replace lines already drawn)
        for line, col in zip(equity_handles, equity_cols):
            line.set_xdata(df_plot["DATE"])
            line.set_ydata(df_plot[col])
        for line, col in zip(balance_handles, balance_cols):
            line.set_xdata(df_plot["DATE"])
            line.set_ydata(df_plot[col])

        # Pre-compute x numeric array and per-line y arrays for fast lookup
        x_num   = mdates.date2num(df_plot["DATE"].tolist())
        x_num   = np.array(x_num)
        line_y  = {}   # line -> np.array of y values
        for line, col in zip(equity_handles, equity_cols):
            line_y[line] = df_plot[col].to_numpy(dtype=float)
        for line, col in zip(balance_handles, balance_cols):
            line_y[line] = df_plot[col].to_numpy(dtype=float)

        all_lines = equity_handles + balance_handles

        # ── Animated artists (blit-compatible) ────────────────────────────────
        v_line = ax.axvline(x=df_plot["DATE"].iloc[0], color='cyan',
                            linestyle='--', alpha=0.35, linewidth=1.0,
                            visible=False, animated=True)

        annot = ax.annotate("", xy=(0, 0), xytext=(12, 12),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round,pad=0.4", fc="#1a1a1a",
                                      ec="#555555", alpha=0.92),
                            color="white", fontsize=7.5, fontfamily='monospace',
                            animated=True)
        annot.set_visible(False)

        info_text = fig.text(0.5, 0.03,
                             "Hover over any curve to display details here",
                             color="#aaaaaa", fontsize=8.5,
                             fontfamily="sans-serif",
                             ha="center", va="center",
                             bbox=dict(boxstyle="round,pad=0.5", fc="#161616",
                                       ec="#333333", alpha=0.95),
                             animated=True)

        # ── Blit background ───────────────────────────────────────────────────
        # We capture the background AFTER the first draw so blitting is clean.
        _bg = [None]   # mutable container so inner functions can write it

        def _save_bg(event=None):
            _bg[0] = fig.canvas.copy_from_bbox(fig.bbox)

        fig.canvas.mpl_connect("draw_event", _save_bg)

        # ── Hover state ───────────────────────────────────────────────────────
        _last = {"idx": -1, "hovered": set()}   # throttle guard

        # Pixel-height tolerance for y-proximity detection
        Y_TOL_PX = 8

        def _px_per_data(ax_ref):
            """Return (scale_x, scale_y): data units per pixel."""
            bbox = ax_ref.get_window_extent()
            xlim = ax_ref.get_xlim()
            ylim = ax_ref.get_ylim()
            sx = (xlim[1] - xlim[0]) / max(bbox.width,  1)
            sy = (ylim[1] - ylim[0]) / max(bbox.height, 1)
            return sx, sy

        def hover(event):
            if event.inaxes is not ax or event.xdata is None:
                # Mouse left axes — reset if needed
                if _last["hovered"]:
                    _last["hovered"] = set()
                    _last["idx"] = -1
                    for ln in all_lines:
                        ln.set_alpha(default_alpha)
                        ln.set_linewidth(default_lw)
                    v_line.set_visible(False)
                    annot.set_visible(False)
                    info_text.set_text("Hover over any curve to display details here")
                    info_text.set_color("#aaaaaa")
                    if _bg[0]:
                        fig.canvas.restore_region(_bg[0])
                        ax.draw_artist(v_line)
                        ax.draw_artist(annot)
                        fig.draw_artist(info_text)
                        fig.canvas.blit(fig.bbox)
                return

            # ── Accurate detection: line.contains() — pixel-perfect ────────────
            # This checks the actual rendered path (including between-point segments).
            # It is fast enough because blitting handles all redraw costs.
            hovered_set = set()
            for ln in all_lines:
                try:
                    cont, _ = ln.contains(event)
                    if cont:
                        hovered_set.add(ln)
                except Exception:
                    pass

            # ── Find nearest x index for value lookup ──────────────────────────
            idx = int(np.searchsorted(x_num, event.xdata))
            idx = min(idx, len(x_num) - 1)
            if idx > 0 and abs(event.xdata - x_num[idx-1]) < abs(event.xdata - x_num[idx]):
                idx -= 1

            # Throttle: skip redraw if nothing changed
            if hovered_set == _last["hovered"] and idx == _last["idx"]:
                return
            _last["idx"] = idx
            _last["hovered"] = hovered_set

            target_date = df_plot["DATE"].iloc[idx]

            # ── Update line styles ─────────────────────────────────────────
            if hovered_set:
                for ln in all_lines:
                    if ln in hovered_set:
                        ln.set_alpha(1.0)
                        ln.set_linewidth(2.2)
                    else:
                        ln.set_alpha(0.06 if use_clutter_mode else 0.12)
                        ln.set_linewidth(0.7)

                # Floating tooltip
                tip_lines = []
                for ln in hovered_set:
                    col_name = handle_to_col[ln]
                    val = line_y[ln][idx]
                    nm  = col_name.replace("EQUITY_","").replace("BALANCE_","")[:20]
                    tip_lines.append(f"{nm}: {val:,.2f}")
                annot.set_text("\n".join(tip_lines))
                first_ln = next(iter(hovered_set))
                annot.xy = (target_date, line_y[first_ln][idx])
                annot.set_visible(True)

                # Bottom bar
                date_str = target_date.strftime('%Y-%m-%d %H:%M')
                parts = [f"📅 {date_str}"]
                for ln in hovered_set:
                    col_name = handle_to_col[ln]
                    val = line_y[ln][idx]
                    nm  = col_name.replace("EQUITY_","").replace("BALANCE_","")
                    kind = "EQ" if "EQUITY" in col_name else "BAL"
                    parts.append(f"[{kind}] {nm}: {val:,.2f}")
                info_text.set_text("   |   ".join(parts))
                info_text.set_color("white")

                v_line.set_xdata([target_date, target_date])
                v_line.set_visible(True)
            else:
                for ln in all_lines:
                    ln.set_alpha(default_alpha)
                    ln.set_linewidth(default_lw)
                v_line.set_visible(False)
                annot.set_visible(False)
                info_text.set_text("Hover over any curve to display details here")
                info_text.set_color("#aaaaaa")

            # ── Blit: only repaint changed pixels ─────────────────────────
            if _bg[0]:
                fig.canvas.restore_region(_bg[0])
                for ln in all_lines:
                    ax.draw_artist(ln)
                ax.draw_artist(v_line)
                ax.draw_artist(annot)
                fig.draw_artist(info_text)
                fig.canvas.blit(fig.bbox)
            else:
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)

        fig.subplots_adjust(left=0.02, right=0.99, top=0.95, bottom=0.10)

        # Maximize window on open
        try:
            manager = plt.get_current_fig_manager()
            manager.window.showMaximized()
        except Exception:
            pass

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



