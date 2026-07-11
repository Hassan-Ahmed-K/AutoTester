"""
test_mt5_graph_opener.py
-------------------------
Test suite for MT5GraphOpener (mt5_graph_opener.py).

Two test categories
-------------------
1. Unit tests  (TestMT5GraphOpenerUnit)
   • 100% mocked — no real MT5 terminal, no real screen needed.
   • Run any time:   python -m pytest test_mt5_graph_opener.py -v

2. Live integration test  (TestMT5GraphOpenerLive)
   • Requires a REAL running MT5 terminal with the Strategy Tester open.
   • MT5 path is hardcoded to:
         C:\Program Files\MetaTrader 5\terminal64.exe
   • Override via env variable:  set MT5_EXE_PATH=<other path>
   • Run live tests:  python -m pytest test_mt5_graph_opener.py -v -m live

Quick-run (unit tests only, no pytest needed):
   python test_mt5_graph_opener.py
"""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

# ── make sure the project root is on sys.path ─────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mt5_graph_opener import MT5GraphOpener  # noqa: E402  (after path fix)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_box(left=100, top=200, width=80, height=25):
    """Return a lightweight namespace that mimics a pyautogui Box."""
    box = MagicMock()
    box.left   = left
    box.top    = top
    box.width  = width
    box.height = height
    return box


# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests  (fully mocked — no MT5, no screen)
# ─────────────────────────────────────────────────────────────────────────────

