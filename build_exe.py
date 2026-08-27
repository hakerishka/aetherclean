"""
Build script for compiling AetherClean into a standalone Windows .exe using PyInstaller.
"""

import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def build():
    print("=" * 60)
    print("      AetherClean Standalone Windows .exe Builder")
    print("=" * 60)
    print()

    # PyInstaller options
    dist_dir = os.path.join(BASE_DIR, "dist")
    build_dir = os.path.join(BASE_DIR, "build")
    config_dir = os.path.join(BASE_DIR, "config")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name=AetherClean",
        f"--add-data={config_dir};config",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=psutil",
        "--hidden-import=yaml",
        "--hidden-import=send2trash",
        "--hidden-import=ctypes",
        "--clean",
        os.path.join(BASE_DIR, "main.py")
    ]

    print("Running PyInstaller command:")
    print(" ".join(cmd))
    print()

    result = subprocess.run(cmd, cwd=BASE_DIR)

    if result.returncode == 0:
        exe_path = os.path.join(dist_dir, "AetherClean.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print()
            print("=" * 60)
            print(f"[SUCCESS] Standalone executable created successfully!")
            print(f"File location: {exe_path}")
            print(f"File size:     {size_mb:.1f} MB")
            print("You can now copy AetherClean.exe to any Windows PC without Python!")
            print("=" * 60)
            return True

    print("\n[ERROR] Compilation failed. Please inspect logs above.")
    return False


if __name__ == "__main__":
    build()
