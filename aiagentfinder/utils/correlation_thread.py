from PyQt5.QtCore import QObject, pyqtSignal
import requests, pandas as pd
from io import StringIO

class CorrelationWorker(QObject):
    finished = pyqtSignal(object)   # emits DataFrame if success
    error = pyqtSignal(str)         # emits error message

    def __init__(self, market="forex", period=50, symbols=None, output_format="csv", endpoint="snapshot"):
        super().__init__()
        self.market = market
        self.period = period
        self.symbols = symbols or ["EURUSD", "EURGBP", "AUDNZD"]
        self.output_format = output_format
        self.endpoint = endpoint

    def run(self):
        try:
            symbol_str = "|".join(self.symbols)
            url = f"https://www.mataf.io/api/tools/{self.output_format}/correl/{self.endpoint}/{self.market}/{self.period}/correlation.{self.output_format}?symbol={symbol_str}"

            response = requests.get(url)
            if response.status_code == 200:
                lines = response.text.splitlines()
                csv_data = "\n".join(lines[3:])  # drop metadata
                df = pd.read_csv(StringIO(csv_data))
                self.finished.emit(df)
            else:
                self.error.emit(f"Error {response.status_code}: Unable to fetch data")
        except Exception as e:
            self.error.emit(str(e))
