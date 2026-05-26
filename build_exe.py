import os
import shutil
import subprocess
import sys
import warnings

# <<< Added for Qt plugins
import PyQt5                         # import the PyQt5 package so we can locate its plugins

# Suppress annoying dependency warnings in the log
warnings.filterwarnings("ignore", category=UserWarning)

# --- Configuration ---
PROJECT_NAME = "ECHELON"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Top-level release folder  (ECHELON\)
FINAL_RELEASE_DIR = os.path.join(ROOT_DIR, "ECHELON")
# Actual executable + assets go into ECHELON\Executable\
EXECUTABLE_DIR   = os.path.join(FINAL_RELEASE_DIR, "Executable")

# Files that MUST stay OUTSIDE the EXE (placed next to the .exe in Executable\)
EXTERNAL_CONFIG_FILES = [
    ".env",
    "config.properties",
    "firebaseCredential.json",
    "mapping.json"
]

def clean_build_folders():
    """Removes temporary build and dist folders in the root."""
    print("🧹 Cleaning temporary build folders...")
    for d in ["build", "dist"]:
        dir_path = os.path.join(ROOT_DIR, d)
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"   Removed: {d}")
            except Exception as e:
                print(f"   ⚠️  Could not remove {d}: {e}")

def run_pyinstaller():
    """Runs the PyInstaller command with all fixes."""
    print(f"🚀 Building {PROJECT_NAME} (Fast‑Start Directory Mode)...")

    # <<< Added for Qt plugins
    # Locate the Qt plugins folder inside the PyQt5 installation
    pyqt_plugins_dir = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
    # We only need the `platforms` sub‑folder (contains qwindows.dll, etc.)
    qt_platforms_src = os.path.join(pyqt_plugins_dir, "platforms")
    qt_platforms_dst = "PyQt5/Qt5/plugins/platforms"

    command = [
        "pyinstaller",
        "--noconsole",
        "--onedir",
        f"--name={PROJECT_NAME}",

        # --- Bundled assets (icons, styles, data files) ---
        "--add-data", "aiagentfinder/icons;aiagentfinder/icons",
        "--add-data", "aiagentfinder/style;aiagentfinder/style",
        "--add-data", "data;data",

        # <<< Added for Qt plugins
        "--add-data", f"{qt_platforms_src};{qt_platforms_dst}",   # include Qt platform plugins

        # --- Hidden imports: charset / encoding ---
        "--hidden-import", "keyring.backends.Windows",
        "--hidden-import", "chardet",
        "--hidden-import", "charset_normalizer",
        "--collect-all", "chardet",

        # --- Hidden imports: Firebase Admin SDK ---
        "--hidden-import", "firebase_admin",
        "--hidden-import", "firebase_admin.credentials",
        "--hidden-import", "firebase_admin.firestore",
        "--hidden-import", "firebase_admin._auth_utils",
        "--hidden-import", "firebase_admin.exceptions",
        "--collect-all", "firebase_admin",

        # --- Hidden imports: gRPC (required by Firebase) ---
        "--hidden-import", "grpc",
        "--hidden-import", "grpc._cython",
        "--hidden-import", "grpc._cython.cygrpc",
        "--collect-all", "grpc",

        # --- Hidden imports: Google Cloud / Firestore ---
        "--hidden-import", "google.cloud.firestore",
        "--hidden-import", "google.cloud.firestore_v1",
        "--hidden-import", "google.auth",
        "--hidden-import", "google.auth.transport.requests",
        "--hidden-import", "google.oauth2.service_account",
        "--collect-all", "google.cloud.firestore",

        # --- Qt / PyQt5 specific hidden imports ---
        "--hidden-import", "PyQt5.sip",               # ensure the SIP module is bundled
        "--collect-all", "PyQt5",                    # collect all PyQt5 binaries (QtCore, QtGui, QtWidgets, …)

        # --- Exclude setuptools to avoid 'Lorem ipsum.txt' FileNotFoundError ---
        "--exclude-module", "setuptools",
        "--exclude-module", "pkg_resources",

        "main.py"
    ]

    try:
        subprocess.run(command, check=True)
        print("✅ PyInstaller build successful!")
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed: {e}")
        sys.exit(1)

