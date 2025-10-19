import json
import os
from PyQt5.QtWidgets import QInputDialog, QFileDialog, QMessageBox
import matplotlib.pyplot as plt
from aiagentfinder.utils import Logger
import csv

class QueueManager:
    def __init__(self, ui):
        self.ui = ui
        self.tests = []  # list of dicts: {symbol, expert, test_name, ...}


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


    def add_test_to_queue(self, test: dict):
        self.tests.append(test)
        self.refresh_queue()

    def delete_test(self, index: int):
        if 0 <= index < len(self.tests):
            del self.tests[index]
            self.refresh_queue()


    def move_up(self, index: int):
        if index > 0:
            self.tests[index - 1], self.tests[index] = self.tests[index], self.tests[index - 1]
            self.refresh_queue()
            self.ui.queue_list.setCurrentRow(index - 1)

    def move_down(self, index: int):

        if index < len(self.tests) - 1:
            self.tests[index + 1], self.tests[index] = self.tests[index], self.tests[index + 1]
            self.refresh_queue()
            self.ui.queue_list.setCurrentRow(index + 1)

    # def duplicate_test(self, index: int):

    #     if 0 <= index < len(self.tests):
    #         self.tests.insert(index + 1, dict(self.tests[index]))
    #         self.refresh_queue()
    #         self.ui.queue_list.setCurrentRow(index + 1)

    def duplicate_test(self, index: int):
        if 0 <= index < len(self.tests):
            new_test = dict(self.tests[index])  # copy original test

            # Add "dup_" to the name (if it has one)
            if "test_name" in new_test:
                new_test["test_name"] = f"dup_{new_test['test_name']}"

            self.tests.insert(index + 1, new_test)
            self.refresh_queue()
            self.ui.queue_list.setCurrentRow(index + 1)

    def update_all_tests(self, updates: dict):
        if not self.tests:
            return

        for i, test in enumerate(self.tests):
            for key, value in updates.items():
                if key in test:
                    self.tests[i][key] = value
        self.refresh_queue()


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
                self.tests =self.tests + json.load(f)
            self.refresh_queue()

    def export_template(self):
        Logger.info("📤 Export template initiated.")
        path, _ = QFileDialog.getSaveFileName(self.ui, "Export Template", "", "CSV Files (*.csv)")
        Logger.debug(f"Save dialog returned path: {path}")

        if path:
            try:
                if not self.tests:
                    Logger.warning("⚠️ The tests list is empty. Nothing to export.")
                    QMessageBox.warning(self.ui, "Error", "The tests list is empty. Nothing to export.")
                    raise ValueError("The tests list is empty. Nothing to export.")


                # Ensure consistent column order from the first test
                header_keys = list(self.tests[0].keys())
                Logger.debug(f"Using header keys: {header_keys}")

                Logger.info(f"Writing {len(self.tests)} tests to {path}")

                with open(path, "w", encoding="utf-8") as f:
            
                    header = ",".join(header_keys)
                    f.write(header + "\n")
                    Logger.debug(f"Header written: {header}")

                    # Write each row by following header key order
                    for idx, test in enumerate(self.tests, start=1):
                        row = ",".join(str(test.get(key, "")) for key in header_keys)
                        f.write(row + "\n")
                        Logger.debug(f"Row {idx} written: {row}")

                Logger.success(f"✅ Export completed successfully! File saved at {path}")

            except ValueError as ve:
                Logger.error(f"❌ Export aborted: {ve}")

            except Exception as e:
                Logger.error(f"❌ Unexpected error exporting template: {e}")
        else:
            Logger.info("Export template cancelled by user.")
    # ---------------- Extra Features ----------------
    def create_non_correlated_list(self):
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

    def get_element_index(self, test_name: str):
        for i, test in enumerate(self.tests):
            if test.get("test_name") == test_name:
                return i
        return -1  # not found

    # ---------------- Queue-Like Behavior ----------------
    def get_next_test(self):
        if self.tests:
            return self.tests.pop(0)
        return None

    def is_empty(self):
        return len(self.tests) == 0

    def clear(self):
        self.tests.clear()

    def __len__(self):
        return len(self.tests)
    


