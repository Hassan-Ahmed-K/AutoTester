"""
switch_graph_and_save_csv.py
-----------------------------
Switches to the Graph tab inside the MT5 Strategy Tester result panel
(MT5 must already be running) and exports the graph data as both a
CSV file and a PNG screenshot.

Usage
-----
    # Default output paths (CSV_Reports/ folder, timestamped):
    python switch_graph_and_save_csv.py

    # Custom base name (produces result.csv and result.png):
    python switch_graph_and_save_csv.py --output "D:/MyReports/result"

    # Custom paths for each format individually:
    python switch_graph_and_save_csv.py --csv "D:/Reports/data.csv" --png "D:/Reports/chart.png"

Requirements
------------
    pip install MetaTrader5 pywinauto pyautogui
"""

import os
import sys
import time
import argparse
from datetime import datetime

import MetaTrader5 as mt5
import pyautogui
from pywinauto.application import Application
from pywinauto import Desktop


# ── Configuration ─────────────────────────────────────────────────────────────

MT5_EXE = r"C:\Program Files\MetaTrader 5\terminal64.exe"

# Reference images for the Graph tab button (tried in order)
GRAPH_IMAGES = [
    os.path.join(os.path.dirname(__file__), "data", "graph_btn.png"),
    os.path.join(os.path.dirname(__file__), "data", "graph_wt_btn.png"),
    os.path.join(os.path.dirname(__file__), "data", "graph.png"),
]

# Pixels above the Graph tab centre to right-click into the chart area
RIGHT_CLICK_OFFSET_Y = 100

# pyautogui image-match confidence
CONFIDENCE = 0.85

# Delay between actions (seconds)
PAUSE_SHORT   = 0.3
PAUSE_MEDIUM  = 0.6
PAUSE_LONG    = 1.0
PAUSE_SETTLE  = 2.5   # extra wait after a Save-As dialog closes before next screen scan

# How many times to retry locateOnScreen if the screen is still repainting
GRAPH_TAB_RETRIES = 3


# ── Logger ────────────────────────────────────────────────────────────────────

class Log:
    @staticmethod
    def info(msg):    print(f"[INFO]    {msg}")
    @staticmethod
    def ok(msg):      print(f"[OK]      ✅ {msg}")
    @staticmethod
    def warn(msg):    print(f"[WARN]    ⚠️  {msg}")
    @staticmethod
    def error(msg):   print(f"[ERROR]   ❌ {msg}")
    @staticmethod
    def step(n, msg): print(f"\n[STEP {n}]  {msg}")
    @staticmethod
    def banner(msg):
        print()
        print("=" * 60)
        print(f"  {msg}")
        print("=" * 60)


# ── Step 1 – Connect to MT5 ───────────────────────────────────────────────────

def connect_mt5() -> bool:
    """Initialise the MT5 Python bridge against the already-running terminal."""
    Log.step(1, "Connecting to MT5 terminal…")

    if mt5.initialize(MT5_EXE):
        info = mt5.terminal_info()
        Log.ok(f"Connected  →  {info.path}")
        Log.info(f"Data path  →  {info.data_path}")
        return True
    else:
        Log.error(f"mt5.initialize() failed: {mt5.last_error()}")
        return False


# ── Step 2 – Focus the MT5 window ────────────────────────────────────────────

def focus_mt5_window():
    """Bring the MT5 main window to the foreground.

    Returns
    -------
    (window, app) : tuple
    """
    Log.step(2, "Focusing MT5 window…")

    app = Application(backend="uia").connect(path=MT5_EXE)
    pid = app.process

    desktop = Desktop(backend="uia")
    for win in desktop.windows():
        if win.process_id() == pid:
            win.restore()
            win.set_focus()
            Log.ok(f"Window focused → '{win.window_text()}'")
            return win, app

    Log.warn("Could not find window by PID — using app.top_window() as fallback.")
    return app.top_window(), app


# ── Step 3 – Locate and click the Graph tab ───────────────────────────────────

