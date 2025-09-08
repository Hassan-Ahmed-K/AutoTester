
from PyQt5.QtCore import  pyqtSignal , QObject
import os, glob, subprocess
import time

class MT5Worker(QObject):
    finished = pyqtSignal(bool, str, str)  # success, msg, data_folder
    error = pyqtSignal(str)                # error signal
    log = pyqtSignal(str)                  # log messages

    def __init__(self, mt5, file_path):
        super().__init__()
        self.mt5 = mt5
        self.file_path = file_path

    def run(self):
        try:
            self.log.emit("Connecting MT5 terminal...")
           
            success = self.mt5.connect(self.file_path)
          
            if not success:
                self.finished.emit(False, "❌ Failed to connect MT5", "")
                return

            roaming = os.path.join(os.environ["APPDATA"], "MetaQuotes", "Terminal")
            candidates = glob.glob(os.path.join(roaming, "*"))

            data_folder = ""
            for folder in candidates:
                if os.path.isdir(os.path.join(folder, "config")):
                    data_folder = folder
                    break

            if data_folder:
                self.finished.emit(True, data_folder, "")  # emit only path
            else:
                self.finished.emit(True, "", "")

        except Exception as e:
        
            self.error.emit(f"Exception: logger.error(e)")
            self.finished.emit(False, f"❌ Exception: {e}", "")