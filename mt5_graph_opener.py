"""
mt5_graph_opener.py
--------------------
Connects to a running MetaTrader 5 terminal and opens the "Graph" tab
inside the Strategy Tester result panel.

Usage (standalone):
    python mt5_graph_opener.py --mt5-path "C:/Program Files/MetaTrader 5/terminal64.exe"

Usage (as a module):
    from mt5_graph_opener import MT5GraphOpener

    opener = MT5GraphOpener(mt5_exe_path="C:/Program Files/MetaTrader 5/terminal64.exe")
    opener.connect()
    opener.open_graph_tab()
    opener.disconnect()
"""

import os
import time
import argparse
import MetaTrader5 as mt5


# ──────────────────────────────────────────────────────────────────────────────
# Helper: simple console logger (no dependency on the internal Logger class)
# ──────────────────────────────────────────────────────────────────────────────
class _Log:
    @staticmethod
    def info(msg: str):    print(f"[INFO]    {msg}")
    @staticmethod
    def success(msg: str): print(f"[SUCCESS] {msg}")
    @staticmethod
    def warning(msg: str): print(f"[WARNING] {msg}")
    @staticmethod
    def error(msg: str):   print(f"[ERROR]   {msg}")


# ──────────────────────────────────────────────────────────────────────────────
# Candidate reference images for the Graph tab button.
# Add more variants to "data/" if needed (e.g. different DPI / colour themes).
# ──────────────────────────────────────────────────────────────────────────────
_GRAPH_TAB_IMAGES = [
    os.path.join(os.getcwd(), "data", "graph_btn.png"),
    os.path.join(os.getcwd(), "data", "graph_wt_btn.png"),
    os.path.join(os.getcwd(), "data", "graph.png"),
]


class MT5GraphOpener:
    """
    Connects to a MetaTrader 5 terminal process and opens the Graph tab
    inside the Strategy Tester result area.

    Parameters
    ----------
    mt5_exe_path : str
        Absolute path to ``terminal64.exe`` (or ``terminal.exe``).
    image_confidence : float, optional
        pyautogui image-match confidence threshold (0–1).  Default ``0.85``.
    """

    def __init__(self, mt5_exe_path: str, image_confidence: float = 0.85):
        self.mt5_exe_path = mt5_exe_path
        self.image_confidence = image_confidence
        self._connected = False

    # ──────────────────────────────────────────────────────────────────────────
    # Connection helpers
    # ──────────────────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """
        Initialise the MT5 Python API against the running terminal.

        Returns
        -------
        bool
            ``True`` if the connection was successful.
        """
        if mt5.initialize(self.mt5_exe_path):
            self._connected = True
            info = mt5.terminal_info()
            _Log.success(f"Connected to MT5 terminal at: {info.path}")
            _Log.info(f"Data path: {info.data_path}")
            return True
        else:
            self._connected = False
            _Log.error(f"Failed to connect to MT5. Error: {mt5.last_error()}")
            return False

    def disconnect(self):
        """Shut down the MT5 Python API connection."""
        mt5.shutdown()
        self._connected = False
        _Log.info("Disconnected from MT5.")

    # ──────────────────────────────────────────────────────────────────────────
    # Window focus helper
    # ──────────────────────────────────────────────────────────────────────────

    def _focus_mt5_window(self):
        """
        Bring the MT5 main window to the foreground using pywinauto.

        Returns
        -------
        tuple[window, app]
            The focused window handle and the pywinauto Application object.
        """
        from pywinauto.application import Application
        from pywinauto import Desktop

        _Log.info("Connecting via pywinauto (UIA backend)…")
        app = Application(backend="uia").connect(path=self.mt5_exe_path)
        pid = app.process

        desktop = Desktop(backend="uia")
        for win in desktop.windows():
            if win.process_id() == pid:
                win.restore()
                win.set_focus()
                _Log.success(f"Focused window: '{win.window_text()}'")
                return win, app

        _Log.warning("Could not identify the MT5 main window; returning app top window.")
        return app.top_window(), app

    # ──────────────────────────────────────────────────────────────────────────
    # Graph tab locator
    # ──────────────────────────────────────────────────────────────────────────

    def _locate_graph_tab(self):
        """
        Try each candidate image until the Graph tab button is found on screen.

        Returns
        -------
        pyautogui.Box | None
            The bounding box of the found image, or ``None`` if not found.
        """
        import pyautogui

        for img_path in _GRAPH_TAB_IMAGES:
            if not os.path.isfile(img_path):
                _Log.warning(f"Reference image not found on disk — skipping: {img_path}")
                continue

            _Log.info(f"Trying image: {os.path.basename(img_path)}")
            try:
                location = pyautogui.locateOnScreen(img_path, confidence=self.image_confidence)
            except Exception as exc:
                _Log.warning(f"Error during screen scan ({os.path.basename(img_path)}): {exc}")
                continue

            if location:
                _Log.success(f"Graph tab located using: {os.path.basename(img_path)}")
                return location
            else:
                _Log.info(f"Not found with: {os.path.basename(img_path)}")

        return None

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def open_graph_tab(self) -> bool:
        """
        Click the "Graph" tab in the MT5 Strategy Tester result pane.

        Steps
        -----
        1. Focus the MT5 main window.
        2. Locate the Graph tab button on screen using reference images.
        3. Click the tab button.

        Returns
        -------
        bool
            ``True`` if the Graph tab was successfully clicked.

        Raises
        ------
        RuntimeError
            If the Graph tab button cannot be found on screen.
        """
        import pyautogui

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.3

        # Step 1 – bring MT5 to foreground
        mt5_window, app = self._focus_mt5_window()
        time.sleep(0.5)  # give the OS time to repaint the window

        # Step 2 – locate the Graph tab
        graph_tab = self._locate_graph_tab()

        if graph_tab is None:
            raise RuntimeError(
                "Graph tab button not found on screen. "
                "Make sure the Strategy Tester panel is visible and "
                "that a backtest result is loaded. "
                "Also verify that reference images exist in the 'data/' folder "
                "(graph_btn.png, graph_wt_btn.png, graph.png)."
            )

        # Step 3 – click the tab
        center_x = graph_tab.left + graph_tab.width // 2
        center_y = graph_tab.top + graph_tab.height // 2

        pyautogui.click(center_x, center_y)
        time.sleep(0.5)

        _Log.success(f"Graph tab clicked at ({center_x}, {center_y}).")
        return True


# ──────────────────────────────────────────────────────────────────────────────
# Standalone entry point
# ──────────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Connect to MetaTrader 5 and open the Graph tab."
    )
    parser.add_argument(
        "--mt5-path",
        required=True,
        help='Full path to the MT5 executable, e.g. "C:/Program Files/MetaTrader 5/terminal64.exe"',
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.85,
        help="Image-match confidence threshold for pyautogui (0.0–1.0).  Default: 0.85",
    )
    return parser.parse_args()


def main():
    args = _parse_args()

    opener = MT5GraphOpener(
        mt5_exe_path=args.mt5_path,
        image_confidence=args.confidence,
    )

    # Connect to MT5
    if not opener.connect():
        _Log.error("Aborting — could not connect to MT5.")
        return

    try:
        # Open the Graph tab
        opener.open_graph_tab()
        _Log.success("Graph tab is now active.")
    except RuntimeError as err:
        _Log.error(str(err))
    finally:
        opener.disconnect()


if __name__ == "__main__":
    main()
