import MetaTrader5 as mt5

class MT5Manager:

    def __init__(self):
        self.connected = False
        self.mt5 = mt5

    def connect(self, path):
        if mt5.initialize(path):
            self.connected = True
            return True
        else:
            self.connected = False
            return False

    def disconnect(self):
        mt5.shutdown()
        self.connected = False

 