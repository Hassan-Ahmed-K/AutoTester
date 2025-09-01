import MetaTrader5 as mt5

class MT5Manager:
    def __init__(self, path=None):
        self.path = path
        self.connected = False

    def connect(self):
        """Connect to MT5 terminal"""
        if not mt5.initialize(path=self.path):
            return False, mt5.last_error()
        self.connected = True
        return True, mt5.account_info()

    def disconnect(self):
        """Disconnect MT5"""
        mt5.shutdown()
        self.connected = False
        return True
