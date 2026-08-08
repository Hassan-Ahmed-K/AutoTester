from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QProgressDialog, QProgressBar, QApplication
import traceback
import psutil

class WorkerV2(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)

    def __init__(self, func, *args, parent=None, **kwargs):
        super().__init__(parent)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._stop = False
        self._pause = False

    def stop(self):
        self._stop = True

    def pause(self):
        self._pause = True

    def resume(self):
        self._pause = False

    @pyqtSlot()
    def run(self):
        try:
            self.kwargs["worker"] = self
            result = self.func(*self.args, **self.kwargs)
            self.result.emit(result)
        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(tb)
        finally:
            self.finished.emit()


class ThreadRunnerV2:
    def __init__(self, parent=None):
        self.parent = parent
        self.thread = None
        self.worker = None
        self.dialog = None

    def run(self, func, *args, show_dialog=True, **kwargs):
        self.thread = QThread()
        self.worker = WorkerV2(func, *args, **kwargs)
        self.worker.moveToThread(self.thread)

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
            self.dialog = None

        self.thread.started.connect(self.worker.run)
        self.worker.result.connect(self.on_result)
        self.worker.error.connect(self.on_error)
        self.worker.finished.connect(self.cleanup)

        self.thread.start()
        if self.dialog:
            self.dialog.show()

    def on_result(self, result):
        print("WorkerV2 result:", result)

    def on_error(self, err):
        print("WorkerV2 error:", err)

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

    def stop(self, immediate_stop=True, pid=None):
        """Stop the thread and terminate any child processes immediately"""
        print("ThreadRunnerV2 stop called. immediate_stop:", immediate_stop, "pid:", pid)
        if self.worker:
            self.worker.stop()
            
        # Terminate child processes immediately if immediate_stop is True
        if immediate_stop:
            try:
                current_process = psutil.Process()
                children = current_process.children(recursive=True)
                for child in children:
                    if pid is None or child.pid == pid or child.parent().pid == pid:
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

    def pause(self):
        if self.worker:
            self.worker.pause()

    def resume(self):
        if self.worker:
            self.worker.resume()
