import os
import sys

def get_resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a BUNDLED resource (icons, styles, data assets).
    In a PyInstaller EXE, these live inside the _MEIPASS temp folder.
    In development, resolves from the project root.

    Use this for: icons, .qss stylesheets, logo images, data assets bundled via --add-data.
    Do NOT use this for external config files (firebaseCredential.json, .env, etc.).

    :param relative_path: The path to the resource relative to the project root.
    :return: The absolute path to the resource.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # In development, the base path is the project root
        # We assume this file is in aiagentfinder/utils/
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    return os.path.join(base_path, relative_path)


def get_external_path(relative_path: str) -> str:
    """
    Get the absolute path to an EXTERNAL config file that lives NEXT TO the EXE,
    not inside the PyInstaller bundle.

    Use this for: firebaseCredential.json, config.properties, session.json,
                  mapping.json, .env — files the user may need to edit.

    In a PyInstaller EXE:  resolves relative to the folder containing the EXE.
    In development:        resolves relative to the project root.

    :param relative_path: The filename or relative path (e.g. 'firebaseCredential.json').
    :return: The absolute path to the external file.
    """
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle — use the EXE's own directory
        base_path = os.path.dirname(sys.executable)
    else:
        # Running in development — project root (two levels up from aiagentfinder/utils/)
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    return os.path.join(base_path, relative_path)
