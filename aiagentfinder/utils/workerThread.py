from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QProgressDialog
import traceback
import os

class Worker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)

    def __init__(self, func, *args, parent=None, **kwargs):
        super().__init__(parent)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._is_running = True

    @pyqtSlot()
    def run(self):
        try:
            res = self.func(*self.args, **self.kwargs)
            self.result.emit(res)
        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(tb)
        finally:
            self.finished.emit()

    def stop(self):
        self._is_running = False


class ThreadRunner:
    def __init__(self, parent=None):
        self.parent = parent
        self.thread = None
        self.worker = None
        self.dialog = None

    def run(self, func, *args, **kwargs):
        # Create QThread + Worker
        self.thread = QThread()
        self.worker = Worker(func, *args, **kwargs)
        self.worker.moveToThread(self.thread)

        # Progress Dialog
        self.dialog = QProgressDialog("Processing...", "Cancel", 0, 0, self.parent)
        self.dialog.setWindowTitle("Please Wait")
        self.dialog.setModal(True)
        self.dialog.canceled.connect(self.worker.stop)

        # Connections
        self.thread.started.connect(self.worker.run)
        self.worker.result.connect(self.on_result)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.cleanup)

        # Start
        self.thread.start()
        self.dialog.show()

    def on_result(self, result):
        print("Worker result:", result)

    def on_error(self, err):
        print("Worker error:", err)

    def cleanup(self):
        self.dialog.close()
        self.thread.quit()
        self.thread.wait()
        self.worker.deleteLater()
        self.thread.deleteLater()