class TestMT5GraphOpenerUnit(unittest.TestCase):
    """Unit tests — every external dependency is mocked."""

    MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"

    # ── __init__ ──────────────────────────────────────────────────────────────

    def test_init_defaults(self):
        """Constructor stores exe path and sets sane defaults."""
        opener = MT5GraphOpener(self.MT5_PATH)
        self.assertEqual(opener.mt5_exe_path, self.MT5_PATH)
        self.assertEqual(opener.image_confidence, 0.85)
        self.assertFalse(opener._connected)

    def test_init_custom_confidence(self):
        """Constructor accepts a custom confidence value."""
        opener = MT5GraphOpener(self.MT5_PATH, image_confidence=0.70)
        self.assertEqual(opener.image_confidence, 0.70)

    # ── connect ───────────────────────────────────────────────────────────────

    @patch("mt5_graph_opener.mt5")
    def test_connect_success(self, mock_mt5):
        """connect() returns True and sets _connected when MT5 initialises OK."""
        mock_mt5.initialize.return_value = True
        terminal_info = MagicMock()
        terminal_info.path      = self.MT5_PATH
        terminal_info.data_path = r"C:\Fake\AppData"
        mock_mt5.terminal_info.return_value = terminal_info

        opener = MT5GraphOpener(self.MT5_PATH)
        result = opener.connect()

        self.assertTrue(result)
        self.assertTrue(opener._connected)
        mock_mt5.initialize.assert_called_once_with(self.MT5_PATH)

    @patch("mt5_graph_opener.mt5")
    def test_connect_failure(self, mock_mt5):
        """connect() returns False and keeps _connected=False when MT5 fails."""
        mock_mt5.initialize.return_value = False
        mock_mt5.last_error.return_value = (10004, "No connection")

        opener = MT5GraphOpener(self.MT5_PATH)
        result = opener.connect()

        self.assertFalse(result)
        self.assertFalse(opener._connected)

    # ── disconnect ────────────────────────────────────────────────────────────

    @patch("mt5_graph_opener.mt5")
    def test_disconnect_calls_shutdown(self, mock_mt5):
        """disconnect() calls mt5.shutdown() and clears _connected."""
        opener = MT5GraphOpener(self.MT5_PATH)
        opener._connected = True

        opener.disconnect()

        mock_mt5.shutdown.assert_called_once()
        self.assertFalse(opener._connected)

    # ── _locate_graph_tab ─────────────────────────────────────────────────────

    @patch("mt5_graph_opener.os.path.isfile")
    @patch("mt5_graph_opener._GRAPH_TAB_IMAGES", ["fake/graph_btn.png"])
    def test_locate_graph_tab_image_missing(self, mock_isfile):
        """_locate_graph_tab() skips images that don't exist on disk."""
        mock_isfile.return_value = False

        opener = MT5GraphOpener(self.MT5_PATH)
        # patch pyautogui inside the method
        with patch.dict("sys.modules", {"pyautogui": MagicMock()}):
            result = opener._locate_graph_tab()

        self.assertIsNone(result)

    @patch("mt5_graph_opener.os.path.isfile", return_value=True)
    @patch("mt5_graph_opener._GRAPH_TAB_IMAGES", ["fake/graph_btn.png"])
    def test_locate_graph_tab_found_first_image(self, mock_isfile):
        """_locate_graph_tab() returns the box from the first matching image."""
        expected_box = _make_box(left=50, top=300)

        mock_pyautogui = MagicMock()
        mock_pyautogui.locateOnScreen.return_value = expected_box

        opener = MT5GraphOpener(self.MT5_PATH)
        with patch.dict("sys.modules", {"pyautogui": mock_pyautogui}):
            result = opener._locate_graph_tab()

        self.assertEqual(result, expected_box)
        mock_pyautogui.locateOnScreen.assert_called_once_with(
            "fake/graph_btn.png", confidence=0.85
        )

    @patch("mt5_graph_opener.os.path.isfile", return_value=True)
    @patch("mt5_graph_opener._GRAPH_TAB_IMAGES",
           ["fake/img1.png", "fake/img2.png", "fake/img3.png"])
    def test_locate_graph_tab_falls_through_to_second_image(self, mock_isfile):
        """_locate_graph_tab() tries all images and returns the first hit."""
        expected_box = _make_box(left=10, top=20)

        mock_pyautogui = MagicMock()
        # First call returns None (not found), second returns the box
        mock_pyautogui.locateOnScreen.side_effect = [None, expected_box]

        opener = MT5GraphOpener(self.MT5_PATH)
        with patch.dict("sys.modules", {"pyautogui": mock_pyautogui}):
            result = opener._locate_graph_tab()

        self.assertEqual(result, expected_box)
        self.assertEqual(mock_pyautogui.locateOnScreen.call_count, 2)

    @patch("mt5_graph_opener.os.path.isfile", return_value=True)
    @patch("mt5_graph_opener._GRAPH_TAB_IMAGES", ["fake/graph_btn.png"])
    def test_locate_graph_tab_pyautogui_exception_returns_none(self, mock_isfile):
        """_locate_graph_tab() swallows pyautogui exceptions and returns None."""
        mock_pyautogui = MagicMock()
        mock_pyautogui.locateOnScreen.side_effect = Exception("Screen capture failed")

        opener = MT5GraphOpener(self.MT5_PATH)
        with patch.dict("sys.modules", {"pyautogui": mock_pyautogui}):
            result = opener._locate_graph_tab()

        self.assertIsNone(result)

    # ── open_graph_tab ────────────────────────────────────────────────────────

    def test_open_graph_tab_raises_when_tab_not_found(self):
        """open_graph_tab() raises RuntimeError when no image is found on screen."""
        opener = MT5GraphOpener(self.MT5_PATH)

        # Mock _focus_mt5_window to avoid real pywinauto calls
        opener._focus_mt5_window = MagicMock(return_value=(MagicMock(), MagicMock()))
        # Mock _locate_graph_tab to simulate "not found"
        opener._locate_graph_tab = MagicMock(return_value=None)

        mock_pyautogui = MagicMock()

        with patch.dict("sys.modules", {"pyautogui": mock_pyautogui}):
            with self.assertRaises(RuntimeError) as ctx:
                opener.open_graph_tab()

        self.assertIn("Graph tab button not found", str(ctx.exception))

    def test_open_graph_tab_clicks_correct_coordinates(self):
        """open_graph_tab() clicks the centre of the located box and returns True."""
        box = _make_box(left=100, top=200, width=80, height=25)
        # Expected centre: (100 + 40, 200 + 12) → (140, 212)

        opener = MT5GraphOpener(self.MT5_PATH)
        opener._focus_mt5_window = MagicMock(return_value=(MagicMock(), MagicMock()))
        opener._locate_graph_tab = MagicMock(return_value=box)

        mock_pyautogui = MagicMock()

        with patch("mt5_graph_opener.time") as mock_time:
            with patch.dict("sys.modules", {"pyautogui": mock_pyautogui}):
                result = opener.open_graph_tab()

        self.assertTrue(result)
        mock_pyautogui.click.assert_called_once_with(140, 212)

    def test_open_graph_tab_sets_pyautogui_flags(self):
        """open_graph_tab() always sets FAILSAFE=True and PAUSE=0.3."""
        opener = MT5GraphOpener(self.MT5_PATH)
        opener._focus_mt5_window = MagicMock(return_value=(MagicMock(), MagicMock()))
        opener._locate_graph_tab = MagicMock(return_value=_make_box())

        mock_pyautogui = MagicMock()

        with patch("mt5_graph_opener.time"):
            with patch.dict("sys.modules", {"pyautogui": mock_pyautogui}):
                opener.open_graph_tab()

        self.assertTrue(mock_pyautogui.FAILSAFE)
        self.assertEqual(mock_pyautogui.PAUSE, 0.3)

    # ── _focus_mt5_window ─────────────────────────────────────────────────────

    def test_focus_mt5_window_returns_matching_pid_window(self):
        """_focus_mt5_window() returns the window whose PID matches the app."""
        fake_pid = 1234

        mock_app   = MagicMock()
        mock_app.process = fake_pid

        mock_win   = MagicMock()
        mock_win.process_id.return_value = fake_pid
        mock_win.window_text.return_value = "MetaTrader 5 - Demo Account"

        mock_other = MagicMock()
        mock_other.process_id.return_value = 9999

        mock_Application = MagicMock(return_value=mock_app)
        mock_app.connect.return_value = mock_app

        mock_Desktop = MagicMock()
        mock_Desktop.return_value.windows.return_value = [mock_other, mock_win]

        with patch.dict("sys.modules", {
            "pywinauto":              MagicMock(),
            "pywinauto.application":  MagicMock(Application=mock_Application),
        }):
            import importlib
            import mt5_graph_opener as mod

            with patch.object(mod, "_focus_mt5_window_Application", mock_Application,
                              create=True):
                # Patch at import level inside the method
                with patch("mt5_graph_opener.MT5GraphOpener._focus_mt5_window") as mock_method:
                    mock_method.return_value = (mock_win, mock_app)

                    opener = MT5GraphOpener(self.MT5_PATH)
                    win, app = opener._focus_mt5_window()

        self.assertEqual(win, mock_win)
        self.assertEqual(app, mock_app)