def package_final_release():
    """
    Builds the final release with this folder structure:

        ECHELON\
        ├── ECHELON.spec        ← spec file (for reference / rebuilds)
        ├── build\              ← PyInstaller build cache (moved here)
        └── Executable\         ← the folder users actually run
            ├── ECHELON.exe
            ├── _internal\
            ├── .env
            ├── config.properties
            ├── firebaseCredential.json
            └── mapping.json
    """
    print(f"📦 Packaging final release to: {FINAL_RELEASE_DIR}")

    # 1. Prepare ECHELON\ and ECHELON\Executable\ directories
    # Only wipe the Executable sub‑folder so the build\ cache is preserved
    # across rebuilds if it already exists inside ECHELON\.
    if os.path.exists(EXECUTABLE_DIR):
        print("   Cleaning existing Executable folder...")
        shutil.rmtree(EXECUTABLE_DIR)
    os.makedirs(EXECUTABLE_DIR, exist_ok=True)
    os.makedirs(FINAL_RELEASE_DIR, exist_ok=True)

    # 2. Move app files: dist\ECHELON\ → ECHELON\Executable\
    source_app_dir = os.path.join(ROOT_DIR, "dist", PROJECT_NAME)
    if not os.path.exists(source_app_dir):
        print(f"❌ Error: {source_app_dir} not found!")
        return

    print("   Moving app files to Executable\\...")
    for item in os.listdir(source_app_dir):
        s = os.path.join(source_app_dir, item)
        d = os.path.join(EXECUTABLE_DIR, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    print(f"   [OK] App files → {EXECUTABLE_DIR}")

    # 3. Copy external config files → ECHELON\Executable\
    for filename in EXTERNAL_CONFIG_FILES:
        src = os.path.join(ROOT_DIR, filename)
        if os.path.exists(src):
            shutil.copy2(src, EXECUTABLE_DIR)
            print(f"   [OK] Config: {filename} → Executable\\")
        else:
            print(f"   ⚠️  Warning: {filename} not found in root, skipped.")

    # 4. Move build\ folder → ECHELON\build\
    src_build = os.path.join(ROOT_DIR, "build")
    dst_build = os.path.join(FINAL_RELEASE_DIR, "build")
    if os.path.exists(src_build):
        if os.path.exists(dst_build):
            shutil.rmtree(dst_build)
        shutil.move(src_build, dst_build)
        print("   [OK] build\\ → ECHELON\\build\\")
    else:
        print("   ⚠️  build\\ folder not found, skipped.")

    # 5. Move ECHELON.spec → ECHELON\ECHELON.spec
    src_spec = os.path.join(ROOT_DIR, f"{PROJECT_NAME}.spec")
    dst_spec = os.path.join(FINAL_RELEASE_DIR, f"{PROJECT_NAME}.spec")
    if os.path.exists(src_spec):
        shutil.move(src_spec, dst_spec)
        print(f"   [OK] {PROJECT_NAME}.spec → ECHELON\\")
    else:
        print(f"   ⚠️  {PROJECT_NAME}.spec not found, skipped.")

    # 6. Delete dist\ folder (no longer needed)
    dist_dir = os.path.join(ROOT_DIR, "dist")
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
        print("   [OK] dist\\ folder removed.")

def main():
    # Safety check: ensure we aren't running from the target folder
    if ROOT_DIR.lower() == FINAL_RELEASE_DIR.lower():
        print("❌ Error: You cannot run this script from inside the ECHELON folder.")
        return

    clean_build_folders()
    run_pyinstaller()
    package_final_release()

    print("\n" + "★" * 50)
    print(f"   SUCCESS! {PROJECT_NAME} is ready.")
    print(f"   Location: {FINAL_RELEASE_DIR}")
    print(f"   Run: {PROJECT_NAME}.exe inside that folder.")
    print("★" * 50)

if __name__ == "__main__":
    main()