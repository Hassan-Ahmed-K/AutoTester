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
from .logger import Logger
from pathlib import Path


class MT5Manager:

    def __init__(self):
        self.connected = False
        self.mt5 = mt5
        self.symbol_list = []
        self.pid = None

    def connect(self, path):
        if mt5.initialize(path):
            self.connected = True

            info = mt5.terminal_info()
            self.mt5_path = path
            self.data_path = info.data_path
            self.logs_dir = Path(os.path.join(self.data_path, "logs"))

            Logger.info(f"MT5 Data Path: {self.data_path}")
            Logger.info(f"Log Directory: {self.logs_dir}")

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
        """Fetch MT5 symbols and save them to a JSON file"""
        try:
            # fetch symbols
            symbols = mt5.symbols_get()
            if symbols is None:
                Logger.error(f"❌ Failed to get symbols: {mt5.last_error()}")
                return False

            # convert to dict (symbol object → dict)
            symbols_list = [s._asdict() for s in symbols]

            # save to JSON
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(symbols_list, f, indent=4, ensure_ascii=False)

            Logger.success(f"✅ Saved {len(symbols_list)} symbols to {os.path.abspath(file_name)}")
            return True

        except Exception as e:
            Logger.error(f"⚠️ Error saving symbols to {file_name}: {e}")
            return False
   
    def load_symbols_from_json(file_name="symbols.json"):
        """Load saved MT5 symbols from JSON file"""
        if not os.path.exists(file_name):
            Logger.error(f"❌ File not found: {file_name}")
            return None

        try:
            with open(file_name, "r", encoding="utf-8") as f:
                symbols_list = json.load(f)

            Logger.success(f"✅ Loaded {len(symbols_list)} symbols from {os.path.abspath(file_name)}")
            return symbols_list

        except Exception as e:
            Logger.error(f"⚠️ Failed to load symbols from {file_name}: {e}")
            return None
   
    def get_symbol_list(self):
        try:
        # Get all symbols from broker once
            self.symbol_list = [s.name for s in mt5.symbols_get()]
            fx_symbols = self.get_fx_symbols()  # fixed list (28 pairs)
            metals = self.get_metals_symbols()  
            indices = self.get_indices_symbols()  
            self.symbol_list = fx_symbols + metals + indices
        except Exception:
            self.symbol_list = []
        
        return self.symbol_list
        
    def get_fx_symbols(self):
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
    
    def run_test(self, settings: dict, data_path: str, mt5_path: str, report_path: str, expert_path, report_type="HTML"):
        try:
            Logger.info(f"▶️ Running test: {settings.get('test_name', 'Unnamed')} on {settings.get('symbol', 'Unknown')}")
            
            result = self.run_strategy(settings, data_path, mt5_path, report_path, expert_path, report_type)

            Logger.success(f"✅ Test '{settings.get('test_name', 'Unnamed')}' completed successfully.")
            return result

        except Exception as e:
            Logger.error(f"❌ Error running test '{settings.get('test_name', 'Unnamed')}': {e}")
            return None

    def run_strategy(self, settings: dict, data_path: str, mt5_path: str, report_path: str, expert_path, report_type="XML", setProcessor=False, save_csv=False, save_graph=False):
        proc = None
        try:
            success_flag = False
            Logger.info("Starting run_strategy...")
            Logger.info("settings: " + str(settings))

            # --- Mapping dictionaries ---
            MODEL_MAP = {
                "Every tick": 0,
                "1 minute OHLC": 1,
                "Open prices only": 2,
                "Math calculation": 3,
                "Every tick based on real ticks": 4,
            }

            FORWARD_MAP = {
                "Disabled": 0,
                "1/2": 1,
                "1/3": 2,
                "1/4": 3,
                "Custom": 4
            }

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

            REPORT_MODE_MAP = {
                "HTML": 0,
                "GRAPH": 0,
                "OVERVIEW": 1,
                "CSV": 4,
                "XML": 4
            }

            ext_map = {
                "HTML": ".htm",
                "GRAPH": ".htm",
                "CSV": ".csv",
                "XML": ".xml",
                "OVERVIEW": ".htm"
            }

            # --- Extract settings ---
            test_name = settings.get("test_name", "StrategyTest")
            expert = settings["expert"]
            param_file = settings["param_file"]
            symbol = settings["symbol"]

            # Sanitize for file paths (replace invalid characters with underscores)
            safe_test_name = re.sub(r'[<>:"/\\|?*]', '_', test_name)
            safe_symbol = re.sub(r'[<>:"/\\|?*]', '_', symbol)
            timeframe = settings.get("timeframe", "H1")

            from_date = datetime.strptime(settings.get("date_from", "2023-01-01"), "%Y-%m-%d").strftime("%Y.%m.%d")
            to_date = datetime.strptime(settings.get("date_to", "2023-12-31"), "%Y-%m-%d").strftime("%Y.%m.%d")

            forward_str = settings.get("forward", "Disabled")
            forward = FORWARD_MAP.get(forward_str, 0)

            forward_date = settings.get("forward_date", None)
            if forward_date:
                forward_date = datetime.strptime(forward_date, "%Y-%m-%d").strftime("%Y.%m.%d")

            deposit = settings.get("deposit", 10000)
            delay = settings.get("delay", 0)
            model_str = settings.get("model", "Every tick")
            currency = settings.get("currency", "USD")
            leverage = settings.get("leverage", "100.00")
            optim_str = settings.get("optimization", settings.get("optimazation", "Disabled"))
            criterion_str = settings.get("criterion", "Balance Max")

            model = MODEL_MAP.get(model_str, 0)
            optimization = OPTIMIZATION_MAP.get(optim_str, 0)
            criterion = CRITERION_MAP.get(criterion_str, 0)
            report_mode = REPORT_MODE_MAP.get(report_type.upper(), 0)

            # --- Timestamp folder ---
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # --- Handle normal vs setProcessor mode ---
            if not setProcessor:
                # 1. Create a unique relative folder path
                relative_folder = os.path.join(report_path, f"{safe_test_name}_{timestamp}")
                
                # 2. Create the absolute folder for Python to use
                absolute_folder = os.path.join(data_path, relative_folder)
                os.makedirs(absolute_folder, exist_ok=True)

                # 3. Prepare the filename
                safe_forward_str = forward_str.replace("/", "_").replace("\\", "_")
                report_file_name = f"{safe_symbol}_{safe_test_name}_{safe_forward_str}_report_{timestamp}"
                
                # 4. report_path MUST be relative for the MT5 .ini to work reliably
                report_path = os.path.join(relative_folder, report_file_name)
                
                # 5. Final absolute path for Python tracking
                final_abs_report_path = os.path.join(data_path, report_path)
            else:
                ext = ext_map.get(report_type.upper(), ".html")
                report_file = f"{safe_symbol}_{param_file.replace('.set', '')}"
                # In setProcessor mode, keep it simple
                report_path = os.path.join(report_path, report_file)
                final_abs_report_path = os.path.join(data_path, report_path)

            print("report_path = ", final_abs_report_path)

            check_dir = final_abs_report_path
            
            parent_dir = os.path.dirname(check_dir)

            folder_name = os.path.basename(check_dir)

            if os.path.exists(parent_dir):
                for file in os.listdir(parent_dir):
                    file_path = os.path.join(parent_dir, file)

                    if os.path.isfile(file_path) and file.startswith(folder_name):
                        try:
                            os.remove(file_path)
                            Logger.info(f"Deleted: {file}")
                        except Exception as e:
                            Logger.warning(f"Could not delete {file}: {e}")


            # --- Prepare folders ---
            config_dir = os.path.join(data_path, "config")
            logs_dir = Path(os.path.join(data_path, "logs"))
            os.makedirs(config_dir, exist_ok=True)

            config_path = os.path.join(config_dir, f"{safe_test_name}_{report_type}.ini")

            # --- Debug info ---
            Logger.debug(f"Settings: {settings}")
            Logger.debug(f"Config path  = {config_path}")
            Logger.debug(f"Report path  = {report_path}")
            # Logger.debug(f"Report File  = {report_file}")
            Logger.debug(f"Report Mode  = {report_mode}")
            Logger.debug(f"Param Files  = {param_file}")
            Logger.debug(f"Expert       = {expert}")
            Logger.debug(f"Expert Path  = {Path(*Path(expert_path[expert]['path']).parts[-2:])}")
            Logger.debug(f"Symbol       = {safe_symbol}")
            Logger.debug(f"Timeframe    = {timeframe}")
            Logger.debug(f"Model        = {model} ({model_str})")
            Logger.debug(f"Optimization = {optimization} ({optim_str})")
            Logger.debug(f"Criterion    = {criterion} ({criterion_str})")
            Logger.debug(f"Forward      = {forward} ({forward_str})")
            if forward == 4 and forward_date:
                Logger.debug(f"Forward Date = {forward_date}")

            # --- Build INI file ---
            ini_lines = [
                "[Common]",
                "AutoConfiguration=1",
                "",
                "[Tester]",
                f"Expert={Path(*Path(expert_path[expert]['path']).parts[-2:])}",
                f"Symbol={safe_symbol}",
                f"Period={timeframe}",
                f"Optimization={optimization}",
                f"OptimizationCriterion={criterion}",
                f"Inputs={param_file}",
                f"FromDate={from_date}",
                f"ToDate={to_date}",
                "VisualMode=0",
                f"Deposit={deposit}",
                f"Currency={currency}",
                f"Leverage={leverage}",
                f"ExecutionMode={delay}",
                f"ForwardMode={forward}",
                "StartTesting=1",
                "TesterChartDump=0",
                f"Report={report_path}",
                f"ReportMode={report_mode}",
                "ReplaceReport=1"
            ]

            need_gui = save_csv or save_graph

            if need_gui:
                # Keep the terminal open so GUI automation can run to export CSV/PNG
                ini_lines.append("ShutdownTerminal=0")
            else:
                # Shut down the terminal automatically when test completes
                ini_lines.append("ShutdownTerminal=1")

            if forward == 4 and forward_date:
                ini_lines.append(f"ForwardDate={forward_date}")

            if model is not None:
                ini_lines.append(f"Model={model}")

            ini_content = "\n".join(ini_lines)

            with open(config_path, "w") as f:
                f.write(ini_content)

            Logger.info(f"INI config file written: {config_path}")

            proc = subprocess.Popen([mt5_path, f"/config:{config_path}"])
            self.pid = proc.pid

            Logger.success(f"🚀 Backtest started. Tracking report: {report_path}")


            latest_log = None
            current_log_pointer = 0

            # Pick newest log file
            if logs_dir.exists():
                log_files = sorted(logs_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
                if log_files:
                    latest_log = log_files[0]
                    current_log_pointer = latest_log.stat().st_size  # Skip old content
                    Logger.debug(f"Using log file: {latest_log}")
                    Logger.debug(f"Initial log pointer: {current_log_pointer}")

            ext = ext_map.get(report_type.upper(), ".htm")
            file_to_check = Path(os.path.join(data_path, report_path) + ext)
            last_size = -1
            stable_time = 0
            stable_seconds = 2
            success_flag = False

            while proc.poll() is None:
                # 1. Check if the report file exists and is stable
                if file_to_check.exists():
                    size = file_to_check.stat().st_size
                    Logger.info(f"Report file size: {size}")
                    if size == last_size:
                        stable_time += 1
                        if stable_time >= stable_seconds:
                            success_flag = True
                            Logger.info("✅ Success: Report file has stabilized.")
                            break
                    else:
                        stable_time = 0
                        last_size = size

                # 2. Check the logs for completion message
                if latest_log and latest_log.exists():
                    try:
                        with open(latest_log, "r", encoding="utf-16") as f:
                            f.seek(current_log_pointer)
                            new_lines = f.readlines()

                            if new_lines:
                                for line in new_lines:
                                    Logger.info(line)
                                    line_lower = line.lower()
                                    if "successfully finished" in line_lower or 'result "successfully finished"' in line_lower:
                                        success_flag = True
                                        Logger.info("✅ Success flag set to True based on log line")
                                        break

                            current_log_pointer = f.tell()
                    except Exception as e:
                        Logger.warning(f"Error reading MT5 log: {e}")

                if success_flag:
                    break

                time.sleep(1)


            if need_gui:
                Logger.info("---------------------------  SAVE EXPORT -----------------------------------------------")
                csv_path = os.path.join(data_path, report_path) + ".csv" if save_csv else None
                png_path = os.path.join(data_path, report_path) + "_graph.png" if save_graph else None
                Logger.info(f"Exporting graph... CSV Path: {csv_path}, PNG Path: {png_path}")
                Logger.info(f"mt5_path = {mt5_path}")
                Logger.info(f"report_path = {os.path.join(data_path, report_path)}")
                
                self.export_graph_to_csv(
                    mt5_path,
                    csv_path,
                    png_output_dir=png_path
                )

                if proc and proc.poll() is None:
                    proc.terminate()
                Logger.info("----------------------------------------------------------------------------------------")



            os.remove(config_path)
            
            # --- After process exits ---
            folder_path = os.path.dirname(os.path.join(data_path, report_path))
            Logger.info(f"folder_path = {folder_path}")

            if (os.path.exists(folder_path) and os.listdir(folder_path)) or success_flag:
                Logger.success(f"✅ Test completed. Report saved at {report_path}")
                return {"status": "success", "report": report_path}
            else:
                Logger.error("❌ Report not found.")
                return {"status": "error", "message": "Report not generated"}

        except Exception as e:
            if proc is not None and proc.poll() is None:
                proc.terminate()
            Logger.error(f"❌ Error running test: {str(e)}")
            return {"status": "error", "message": str(e)}


    def focus_mt5(self,mt5_exe_path):
        from pywinauto.application import Application
        from pywinauto import Desktop
        app = Application(backend="uia").connect(path=mt5_exe_path)
        pid = app.process

        desktop = Desktop(backend="uia")

        for w in desktop.windows():
            if w.process_id() == pid:
                title = w.window_text().lower()
                Logger.info("title = " + title)
                w.restore()
                w.set_focus()
                Logger.info(f"✅ Focused MT5: {w.window_text()}")
                return w, app

        return None, app

    # ──────────────────────────────────────────────────────────────────────
    # Graph export helpers
    # ──────────────────────────────────────────────────────────────────────

    _GRAPH_IMAGES        = ["graph_btn.png", "graph_wt_btn.png", "graph.png"]
    _GRAPH_TAB_RETRIES   = 3
    _GRAPH_CONFIDENCE    = 0.85
    _RIGHT_CLICK_OFFSET  = 100   # px above tab centre to right-click into the chart
    _PAUSE_SETTLE        = 2.5   # seconds to wait after a Save-As dialog closes

    # Tab labels MT5 uses (checked case-insensitively)
    _GRAPH_TAB_LABELS    = ["graph", "chart"]
    # UIA control types that can host the tab button
    _GRAPH_CTRL_TYPES    = ["TabItem", "Button", "RadioButton", "Custom"]

    def _click_graph_tab_uia(self, mt5_window):
        """
        PRIMARY strategy — walk the UIA accessibility tree of the MT5 main
        window and click the first control whose text matches a known Graph
        tab label.  No image files, no screen-capture, fully DPI-safe.

        Parameters
        ----------
        mt5_window : pywinauto wrapper returned by focus_mt5()

        Returns
        -------
        (cx, cy) : tuple[int, int]  – screen centre of the clicked control.

        Raises
        ------
        RuntimeError  – when no matching control is found.
        """
        if mt5_window is None:
            raise RuntimeError("MT5 window wrapper is None — cannot walk UIA tree.")

        Logger.info("🔍 Searching UIA tree for Graph tab…")

        # Collect candidates from every interesting control type
        candidates = []
        for ctrl_type in self._GRAPH_CTRL_TYPES:
            try:
                found = mt5_window.descendants(control_type=ctrl_type)
                candidates.extend(found)
            except Exception:
                pass

        Logger.info(f"   UIA candidates scanned: {len(candidates)}")

        for ctrl in candidates:
            try:
                text = ctrl.window_text().strip()
            except Exception:
                continue
            if text.lower() in self._GRAPH_TAB_LABELS:
                try:
                    rect = ctrl.rectangle()
                    cx   = (rect.left + rect.right)  // 2
                    cy   = (rect.top  + rect.bottom) // 2
                    Logger.info(f"✅ UIA found '{text}' control at ({cx}, {cy}) — clicking…")
                    ctrl.click_input()
                    time.sleep(0.5)
                    Logger.info(f"✅ Clicked Graph tab via UIA at ({cx}, {cy})")
                    return cx, cy
                except Exception as click_err:
                    Logger.warning(f"⚠️ UIA click failed for '{text}': {click_err} — trying next candidate…")

        raise RuntimeError(
            "❌ UIA: no control with text in "
            f"{self._GRAPH_TAB_LABELS} found among {len(candidates)} candidates."
        )

    def _locate_graph_tab_image(self):
        """
        FALLBACK strategy — classic pyautogui image scan.
        Returns a pyautogui Box, or raises RuntimeError if not found.
        """
        import pyautogui

        data_dir = os.path.join(os.getcwd(), "data")
        for attempt in range(1, self._GRAPH_TAB_RETRIES + 1):
            if attempt > 1:
                Logger.warning(f"Retry {attempt}/{self._GRAPH_TAB_RETRIES} — waiting for screen to repaint…")
                time.sleep(self._PAUSE_SETTLE)

            for name in self._GRAPH_IMAGES:
                img = os.path.join(data_dir, name)
                if not os.path.isfile(img):
                    Logger.warning(f"⚠️ Image missing on disk — skipping: {name}")
                    continue
                Logger.info(f"🔍 Image fallback trying: {name}")
                try:
                    location = pyautogui.locateOnScreen(img, confidence=self._GRAPH_CONFIDENCE)
                except Exception as exc:
                    Logger.warning(f"⚠️ Screen scan error ({name}): {exc}")
                    continue
                if location:
                    Logger.info(f"✅ Found Graph tab using image: {name}")
                    return location
                Logger.info(f"❌ Not matched: {name}")

        raise RuntimeError(
            f"❌ Graph tab image not found after {self._GRAPH_TAB_RETRIES} attempt(s). "
            "Check screenshot scaling and that the Strategy Tester panel is visible."
        )

    def _click_graph_tab(self, mt5_window=None):
        """
        Click the Graph tab and return its screen centre (cx, cy).

        Strategy
        --------
        1. UIA tree walk (no images, DPI-safe) — preferred.
        2. pyautogui image scan                — fallback if UIA fails.

        Parameters
        ----------
        mt5_window : pywinauto wrapper (optional but strongly recommended).
        """
        import pyautogui

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE    = 0.3

        # ── Strategy 1: UIA ──────────────────────────────────────────────────
        try:
            cx, cy = self._click_graph_tab_uia(mt5_window)
            return cx, cy
        except RuntimeError as uia_err:
            Logger.warning(f"⚠️ UIA strategy failed: {uia_err}")
            Logger.warning("   Falling back to image-based detection…")

        # ── Strategy 2: image scan ───────────────────────────────────────────
        box = self._locate_graph_tab_image()
        cx  = box.left + box.width  // 2
        cy  = box.top  + box.height // 2
        pyautogui.click(cx, cy)
        time.sleep(0.5)
        Logger.info(f"✅ Clicked Graph tab via image at ({cx}, {cy})")
        return cx, cy

    def _open_context_menu(self, cx, cy, app):
        """
        Right-click at (cx, cy - _RIGHT_CLICK_OFFSET) to open the chart
        context menu and return the menu wrapper.
        """
        import pyautogui
        from pywinauto import Desktop

        right_click_y = cy - self._RIGHT_CLICK_OFFSET
        pyautogui.rightClick(cx, right_click_y)
        time.sleep(0.5)
        Logger.info(f"✅ Right-clicked chart at ({cx}, {right_click_y})")

        # Wait up to 2 s for the menu window to appear
        desktop = Desktop(backend="uia")
        for _ in range(10):
            try:
                if any(
                    w.element_info.control_type == "Menu"
                    for w in desktop.windows()
                ):
                    Logger.info("✅ Context menu detected.")
                    break
            except Exception:
                pass
            time.sleep(0.2)

        try:
            menu = app.window(control_type="Menu")
            if not menu.exists():
                menu = app.top_window()
        except Exception:
            menu = app.top_window()

        return menu

    def _click_menu_item(self, menu, label):
        """
        Find the first MenuItem whose text contains *label* and invoke it.

        Returns
        -------
        bool – True if the item was found and invoked.
        """
        try:
            items = menu.descendants(control_type="MenuItem")
            Logger.info(f"Menu items ({len(items)}):")
            for item in items:
                text = item.window_text()
                Logger.info(f"  • {text}")
                if label in text:
                    Logger.info(f"  → Found '{label}' — invoking…")
                    try:
                        item.invoke()
                        Logger.info(f"  → Invoked via UIA.")
                    except Exception as inv_err:
                        Logger.warning(f"  → invoke() failed ({inv_err}) — trying click_input()…")
                        item.click_input()
                        Logger.info(f"  → Clicked via click_input().")
                    return True
            Logger.error(f"❌ '{label}' not found in context menu.")
            return False
        except Exception as exc:
            Logger.error(f"❌ Error enumerating menu: {exc}")
            return False

    def _save_file_dialog(self, output_path):
        """
        Type *output_path* into the active Save-As dialog and confirm.
        Then presses Escape and waits _PAUSE_SETTLE so the screen fully
        repaints before the next UI action.
        """
        import pyautogui
        from pywinauto import Desktop

        time.sleep(0.8)   # let the dialog paint
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.2)
        pyautogui.write(output_path, interval=0.02)
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(1.0)

        # Handle "Overwrite?" confirmation
        try:
            desktop = Desktop(backend="uia")
            confirm = desktop.window(title_re=".*(Confirm|Replace|Overwrite).*")
            if confirm.exists(timeout=2):
                Logger.warning("⚠️ Overwrite dialog detected — clicking Yes.")
                confirm.child_window(title="Yes", control_type="Button").click_input()
        except Exception:
            pass

        Logger.info(f"✅ Saved → {output_path}")
        pyautogui.press("escape")   # dismiss any residual dialog state
        time.sleep(self._PAUSE_SETTLE)

    def export_graph_to_csv(self, mt5_exe_path, output_dir, png_output_dir=None):
        """
        Switch to the Graph tab and export the chart data.

        The context menu contains both 'Export to CSV' and 'Export to PNG'
        in the same popup, so when *png_output_dir* is provided the PNG is
        exported in the same workflow — no second image search needed.

        Parameters
        ----------
        mt5_exe_path  : str  – Path to terminal64.exe.
        output_dir    : str  – Full path for the output CSV file.
        png_output_dir: str  – (optional) Full path for the output PNG file.
        """
        import pyautogui

        # ── Focus MT5 ───────────────────────────────────────────────
        mt5_window, app = self.focus_mt5(mt5_exe_path)
        time.sleep(0.5)

        # ── Click Graph tab ONCE ──────────────────────────────────────
        cx, cy = self._click_graph_tab(mt5_window)

        # ── CSV: first right-click ─────────────────────────────────────
        if output_dir:
            Logger.info("📤 Exporting CSV…")
            menu = self._open_context_menu(cx, cy, app)
            found = self._click_menu_item(menu, "Export to CSV")
            if not found:
                Logger.error("❌ 'Export to CSV' not found in menu — skipping CSV.")
            else:
                self._save_file_dialog(output_dir)
                Logger.info("✅ CSV exported successfully!")

        # ── PNG: second right-click at the SAME (cx, cy) ──────────────
        if png_output_dir:
            Logger.info("📤 Exporting PNG…")
            menu = self._open_context_menu(cx, cy, app)   # same coords, no re-search
            found = self._click_menu_item(menu, "Export to PNG")
            if not found:
                Logger.warning("⚠️ 'Export to PNG' not found — trying 'Save as Picture'…")
                found = self._click_menu_item(menu, "Save as Picture")
            if not found:
                Logger.error("❌ PNG export menu item not found — skipping PNG.")
            else:
                self._save_file_dialog(png_output_dir)
                Logger.info("✅ PNG exported successfully!")

    def export_graph_to_png(self, mt5_exe_path, output_dir):
        """
        Convenience wrapper — exports only the PNG screenshot of the Graph tab.
        Internally calls export_graph_to_csv with csv disabled and png enabled.

        .. note::
            Prefer calling export_graph_to_csv(csv_path, png_output_dir=png_path)
            directly so both formats are exported in a single workflow.
        """
        import pyautogui

        mt5_window, app = self.focus_mt5(mt5_exe_path)
        time.sleep(0.5)

        cx, cy = self._click_graph_tab(mt5_window)

        menu = self._open_context_menu(cx, cy, app)
        found = self._click_menu_item(menu, "Export to PNG")
        if not found:
            Logger.warning("⚠️ 'Export to PNG' not found — trying 'Save as Picture'…")
            found = self._click_menu_item(menu, "Save as Picture")
        if not found:
            Logger.error("❌ PNG export menu item not found.")
        else:
            self._save_file_dialog(output_dir)
            Logger.info("✅ PNG exported successfully!")

    def export_graph_to_csv_v2(self,mt5_exe_path, output_dir):
        Logger.info("Attempting to connect via UIA...")
        import time
        import os
        from pywinauto.application import Application
        from pywinauto import mouse, keyboard
        from pywinauto import Desktop

        try:

            app = Application(backend="uia").connect(path=mt5_exe_path)
            win = app.window(title_re=f".*MetaQuotes.*")
            win.set_focus()
            Logger.info(f"Connected to: {win.window_text()}")

            time.sleep(1)

            # Optional safety
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.3

            # 3️⃣ Find Graph button via image
            graph_tab = pyautogui.locateOnScreen(os.path.join(os.getcwd(), "data", "graph_btn.png"), confidence=0.8)
            
            if graph_tab.exists():
                Logger.info("✅ Found 'Graph' tab!")
                graph_tab.click_input()
                Logger.info("✅ Clicked 'Graph' tab.")
                
                rect = graph_tab.rectangle()
                Logger.info(f"Tab coordinates: {rect}")
                
                click_x = rect.mid_point().x
                click_y = rect.mid_point().y - 50
                
                Logger.info(f"Right-clicking at ({click_x}, {click_y}) (50px above tab)...")
                
                mouse.right_click(coords=(click_x, click_y))
                time.sleep(1)
                
                Logger.info("Waiting for context menu...")
                try:
                    menu = app.window(control_type="Menu")
                    if not menu.exists():
                        menu = app.top_window()
                    
                    Logger.info("Dumping menu items:")
                    items = menu.descendants(control_type="MenuItem")
                    for item in items:
                        text = item.window_text()
                        Logger.info(f" - {text}")
                        if "Export to CSV" in text:
                            Logger.info("   -> Found target! Invoking...")
                            try:
                                item.invoke()
                                Logger.info("   -> Invoked 'Export to CSV'")
                            except Exception as invoke_err:
                                Logger.info(f"   -> Invoke failed ({invoke_err}), trying click_input...")
                                item.click_input()
                                Logger.info("   -> Clicked 'Export to CSV'")
                            break
                    
                    # Handle Save As Dialog
                    Logger.info("Waiting for Save As dialog...")
                    # Search for the dialog more robustly
                    save_dlg = None
                    for _ in range(10):
                        try:
                            # Try finding it as a top-level window of the app
                            save_dlg = app.window(title="Save As")
                            if save_dlg.exists():
                                break
                            
                            # Try finding it as a child of the main window
                            save_dlg = win.child_window(title="Save As")
                            if save_dlg.exists():
                                break
                            from pywinauto import Desktop
                            save_dlg = Desktop(backend="uia").window(title="Save As")
                            if save_dlg.exists():
                                break
                        except:
                            pass
                    
                    if save_dlg and save_dlg.exists():
                        Logger.info("✅ Save As dialog found!")
                        save_dlg.set_focus()
                    else:
                        Logger.info("❌ Save As dialog NOT found.")
                        raise TimeoutError("Save As dialog did not appear.")
                    
                    full_path = output_dir 
                    Logger.info(f"Saving to: {full_path}")

                    # if not os.path.exists(output_dir):
                    #     Logger.info(f"Creating directory: {output_dir}")
                    #     os.makedirs(output_dir)
                        
                    Logger.info(f"Navigating to folder: {output_dir}")
                    
                    try:
                        file_box = save_dlg.child_window(title="File name:", control_type="Edit")
                    except:
                        Logger.info("Could not find 'File name:' edit box by title, trying by index...")
                        file_box = save_dlg.child_window(control_type="Edit", found_index=0)
                    
                    Logger.info("Typing full path...")
                    file_box.type_keys(full_path.replace(" ", "{SPACE}"), with_spaces=True)
                    # time.sleep(0.5)

                    save_btn = save_dlg.child_window(title="Save", control_type="Button")
                    save_btn.click()
                    # time.sleep(0.5) 
                    
                    # print(f"Setting file name: {output_filename}")
                    
                    Logger.info("Clicking Save button...")
                    save_btn.click()
                    
                    try:
                        # Wait briefly to see if confirmation dialog appears
                        confirm_dlg = save_dlg.child_window(title="Confirm Save As")
                        if confirm_dlg.exists(timeout=2):
                            Logger.info("⚠️ File exists. Overwriting...")
                            yes_btn = confirm_dlg.child_window(title="Yes", control_type="Button")
                            yes_btn.click()
                            Logger.info("✅ Overwritten.")
                    except:
                        pass
                        
                    Logger.info("✅ File saved successfully.")
                        
                except Exception as e:
                    Logger.info(f"Error handling menu or save dialog: {e}")
                    
            else:
                Logger.info("⚠️ 'Graph' TabItem not found. Searching for any element named 'Graph'...")
                # Search deeper for any element with title "Graph"
                elements = win.descendants(title="Graph")
                if elements:
                    for e in elements:
                        Logger.info(f" - Found element: '{e.window_text()}' ({e.element_info.control_type})")
                        Logger.info("   -> Clicking candidate...")
                        e.click_input()
                        Logger.info("   -> Clicked.")
                        break
                else:
                    Logger.info("❌ No element named 'Graph' found.")

        except Exception as e:
            Logger.error(f"Error: {e}")

    