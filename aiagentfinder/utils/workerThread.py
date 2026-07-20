from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QProgressDialog, QApplication, QProgressBar
import traceback
import os
import psutil

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

    def run(self, func, *args, show_dialog=True, **kwargs):
        # Create QThread + Worker
        self.thread = QThread()
        self.worker = Worker(func, *args, **kwargs)
        self.worker.moveToThread(self.thread)

        # Create progress dialog only if requested
        if show_dialog:
            self.dialog = QProgressDialog("Processing...", "Cancel", 0, 0, self.parent)
            self.dialog.setWindowTitle("Please Wait")
            self.dialog.setModal(True)
            self.dialog.setMinimumDuration(0)
            self.dialog.setRange(0, 0)

            progress_bar = self.dialog.findChild(QProgressBar)
            if progress_bar:
                progress_bar.setAlignment(Qt.AlignCenter)
                progress_bar.setStyleSheet("QProgressBar { min-height: 20px; }")

            QApplication.processEvents()
            self.dialog.canceled.connect(self.stop)
        else:
            self.dialog = None  # make it explicit

        # Connections
        self.thread.started.connect(self.worker.run)
        self.worker.result.connect(self.on_result)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.cleanup)

        # Start the thread
        self.thread.start()

        # Show dialog only if it exists
        if self.dialog:
            self.dialog.show()

    def on_result(self, result):
        print("Worker result:", result)

    def on_error(self, err):
        print("Worker error:", err)

    def stop(self):
        """Stop the thread and terminate any child processes immediately"""
        print("ThreadRunner stop called via cancel button...")
        if self.worker:
            self.worker.stop()
            
        try:
            current_process = psutil.Process()
            children = current_process.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                    print(f"Terminated child process: {child.pid}")
                except Exception as e:
                    print(f"Failed to terminate child process {child.pid}: {e}")
        except Exception as e:
            print(f"Error finding child processes to terminate: {e}")

        # Stop/terminate the QThread
        if self.thread and self.thread.isRunning():
            print("Quitting QThread...")
            self.thread.quit()
            if not self.thread.wait(1000):
                print("Thread did not stop in time, forcing QThread.terminate()...")
                self.thread.terminate()
                self.thread.wait()
                
        self.cleanup()

    def cleanup(self):
        if self.dialog:
            self.dialog.close()
        if self.thread:
            self.thread.quit()
            self.thread.wait()
        if self.worker:
            self.worker.deleteLater()
        if self.thread:
            self.thread.deleteLater()
        self.worker = None
        self.thread = None
