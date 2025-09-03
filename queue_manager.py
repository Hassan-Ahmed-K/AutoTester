import json
import os
from PyQt5.QtWidgets import QInputDialog, QFileDialog, QMessageBox
import matplotlib.pyplot as plt


class QueueManager:
    def __init__(self, ui):
        self.ui = ui
        # Queue is a list of dicts: {symbol, expert}
        self.tests = []

    # ---------------- Core Operations ----------------
    def refresh_queue(self):
        self.ui.queue_list.clear()
        print("Refreshing queue with:", len(self.tests), "items")
        for test in self.tests:
            test_name = test.get("test_name", "")

            display_text = f"{test_name}"
            print("Adding item:", display_text)
            self.ui.queue_list.addItem(display_text)
        print("Queue list count after refresh:", self.ui.queue_list.count())

    def add_test_to_queue(self,tests):
            print("Before append:", self.tests)
            self.tests.append(tests)
            print("After append:", self.tests)
            self.refresh_queue()

    def delete_test(self, index):
        if 0 <= index < len(self.tests):
            del self.tests[index]
            self.refresh_queue()

    def move_up(self, index):
        if index > 0:
            self.tests[index - 1], self.tests[index] = self.tests[index], self.tests[index - 1]
            self.refresh_queue()
            self.ui.queue_list.setCurrentRow(index - 1)

    def move_down(self, index):
        if index < len(self.tests) - 1:
            self.tests[index + 1], self.tests[index] = self.tests[index], self.tests[index + 1]
            self.refresh_queue()
            self.ui.queue_list.setCurrentRow(index + 1)

    def duplicate_test(self, index):
        if 0 <= index < len(self.tests):
            self.tests.insert(index + 1, dict(self.tests[index]))
            self.refresh_queue()
            self.ui.queue_list.setCurrentRow(index + 1)

    # ---------------- File Operations ----------------
    def save_queue(self):
        path, _ = QFileDialog.getSaveFileName(self.ui, "Save Queue", "", "JSON Files (*.json)")
        if path:
            with open(path, "w") as f:
                json.dump(self.tests, f, indent=4)

    def load_queue(self):
        path, _ = QFileDialog.getOpenFileName(self.ui, "Load Queue", "", "JSON Files (*.json)")
        if path and os.path.exists(path):
            with open(path, "r") as f:
                self.tests = json.load(f)
            self.refresh_queue()

    def export_template(self):
        path, _ = QFileDialog.getSaveFileName(self.ui, "Export Template", "", "CSV Files (*.csv)")
        if path:
            with open(path, "w") as f:
                f.write("Symbol,Expert\n")
                for test in self.tests:
                    f.write(f"{test['symbol']},{test['expert']}\n")

    # ---------------- Extra Features ----------------
    def create_non_correlated_list(self):
        # Placeholder (real logic can use correlation stats)
        result = {t["symbol"]: t for t in self.tests}.values()  # deduplicate by symbol
        QMessageBox.information(self.ui, "Non-Correlated List", f"Generated {len(result)} items.")

    def show_correlation_matrix(self):
        n = len(self.tests)
        corr = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
        QMessageBox.information(self.ui, "Correlation Matrix", str(corr))

        if n > 0:
            plt.imshow(corr, cmap='hot', interpolation='nearest')
            plt.title("Correlation Matrix")
            plt.colorbar()
            plt.show()
