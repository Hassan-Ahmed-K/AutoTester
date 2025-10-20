import MetaTrader5 as mt5
# from aiagentfinder.utils import  Logger
# from PyQt5.QtWidgets import QMessageBox
import os
import subprocess
import time
import json
from datetime import datetime
import re
from pathlib import Path

class MT5Manager:

    def __init__(self):
        self.connected = False
        self.mt5 = mt5
        self.symbol_list = []

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
    
    def save_symbols_to_json(file_name="symbols.json"):
        # fetch symbols
        symbols = mt5.symbols_get()
        if symbols is None:
            print(f"Failed to get symbols: {mt5.last_error()}")
            return False

        # convert to dict (symbol object → dict)
        symbols_list = [s._asdict() for s in symbols]

        # save to JSON
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(symbols_list, f, indent=4, ensure_ascii=False)

        print(f"✅ Saved {len(symbols_list)} symbols to {os.path.abspath(file_name)}")
        return True
    
    def load_symbols_from_json(file_name="symbols.json"):
        """Load saved MT5 symbols from JSON file"""
        if not os.path.exists(file_name):
            print(f"❌ File not found: {file_name}")
            return None

        try:
            with open(file_name, "r", encoding="utf-8") as f:
                symbols_list = json.load(f)
            print(f"✅ Loaded {len(symbols_list)} symbols from {os.path.abspath(file_name)}")
            return symbols_list
        except Exception as e:
            print(f"⚠️ Failed to load symbols: {e}")
            return None
    
    def get_symbol_list(self):
        try:
        # Get all symbols from broker once
                self.symbol_list = [s.name for s in mt5.symbols_get()]
        except Exception:
            self.symbol_list = []

        fx_symbols = self.get_fx_symbols()  # fixed list (28 pairs)
        metals = self.get_metals_symbols()  # filtered from broker list
        indices = self.get_indices_symbols()  # filtered from broker list

        return fx_symbols + metals + indices

    def get_fx_symbols(self):
        # return [s for s in self.symbol_list if any(cur in s for cur in ["USD","EUR","GBP","JPY","AUD","NZD","CAD","CHF"])]
        MAJOR_PAIRS = [
            "EURUSD", "GBPUSD", "NZDUSD", "AUDUSD",
            "USDJPY", "USDCHF", "USDCAD"
        ]

        MINOR_PAIRS = [
            "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURCAD", "EURNZD",
            "GBPJPY", "GBPCHF", "GBPAUD", "GBPCAD", "GBPNZD",
            "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD",
            "NZDJPY", "NZDCHF", "NZDCAD",
            "CADJPY", "CADCHF", "CHFJPY"
        ]

        return MAJOR_PAIRS + MINOR_PAIRS

    def get_metals_symbols(self):
        return [s for s in self.symbol_list if "XAU" in s or "XAG" in s]

    def get_indices_symbols(self):
        indices_keywords = ["US500", "NAS100", "DJ30", "DE30", "UK100"]
        return [s for s in self.symbol_list if any(idx in s for idx in indices_keywords)]
    
    def run_test(self, settings: dict, data_path:str, mt5_path:str, report_path:str, expert_path):
        try:
            # Logger.info(f"Running test: {settings['test_name']} on {settings['symbol']}")
            print(f"Running test: {settings['test_name']} on {settings['symbol']}")
            # Your actual test execution logic here
            result = self.run_strategy(settings, data_path, mt5_path,report_path, expert_path)

            print(f"Test '{settings['test_name']}' completed successfully.")
            # Logger.success(f"Test '{settings['test_name']}' completed successfully.")
            return result
        except Exception as e:
            print(f"Error running test '{settings['test_name']}': {e}")
            # Logger.error(f"Error running test '{settings['test_name']}': {e}")
            # QMessageBox.critical(self.ui, "Error", f"Test failed: {e}")
            return None

    def run_strategy(self, settings: dict, data_path: str, mt5_path: str, report_path:str, expert_path):
        
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
            logs_dir = Path(os.path.join(data_path, "logs"))
            os.makedirs(config_dir, exist_ok=True)

            config_path = os.path.join(config_dir, f"{test_name}.ini")
            report_path = os.path.join(report_path, f"{test_name}_{timestamp}", f"{symbol}_{test_name}_{forward_str}_report")



            # --- Debug info ---
            print("----------------------------------------------------")
            print("Settings = ", settings)
            print(f"Config path  = {config_path}")
            print(f"Report file  = {report_path}")
            print(f"Expert       = {expert}")
            print("Expert Path = ", Path(*Path(expert_path[expert]["path"]).parts[-2:]))
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
            Expert={Path(*Path(expert_path[expert]["path"]).parts[-2:])}
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
            Report={report_path}
            ReportMode=4
            ReplaceReport=1
            ShutdownTerminal=1
            """

            # 

            # Add ForwardDate only if Custom forward selected
            if forward == 4 and forward_date:
                ini_content += f"\nForwardDate={forward_date}\n"

            if model:
                ini_content += f"\nModel={model}\n"

            # Optional auto-shutdown after test
            # ini_content += "ShutdownTerminal=1\n"

            with open(config_path, "w") as f:
                f.write(ini_content.strip())
        
            # # --- Run MT5 with config ---
            # subprocess.Popen([mt5_path, f"/config:{config_path}"])

            # # --- Wait for report (up to 30 seconds) ---
            # timeout = 60
            # start_time = time.time()
            # while not os.path.exists(report_path) and (time.time() - start_time) < timeout:
            #     time.sleep(1)

            proc = subprocess.Popen([mt5_path, f"/config:{config_path}"])
            print(f"🚀 Backtest started. Tracking report: {report_path}")

            last_progress = 0
            last_log_size = 0

            while proc.poll() is None:  # ⬅️ no timeout
                # --- Check XML report progress
                if os.path.exists(report_path):
                    try:
                        with open(report_path, "r", encoding="utf-16") as f:
                            content = f.read()
                            match = re.search(r'progress="(\d+)"', content)
                            if match:
                                progress = int(match.group(1))
                                if progress != last_progress:
                                    print(f"📊 Progress: {progress}%")
                                    last_progress = progress
                    except Exception:
                        pass

                # --- Check MT5 logs for new lines
                if logs_dir.exists():
                    log_files = sorted(logs_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
                    if log_files:
                        latest_log = log_files[0]
                        try:
                            with open(latest_log, "r", encoding="utf-16") as f:
                                f.seek(last_log_size)
                                new_lines = f.readlines()
                                if new_lines:
                                    for line in new_lines:
                                        print(f"📝 Log: {line.strip()}")
                                last_log_size = f.tell()
                        except Exception:
                            pass

                time.sleep(2)
            if os.path.exists(os.path.join(data_path, report_path)):
                print(f"✅ Test completed. Report saved at {report_path}")
                return {"status": "success", "report": report_path}
            else:
                print("❌ Report not found.")
                return {"status": "error", "message": "Report not generated"}

        except Exception as e:
            print("❌ Error running test:", str(e))
            return {"status": "error", "message": str(e)}
        
