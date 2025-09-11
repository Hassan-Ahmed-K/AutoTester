from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QProgressDialog ,QApplication
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





# class ThreadRunner:
#     """
#     Run any function in a QThread with a progress dialog,
#     with optional success/error/warning callbacks.
#     """
#     def __init__(self, parent=None):
#         self.parent = parent
#         self.thread = None
#         self.worker = None
#         self.progress = None

#     def run(self, fn, on_finished=None, on_error=None, on_warning=None, *args, **kwargs):
#         """Run fn(*args, **kwargs) in a thread with a progress dialog."""

#         # Create progress dialog
#         self.progress = QProgressDialog("Processing...", "Cancel", 0, 0, self.parent)
#         self.progress.setWindowTitle("Please Wait")
#         self.progress.setModal(True)
#         self.progress.setMinimumDuration(0)
#         self.progress.show()

#         # Thread + Worker
#         self.thread = QThread()
#         self.worker = Worker(fn, *args, **kwargs)
#         self.worker.moveToThread(self.thread)

#         # Connect base signals
#         self.thread.started.connect(self.worker.run)
#         self.worker.finished.connect(self.thread.quit)
#         self.worker.error.connect(self.thread.quit)
#         self.worker.warning.connect(self.thread.quit)
#         self.worker.finished.connect(self.worker.deleteLater)
#         self.worker.error.connect(self.worker.deleteLater)
#         self.worker.warning.connect(self.worker.deleteLater)
#         self.thread.finished.connect(self.thread.deleteLater)

#         # Cancel button
#         self.progress.canceled.connect(self.thread.terminate)

#         # Connect optional callbacks
#         if on_finished:
#             self.worker.finished.connect(lambda result: self._wrap_callback(on_finished, result))
#         if on_error:
#             self.worker.error.connect(lambda msg: self._wrap_callback(on_error, msg))
#         if on_warning:
#             self.worker.warning.connect(lambda msg: self._wrap_callback(on_warning, msg))

#         # Start
#         self.thread.start()

#     def _wrap_callback(self, callback, *args):
#         """Close progress dialog safely and call user callback."""
#         if self.progress:
#             self.progress.close()
#         callback(*args)

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
        self.dialog.setMinimumDuration(0)
        
        self.dialog.setRange(0, 0)  # moving bar
         
        QApplication.processEvents()
        
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

