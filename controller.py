from PyQt5.QtWidgets import QMessageBox, QFileDialog
from mt5_manager import MT5Manager
from queue_manager import QueueManager


class AutoBatchController:
    def __init__(self, ui):
        self.ui = ui
        self.mt5 = MT5Manager()
        self.queue = QueueManager()

        # --- Connect UI buttons ---
        # MT5
        if hasattr(self.ui, "connect_btn"):
            self.ui.connect_btn.clicked.connect(self.connect_mt5)
        if hasattr(self.ui, "disconnect_btn"):
            self.ui.disconnect_btn.clicked.connect(self.disconnect_mt5)
        if hasattr(self.ui, "start_btn"):
            self.ui.start_btn.clicked.connect(self.start_tests)

        # Queue
        self.ui.add_btn.clicked.connect(self.add_test)
        self.ui.del_btn.clicked.connect(self.delete_test)
        self.ui.move_up_btn.clicked.connect(lambda: self.move_item(-1))
        self.ui.move_down_btn.clicked.connect(lambda: self.move_item(1))

        # Browse fields
        self.ui.mt5_dir_btn.clicked.connect(
            lambda: self.browse_file(self.ui.mt5_dir_input, "Select MT5 Terminal", "Executable (*.exe)")
        )
        self.ui.data_btn.clicked.connect(lambda: self.browse_folder(self.ui.data_input))
        self.ui.report_btn.clicked.connect(lambda: self.browse_folder(self.ui.report_input))

    # =====================
    # --- MT5 Connection ---
    # =====================
    def connect_mt5(self):
        if self.mt5.connected:
            QMessageBox.information(self.ui, "Info", "Already connected to MT5.")
            return

        self.mt5.path = self.ui.mt5_dir_input.text().strip()
        if not self.mt5.path:
            QMessageBox.warning(self.ui, "Warning", "Please select MT5 terminal path first.")
            return

        success, info = self.mt5.connect()
        if not success:
            QMessageBox.critical(self.ui, "Error", f"Connection failed: {info}")
        else:
            QMessageBox.information(self.ui, "Success", f"Connected to MT5!\nAccount: {info.login}")

    def disconnect_mt5(self):
        if not self.mt5.connected:
            QMessageBox.information(self.ui, "Info", "Not connected to MT5.")
            return

        self.mt5.disconnect()
        QMessageBox.information(self.ui, "Disconnected", "MT5 connection closed.")

    # =====================
    # --- Queue Handling ---
    # =====================
    def add_test(self):
        symbol = self.ui.symbol_input.text().strip() if hasattr(self.ui, "symbol_input") else ""
        expert = self.ui.expert_input.text().strip() if hasattr(self.ui, "expert_input") else ""

        if not symbol or not expert:
            QMessageBox.warning(self.ui, "Warning", "Please enter both Symbol and Expert file.")
            return

        self.queue.add_test(symbol, expert)
        self.ui.queue_list.addItem(f"{symbol} - {expert}")

    def delete_test(self):
        index = self.ui.queue_list.currentRow()
        if index < 0:
            QMessageBox.warning(self.ui, "Warning", "Please select a test to delete.")
            return

        self.queue.delete_test(index)
        self.ui.queue_list.takeItem(index)

    def move_item(self, direction):
        row = self.ui.queue_list.currentRow()
        if row < 0:
            return

        item = self.ui.queue_list.takeItem(row)
        new_row = max(0, min(self.ui.queue_list.count(), row + direction))
        self.ui.queue_list.insertItem(new_row, item)
        self.ui.queue_list.setCurrentRow(new_row)

    # =====================
    # --- Browse Helpers ---
    # =====================
    def browse_file(self, target, title, file_filter):
        path, _ = QFileDialog.getOpenFileName(self.ui, title, "", file_filter)
        if path:
            target.setText(path)

    def browse_folder(self, target):
        path = QFileDialog.getExistingDirectory(self.ui, "Select Folder")
        if path:
            target.setText(path)

    # =====================
    # --- Start Tests ---
    # =====================
    def start_tests(self):
        if not self.mt5.connected:
            QMessageBox.warning(self.ui, "Warning", "Please connect to MT5 first.")
            return

        if self.ui.queue_list.count() == 0:
            QMessageBox.warning(self.ui, "Warning", "No tests in the queue.")
            return

        QMessageBox.information(self.ui, "Info", "Starting backtests... (logic to be added)")