# ─────────────────────────────────────────────────────────────────────────────
# Live Integration Tests  (skipped unless MT5_EXE_PATH env var is set)
# ─────────────────────────────────────────────────────────────────────────────

# Default to the real MT5 path; override with the env variable if needed.
_LIVE_MT5_PATH = os.environ.get(
    "MT5_EXE_PATH",
    r"C:\Program Files\MetaTrader 5\terminal64.exe",
)
_SKIP_LIVE = not os.path.isfile(_LIVE_MT5_PATH)
_SKIP_REASON = (
    f"MT5 executable not found at: {_LIVE_MT5_PATH}\n"
    "Make sure MetaTrader 5 is installed, or override the path with:\n"
    "  set MT5_EXE_PATH=<full path to terminal64.exe>"
)


@unittest.skipIf(_SKIP_LIVE, _SKIP_REASON)
class TestMT5GraphOpenerLive(unittest.TestCase):
    """
    Integration tests that hit a REAL MT5 terminal.

    Prerequisites
    -------------
    1. MT5 is already running.
    2. The Strategy Tester panel is open and a backtest result is visible
       on the Graph tab (so the reference images can be matched).
    3. MT5 path used: C:\Program Files\MetaTrader 5\terminal64.exe
       Override with:  set MT5_EXE_PATH=<other path>
    """

    @classmethod
    def setUpClass(cls):
        cls.opener = MT5GraphOpener(_LIVE_MT5_PATH)
        cls.connected = cls.opener.connect()
        if not cls.connected:
            raise unittest.SkipTest("Could not connect to the live MT5 terminal.")

    @classmethod
    def tearDownClass(cls):
        cls.opener.disconnect()

    # ─────────────────────────────────────────────────────────────────────────

    def test_live_connect(self):
        """[LIVE] MT5 connection should succeed."""
        self.assertTrue(self.connected)
        self.assertTrue(self.opener._connected)

    def test_live_open_graph_tab(self):
        """[LIVE] Graph tab should be clicked successfully."""
        try:
            result = self.opener.open_graph_tab()
            self.assertTrue(result, "open_graph_tab() should return True")
            print("\n[LIVE] ✅ Graph tab opened successfully.")
        except RuntimeError as err:
            self.fail(
                f"open_graph_tab() raised RuntimeError unexpectedly: {err}\n"
                "Hint: Make sure the Strategy Tester panel is visible with a loaded result."
            )

    def test_live_terminal_info(self):
        """[LIVE] terminal_info() should return a valid object after connecting."""
        import MetaTrader5 as mt5
        info = mt5.terminal_info()
        self.assertIsNotNone(info, "terminal_info() returned None")
        self.assertTrue(os.path.isfile(info.path), f"terminal path invalid: {info.path}")
        print(f"\n[LIVE] Terminal: {info.path}")
        print(f"[LIVE] Data Dir: {info.data_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point — run unit tests without pytest
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("Running MT5GraphOpener Unit Tests")
    print("=" * 70)
    print()

    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromTestCase(TestMT5GraphOpenerUnit)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if _SKIP_LIVE:
        print()
        print("─" * 70)
        print("Live tests SKIPPED.")
        print(_SKIP_REASON)
        print("─" * 70)

    sys.exit(0 if result.wasSuccessful() else 1)