def click_graph_tab() -> tuple:
    """
    Find the Graph tab button on screen (via reference images) and click it.

    Returns
    -------
    (center_x, center_y) : tuple[int, int]
        Screen co-ordinates of the tab centre — reused for the right-click.

    Raises
    ------
    RuntimeError
        If none of the reference images are found on screen.
    """
    Log.step(3, "Locating Graph tab on screen…")

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE    = PAUSE_SHORT

    graph_tab = None

    for attempt in range(1, GRAPH_TAB_RETRIES + 1):
        if attempt > 1:
            Log.warn(f"Retry {attempt}/{GRAPH_TAB_RETRIES} — waiting for screen to repaint…")
            time.sleep(PAUSE_SETTLE)

        for img in GRAPH_IMAGES:
            if not os.path.isfile(img):
                Log.warn(f"Reference image missing — skipping: {os.path.basename(img)}")
                continue

            Log.info(f"Trying → {os.path.basename(img)}")
            try:
                location = pyautogui.locateOnScreen(img, confidence=CONFIDENCE)
            except Exception as exc:
                Log.warn(f"Screen scan error ({os.path.basename(img)}): {exc}")
                continue

            if location:
                Log.ok(f"Graph tab found using: {os.path.basename(img)}")
                graph_tab = location
                break
            else:
                Log.info(f"Not matched: {os.path.basename(img)}")

        if graph_tab:
            break   # found — stop retrying

    if graph_tab is None:
        raise RuntimeError(
            "Graph tab button not found on screen after "
            f"{GRAPH_TAB_RETRIES} attempt(s).\n"
            "  → Make sure the Strategy Tester panel is open with a result loaded.\n"
            "  → Verify data/graph_btn.png, graph_wt_btn.png, graph.png exist."
        )

    cx = graph_tab.left + graph_tab.width  // 2
    cy = graph_tab.top  + graph_tab.height // 2

    pyautogui.click(cx, cy)
    time.sleep(PAUSE_MEDIUM)
    Log.ok(f"Clicked Graph tab at ({cx}, {cy})")

    return cx, cy


# ── Step 4 – Open context menu ────────────────────────────────────────────────

def open_context_menu(cx: int, cy: int, app, step_num: int = 4) -> object:
    """
    Right-click the chart area (above the Graph tab) to open the context menu.

    Parameters
    ----------
    cx, cy      : int   – Tab centre co-ordinates.
    app         : pywinauto Application
    step_num    : int   – Step label for log output.

    Returns
    -------
    menu : pywinauto window wrapper
    """
    Log.step(step_num, "Opening context menu (right-click on chart)…")

    right_click_y = cy - RIGHT_CLICK_OFFSET_Y
    pyautogui.rightClick(cx, right_click_y)
    time.sleep(PAUSE_MEDIUM)
    Log.ok(f"Right-clicked at ({cx}, {right_click_y})")

    # Wait up to 2 s for the menu window to appear
    desktop = Desktop(backend="uia")
    for _ in range(10):
        try:
            if any(
                w.element_info.control_type == "Menu"
                for w in desktop.windows()
            ):
                Log.ok("Context menu detected.")
                break
        except Exception:
            pass
        time.sleep(0.2)

    # Resolve the menu wrapper used for item enumeration
    try:
        menu = app.window(control_type="Menu")
        if not menu.exists():
            menu = app.top_window()
    except Exception:
        menu = app.top_window()

    return menu


# ── Step 5 (generic) – Click a menu item by label ────────────────────────────

def click_menu_item(menu, label: str, step_num: int = 5) -> bool:
    """
    Find and invoke a menu item whose text contains *label*.

    Parameters
    ----------
    menu     : pywinauto window wrapper  – The context-menu wrapper.
    label    : str                       – Substring to match (e.g. 'Export to CSV').
    step_num : int                       – Step label for log output.

    Returns
    -------
    bool – True if the item was invoked successfully.
    """
    Log.step(step_num, f"Looking for '{label}' in context menu…")

    try:
        items = menu.descendants(control_type="MenuItem")
        Log.info(f"Menu items found: {len(items)}")

        for item in items:
            text = item.window_text()
            Log.info(f"  • {text}")

            if label in text:
                Log.ok(f"Found target → '{text}'")
                try:
                    item.invoke()
                    Log.ok("Invoked via UIA.")
                except Exception as invoke_err:
                    Log.warn(f"invoke() failed ({invoke_err}) — trying click_input()…")
                    item.click_input()
                    Log.ok("Clicked via click_input().")
                return True

        Log.error(f"'{label}' not found in menu items.")
        return False

    except Exception as exc:
        Log.error(f"Error enumerating menu: {exc}")
        return False


# ── Step 6 (generic) – Fill Save As dialog ───────────────────────────────────

def save_file_dialog(output_path: str, step_num: int = 6):
    """
    Type *output_path* into the active Windows 'Save As' dialog and confirm.

    Parameters
    ----------
    output_path : str – Full absolute path including extension.
    step_num    : int – Step label for log output.
    """
    Log.step(step_num, "Typing path into Save As dialog…")
    Log.info(f"Output → {output_path}")

    time.sleep(0.8)                               # let the dialog paint

    pyautogui.hotkey("ctrl", "a")                 # clear pre-filled name
    time.sleep(0.2)
    pyautogui.write(output_path, interval=0.02)   # type full path
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(PAUSE_LONG)

    # Handle any "Overwrite existing file?" confirmation
    try:
        desktop = Desktop(backend="uia")
        confirm = desktop.window(title_re=".*(Confirm|Replace|Overwrite).*")
        if confirm.exists(timeout=2):
            Log.warn("Overwrite dialog detected — clicking Yes.")
            confirm.child_window(title="Yes", control_type="Button").click_input()
    except Exception:
        pass

    Log.ok(f"Saved → {output_path}")

    # Press Escape + wait so the screen fully repaints before the next action
    pyautogui.press("escape")
    time.sleep(PAUSE_SETTLE)


