"""
AetherClean — Intelligent Storage & Debris Analyzer for Windows 11.
Main Entry Point.
"""

import sys
import os

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Graceful dependency check for direct CLI invocations
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    import psutil
    import yaml
    import send2trash
except ImportError as e:
    print("=" * 65)
    print(" [AetherClean] Missing required libraries!")
    print(f" Details: {e}")
    print("\n To automatically install dependencies, simply run:")
    print("     run.bat")
    print(" Or manually via terminal:")
    print("     pip install -r requirements.txt")
    print("=" * 65)
    try:
        input("\nPress Enter to exit...")
    except Exception:
        pass
    sys.exit(1)

from ui.main_window import MainWindow


def main():
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("AetherClean")
    app.setOrganizationName("AetherClean")
    app.setStyle("Fusion")

    # Set default UI font
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
