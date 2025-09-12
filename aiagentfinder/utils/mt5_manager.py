import MetaTrader5 as mt5
# from aiagentfinder.utils import  Logger
# from PyQt5.QtWidgets import QMessageBox
import os
import subprocess
import time
import json
from datetime import datetime

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
            result = self.run_strategy(settings, data_path, mt5_path,report_path)

            print(f"Test '{settings['test_name']}' completed successfully.")
            # Logger.success(f"Test '{settings['test_name']}' completed successfully.")
            return result
        except Exception as e:
            print(f"Error running test '{settings['test_name']}': {e}")
            # Logger.error(f"Error running test '{settings['test_name']}': {e}")
            # QMessageBox.critical(self.ui, "Error", f"Test failed: {e}")
            return None

    def run_strategy(self, settings: dict, data_path: str, mt5_path: str, report_path:str):
        
        try:

            # --- Mapping dictionaries ---
            MODEL_MAP = {
                "Math calculation": 0,
                "1 minute OHLC": 1,
                "Open prices only": 2,
                "Every tick": None,
                "Every tick based on real ticks":4,
                
            }

            FORWARD_MAP = {
                "Disabled": 0,
                "1/2": 1,
                "1/3": 2,
                "1/4": 3,
                "Custom": 4
            }

            # OPTIMIZATION_MAP = {
            #     "Disabled": 0,
            #     "Fast genetic based algorithm": 1,
            #     "Slow complete algorithm": 2,
            #     "All symbols selected in MarketWatch": 3
            # }

            OPTIMIZATION_MAP = {
                "Disabled": 0,
                "Slow complete algorithm": 1,
                "Fast genetic based algorithm": 2,
                "All symbols selected in MarketWatch": 3
            }

            CRITERION_MAP = {
                "Balance Max": 0,
                "Profit Factor Max": 1,
                "Expected Payoff Max": 2,
                "Drawdown Max": 3,
                "Recovery Factor Max": 4,
                "Sharpe Ratio Max": 5,
                "Custom max": 6,
                "Complex Criterion max": 7
            }

            # --- Extract settings ---
            test_name     = settings.get("test_name", "StrategyTest")
            expert        = settings["expert"]
            param_file        = settings["param_file"]
            symbol        = settings["symbol"]
            timeframe     = settings.get("timeframe", "H1")

            from_date     = datetime.strptime(settings.get("date_from", "2023-01-01"), "%Y-%m-%d").strftime("%Y.%m.%d")
            to_date       = datetime.strptime(settings.get("date_to", "2023-12-31"), "%Y-%m-%d").strftime("%Y.%m.%d")
            forward_str   = settings.get("forward", "Disabled")
            forward       = FORWARD_MAP.get(forward_str, 0)

            forward_date  = settings.get("forward_date", None)
            if forward_date:
                forward_date = datetime.strptime(forward_date, "%Y-%m-%d").strftime("%Y.%m.%d")

            deposit       = settings.get("deposit", 10000)
            delay         = settings.get("delay", 0)
            model_str     = settings.get("model", "Every tick")
            currency      = settings.get("currency", "USD")
            leverage      = settings.get("leverage", "100.00")
            optim_str     = settings.get("optimization", "Disabled")
            criterion_str = settings.get("criterion", "Balance Max")

            execution_mode = 1 if int(delay) > 0 else 0

            # --- Map text -> numeric values ---
            model         = MODEL_MAP.get(model_str, 0)
            optimization  = OPTIMIZATION_MAP.get(optim_str, 0)
            criterion     = CRITERION_MAP.get(criterion_str, 0)

            # --- Timestamp for unique folder ---
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # --- Create folders ---
            folder = os.path.join(data_path, report_path, f"{test_name}_{timestamp}")
            os.makedirs(folder, exist_ok=True)

            config_dir = os.path.join(data_path, "config")
            os.makedirs(config_dir, exist_ok=True)

            config_path = os.path.join(config_dir, f"{test_name}.ini")
            report_file = os.path.join(folder, f"{test_name}_report.html")

            # --- Debug info ---
            print("----------------------------------------------------")
            print("Settings = ", settings)
            print(f"Config path  = {config_path}")
            print(f"Report file  = {report_file}")
            print(f"Expert       = {expert}")
            print(f"Symbol       = {symbol}")
            print(f"Timeframe    = {timeframe}")
            print(f"Model        = {model} ({model_str})")
            print(f"Optimization = {optimization} ({optim_str})")
            print(f"Criterion    = {criterion} ({criterion_str})")
            print(f"Forward      = {forward} ({forward_str})")
            if forward == 4 and forward_date:
                print(f"Forward Date = {forward_date}")
            print("----------------------------------------------------")

            # --- Write INI config file ---
            ini_content = f"""
            [Common]
            AutoConfiguration=1

            [Tester]
            Expert=Advisors\\{expert}
            Inputs={param_file}
            Symbol={symbol}
            Period={timeframe}
            FromDate={from_date}
            ToDate={to_date}
            Deposit={deposit}
            Currency={currency}
            Leverage={leverage}
            ExecutionMode={delay}
            Optimization={optimization}
            ForwardMode={forward}
            OptCriterion={criterion}
            StartTesting=1
            Report={report_file}
            ReportMode=4
            ReplaceReport=1
            """

            # Add ForwardDate only if Custom forward selected
            if forward == 4 and forward_date:
                ini_content += f"\nForwardDate={forward_date}\n"

            if model:
                ini_content += f"\nModel={model}\n"

            # Optional auto-shutdown after test
            # ini_content += "ShutdownTerminal=1\n"

            with open(config_path, "w") as f:
                f.write(ini_content.strip())
        
            # --- Run MT5 with config ---
            subprocess.Popen([mt5_path, f"/config:{config_path}"])

            # --- Wait for report (up to 30 seconds) ---
            timeout = 60
            start_time = time.time()
            while not os.path.exists(report_path) and (time.time() - start_time) < timeout:
                time.sleep(1)
             
            if os.path.exists(os.path.join(data_path, report_path)):
                print(f"✅ Test completed. Report saved at {report_path}")
                return {"status": "success", "report": report_path}
            else:
                print("❌ Report not found.")
                return {"status": "error", "message": "Report not generated"}

        except Exception as e:
            print("❌ Error running test:", str(e))
            return {"status": "error", "message": str(e)}
        
