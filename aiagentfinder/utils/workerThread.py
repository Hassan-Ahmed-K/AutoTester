from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QProgressDialog, QMessageBox
from aiagentfinder.utils import Logger

class Worker(QObject):
    finished = pyqtSignal(object)   # emits result when done
    error = pyqtSignal(str)         # emits error message if failed
    warning = pyqtSignal(str)       # emits warning message if needed

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Warning as w:   # catch warnings separately
            self.warning.emit(str(w))
        except Exception as e:
            self.error.emit(str(e))




class ThreadRunner:
    """
    Run any function in a QThread with a progress dialog.
    """
    def __init__(self, parent=None):
        self.parent = parent
  

    def run(self, fn, *args, **kwargs):
        """Run fn(*args, **kwargs) in a thread with a ProcessDialog."""
        
        # Create progress dialog
        self.progress = QProgressDialog("Processing...", "Cancel", 0, 0, self.parent)
        self.progress.setWindowTitle("Please Wait")
        self.progress.setModal(True)
        self.progress.setMinimumDuration(0)
        self.progress.show()

        # Thread + Worker
        self.thread = QThread()
        self.worker = Worker(fn, *args, **kwargs)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.warning.connect(self._on_warning)
        self.worker.finished.connect(self.thread.quit)
        self.worker.error.connect(self.thread.quit)
        self.worker.warning.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.worker.warning.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Cancel button
        self.progress.canceled.connect(self.thread.terminate)

        # Start
        self.thread.start()

    def _on_finished(self, result):
        self.progress.close()
        print("✅ Task finished. Result:", result)
        Logger.success(f"Task finished. Result: {result}")

    def _on_error(self, message):
        self.progress.close()
        Logger.error(message, Exception(message))
        QMessageBox.critical(self.parent, "Error", message)

    def _on_warning(self, message):
        self.progress.close()
        Logger.warning(message)
       
        QMessageBox.warning(self.parent, "Warning", message)
