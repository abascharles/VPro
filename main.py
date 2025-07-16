# main.py

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import MainWindow

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("VideoPlayerPro")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("VideoPlayerPro")
    
    # High DPI support is enabled by default in PyQt6
    # No need to explicitly set AA_EnableHighDpiScaling
    
    # Set application style for modern look
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()