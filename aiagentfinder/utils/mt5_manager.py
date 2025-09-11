import MetaTrader5 as mt5
# from aiagentfinder.utils import  Logger
# from PyQt5.QtWidgets import QMessageBox
import os
import subprocess
import time
import json

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

    def get_deposit(self):
        if not self.connected:
            raise RuntimeError("Not connected to MT5 terminal")
        
        account_info = self.mt5.account_info()
        if account_info is None:
            raise RuntimeError("Failed to retrieve account info")
        
        return {
            "balance": account_info.balance,
            "equity": account_info.equity,
            "margin": account_info.margin,
            "currency": account_info.currency,
            "leverage": account_info.leverage
        }
    
    def get_dataPath(self):
        if not self.connected:
            raise RuntimeError("Not connected to MT5 terminal")
        dataPath=self.mt5.terminal_info().data_path
        return dataPath


    
    def get_fx_symbols(self):
        return [s.name for s in mt5.symbols_get() if any(cur in s.name for cur in ["USD","EUR","GBP","JPY","AUD","NZD","CAD","CHF"])]

    def get_metals_symbols(self):
        return [s.name for s in mt5.symbols_get() if "XAU" in s.name or "XAG" in s.name]

    def get_indices_symbols(self):
        indices_keywords = ["US500", "NAS100", "DJ30", "DE30", "UK100"]
        return [s.name for s in mt5.symbols_get() if any(idx in s.name for idx in indices_keywords)]
    
    def run_test(self, settings: dict, data_path:str, mt5_path:str, report_path:str):
        try:
            # Logger.info(f"Running test: {settings['test_name']} on {settings['symbol']}")
            print(f"Running test: {settings['test_name']} on {settings['symbol']}")
            # Your actual test execution logic here
            result = self.run_strategy(settings, data_path, mt5_path)

            print(f"Test '{settings['test_name']}' completed successfully.")
            # Logger.success(f"Test '{settings['test_name']}' completed successfully.")
            return result
        except Exception as e:
            print(f"Error running test '{settings['test_name']}': {e}")
            # Logger.error(f"Error running test '{settings['test_name']}': {e}")
            # QMessageBox.critical(self.ui, "Error", f"Test failed: {e}")
            return None

    def run_strategy(self, settings: dict, data_path: str, mt5_path: str):
        """
        Run a strategy backtest/forward test using MT5.
        
        settings dict must contain:
            test_name, expert, symbol, timeframe, from_date, to_date, forward_mode, deposit
        """
        try:
            # Extract settings
            test_name = settings.get("test_name", "StrategyTest")
            expert = settings["expert"]
            symbol = settings["symbol"]
            timeframe = settings.get("timeframe", "H1")
            from_date = settings.get("from_date", "2023.01.01")
            to_date = settings.get("to_date", "2023.12.31")
            forward_mode = settings.get("forward_mode", 0)
            deposit = settings.get("deposit", 10000)

            # --- Create folders ---
            folder = os.path.join(data_path, "Agent Finder Results")
            os.makedirs(folder, exist_ok=True)
            config_path = os.path.join(data_path, f"{test_name}.ini")
            report_path = os.path.join(folder, f"{test_name}_report.html")
            print("Report_Path =", report_path)

            # --- Get MT5 account info ---
            account_info = mt5.account_info()
            if account_info is None:
                print("❌ Not connected to MT5")
                return {"status": "error", "message": "Not connected to MT5"}
    # {account_info.login}
            # --- Write INI config file ---
            with open(config_path, "w") as f:
                f.write(f"""[Common]
    Login=HassanAhmedKhan23
    Server={account_info.server}
    Password=dfV25Cac
    AutoConfiguration=false

    [Tester]
    Expert={expert}
    Symbol={symbol}
    Period={timeframe}
    FromDate={from_date}
    ToDate={to_date}
    ForwardMode={forward_mode}
    Deposit={deposit}
    Report="{report_path}"
    """)

            # --- Run MT5 with config ---
            cmd = f'"{mt5_path}" /portable /config:"{config_path}"'
            elevated_cmd = f'runas /user:Administrator "{cmd}"'

            subprocess.run(elevated_cmd, shell=True)

            # --- Wait for report (up to 30 seconds) ---
            timeout = 60
            start_time = time.time()
            while not os.path.exists(report_path) and (time.time() - start_time) < timeout:
                time.sleep(1)
             
            if os.path.exists(report_path):
                print(f"✅ Test completed. Report saved at {report_path}")
                return {"status": "success", "report": report_path}
            else:
                print("❌ Report not found.")
                return {"status": "error", "message": "Report not generated"}

        except Exception as e:
            print("❌ Error running test:", str(e))
            return {"status": "error", "message": str(e)}
        