# ── Orchestrator ──────────────────────────────────────────────────────────────

def switch_graph_and_export(csv_path: str, png_path: str):
    """
    Full workflow — exports both CSV and PNG from the MT5 Graph tab.

    Sequence
    --------
    1. Connect to MT5 (already running)
    2. Focus the MT5 window
    3. Click the Graph tab ONCE
    4. Right-click at (cx, cy - offset)  →  context menu
    5. Click 'Export to CSV (Text file)'  →  Save As  →  .csv saved
    6. Right-click at the SAME (cx, cy - offset)  →  same context menu again
    7. Click 'Export to PNG (Picture)'   →  Save As  →  .png saved

    Parameters
    ----------
    csv_path : str – Full absolute path for the output CSV.
    png_path : str – Full absolute path for the output PNG.
    """
    Log.banner("MT5 Graph → CSV + PNG Exporter")

    # Ensure output directories exist
    for path in (csv_path, png_path):
        out_dir = os.path.dirname(path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

    # ── Step 1: Connect ──────────────────────────────────────────────────────
    if not connect_mt5():
        Log.error("Aborting — cannot connect to MT5.")
        return False

    try:
        # ── Step 2: Focus ────────────────────────────────────────────────────
        _, app = focus_mt5_window()
        time.sleep(0.5)

        # ── Step 3: Click Graph tab ONCE ─────────────────────────────────────
        cx, cy = click_graph_tab()

        # ════════════════════════════════════════════════════════════════════
        #  CSV Export  (first right-click)
        # ════════════════════════════════════════════════════════════════════
        Log.banner("Exporting CSV…")

        menu = open_context_menu(cx, cy, app, step_num=4)    # Step 4
        found = click_menu_item(menu, "Export to CSV", 5)    # Step 5
        if not found:
            Log.error("Could not trigger 'Export to CSV' — skipping CSV.")
        else:
            save_file_dialog(csv_path, step_num=6)           # Step 6
            # save_file_dialog already presses Escape + waits PAUSE_SETTLE

        # ════════════════════════════════════════════════════════════════════
        #  PNG Export  (second right-click at the SAME coordinates)
        # ════════════════════════════════════════════════════════════════════
        Log.banner("Exporting PNG…")

        # Reuse the same (cx, cy) from Step 3 — no need to re-find the Graph tab
        menu = open_context_menu(cx, cy, app, step_num=7)    # Step 7

        # MT5 labels this 'Export to PNG (Picture)'
        found = click_menu_item(menu, "Export to PNG", 8)
        if not found:
            Log.warn("'Export to PNG' not found — trying 'Save as Picture'…")
            found = click_menu_item(menu, "Save as Picture", 8)
        if not found:
            Log.error("Could not trigger PNG export — skipping PNG.")
        else:
            save_file_dialog(png_path, step_num=9)           # Step 9

        # ── Summary ──────────────────────────────────────────────────────────
        print()
        print("=" * 60)
        Log.ok(f"CSV → {csv_path}")
        Log.ok(f"PNG → {png_path}")
        print("=" * 60)
        return True

    except RuntimeError as exc:
        Log.error(str(exc))
        return False
    finally:
        mt5.shutdown()
        Log.info("MT5 API disconnected.")


# ── CLI entry point ───────────────────────────────────────────────────────────

def _default_base() -> str:
    """Timestamped base path inside CSV_Reports/ (no extension)."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(
        os.path.dirname(__file__),
        "CSV_Reports",
        f"graph_export_{ts}",
    )


def _parse_args() -> argparse.Namespace:
    base = _default_base()
    parser = argparse.ArgumentParser(
        description="Switch to MT5 Graph tab and export data as CSV + PNG."
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help=(
            "Base path (no extension) for both output files. "
            "Produces <path>.csv and <path>.png. "
            f"Default: CSV_Reports/graph_export_<timestamp>"
        ),
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="Override CSV output path (overrides --output for CSV).",
    )
    parser.add_argument(
        "--png",
        default=None,
        help="Override PNG output path (overrides --output for PNG).",
    )
    args = parser.parse_args()

    # Resolve final paths
    base_path  = args.output if args.output else base
    args.csv   = args.csv   if args.csv   else base_path + ".csv"
    args.png   = args.png   if args.png   else base_path + "_graph.png"
    return args


if __name__ == "__main__":
    args    = _parse_args()
    success = switch_graph_and_export(csv_path=args.csv, png_path=args.png)
    sys.exit(0 if success else 1)
