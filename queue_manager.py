import json
import os


class QueueManager:
    def __init__(self):
        # Queue is a list of dicts: {symbol, expert}
        self.tests = []

    # --- Core Queue Operations ---
    def add_test(self, symbol, expert):
        """Add a test configuration to the queue"""
        self.tests.append({"symbol": symbol, "expert": expert})

    def delete_test(self, index):
        """Delete test by index"""
        if 0 <= index < len(self.tests):
            self.tests.pop(index)

    def move_test(self, old_index, new_index):
        """Move test up/down in the queue"""
        if 0 <= old_index < len(self.tests) and 0 <= new_index < len(self.tests):
            item = self.tests.pop(old_index)
            self.tests.insert(new_index, item)

    def duplicate_test(self, index):
        """Duplicate an existing test"""
        if 0 <= index < len(self.tests):
            self.tests.insert(index + 1, self.tests[index].copy())

    # --- Persistence (Save / Load) ---
    def save_to_file(self, filepath="queue.json"):
        """Save queue to JSON file"""
        with open(filepath, "w") as f:
            json.dump(self.tests, f, indent=4)

    def load_from_file(self, filepath="queue.json"):
        """Load queue from JSON file"""
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                self.tests = json.load(f)
        return self.tests

    # --- Utility ---
    def clear(self):
        """Clear the queue"""
        self.tests = []

    def get_all(self):
        """Return full test list"""
        return self.tests
